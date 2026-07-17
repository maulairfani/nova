"""Shared loader for each business unit's semantic layer (ADR-0024).

Renders a hand-written YAML data dictionary (table/column business
descriptions, relationships, a glossary, derived-metric formulas, and
example question -> SQL pairs) into a single prompt-ready text block for
the SQL Analytics Tool's system prompt. The *content* is unit-specific
(each unit owns its own `semantic/schema.yaml`, same reasoning as each
unit owning its own Alembic migrations, ADR-0016); only the rendering
logic is shared, to keep three units' prompts structurally consistent
without three copies of this function.
"""
from pathlib import Path

import yaml


def load_semantic_layer(yaml_path: str | Path) -> str:
    """Read a unit's `semantic/schema.yaml` and render it into the text
    block `db.py` exposes as `SCHEMA_DESCRIPTION` for the SQL Analytics
    Tool's system prompt."""
    with open(yaml_path, "r", encoding="utf-8") as f:
        spec = yaml.safe_load(f)

    lines = [f"# {spec['business_unit_name']} Analytics Database — Semantic Layer", ""]
    if spec.get("overview"):
        lines.append(spec["overview"])

    lines.append("\n## Tables\n")
    for table_name, table in spec["tables"].items():
        lines.append(f"### {table_name}")
        lines.append(table["description"])
        lines.append("Columns:")
        for col_name, col in table["columns"].items():
            descriptor = col["type"]
            if col.get("pk"):
                descriptor += ", PK"
            if col.get("fk"):
                descriptor += f", FK -> {col['fk']}"
            detail = f"- `{col_name}` ({descriptor}): {col['description']}"
            if col.get("enum"):
                detail += f" Allowed values: {col['enum']}."
            if col.get("unit"):
                detail += f" Unit: {col['unit']}."
            lines.append(detail)
        lines.append("")

    if spec.get("glossary"):
        lines.append("## Business Glossary\n")
        for term, definition in spec["glossary"].items():
            lines.append(f"- **{term}**: {definition}")
        lines.append("")

    if spec.get("metrics"):
        lines.append("## Derived Metrics (not raw columns — compute via the formula)\n")
        for name, metric in spec["metrics"].items():
            lines.append(f"- **{name}**: {metric['description']} Formula: `{metric['formula']}`")
        lines.append("")

    if spec.get("query_examples"):
        lines.append("## Example Questions -> SQL\n")
        for example in spec["query_examples"]:
            lines.append(f"Q: {example['question']}")
            lines.append(f"SQL: {example['sql']}\n")

    return "\n".join(lines)
