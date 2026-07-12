"""Unit tests for run_select's SELECT-only/forbidden-keyword guard
(db.py). These assert NonSelectQueryError is raised before any database
connection is attempted, so no live Postgres is needed here."""
import pytest

from db import NonSelectQueryError, run_select


async def test_rejects_non_select_statement():
    with pytest.raises(NonSelectQueryError):
        await run_select("DELETE FROM articles")


async def test_rejects_select_containing_a_forbidden_keyword():
    with pytest.raises(NonSelectQueryError):
        await run_select("SELECT * FROM articles; DROP TABLE articles;")


async def test_rejects_insert_disguised_with_leading_whitespace():
    with pytest.raises(NonSelectQueryError):
        await run_select("   insert into articles values (1)")
