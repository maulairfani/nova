"""SQL Analytics Tool — minimal text-to-SQL against postgres-plus (read-only).

Part of mcp-plus's fixed shape (TDD §5.2); its correctness is not phase-1's
acceptance bar (only the KB flow, §6.1, is) but it must exist and reject
non-SELECT statements defensively.
"""
from openai import OpenAI

from config import settings
from db import SCHEMA_DESCRIPTION, NonSelectQueryError, run_select

_llm = OpenAI(base_url="https://openrouter.ai/api/v1", api_key=settings.openrouter_api_key)

_SYSTEM_PROMPT = f"""You translate a natural-language analytics question into a single
read-only PostgreSQL SELECT statement against this schema:

{SCHEMA_DESCRIPTION}

Rules:
- Output ONLY the SQL statement, no explanation, no markdown code fences.
- Only ever write a SELECT statement. Never write INSERT/UPDATE/DELETE/DDL.
- Use the tables/columns above exactly as named.
"""


async def sql_analytics(question: str) -> dict:
    """Answer an analytics question about MCN+'s titles, engagement,
    subscriptions/churn, coin transactions, or content licensing costs
    (streaming or shorts) by generating and executing a read-only SQL query."""
    response = _llm.chat.completions.create(
        model=settings.openrouter_llm_model,
        messages=[
            {"role": "system", "content": _SYSTEM_PROMPT},
            {"role": "user", "content": question},
        ],
        temperature=0,
    )
    sql = response.choices[0].message.content.strip()

    try:
        rows = await run_select(sql)
    except NonSelectQueryError as exc:
        return {"error": str(exc), "generated_sql": sql}

    return {"generated_sql": sql, "rows": rows}
