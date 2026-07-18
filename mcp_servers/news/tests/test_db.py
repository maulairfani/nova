"""Unit tests for run_select's SELECT-only/forbidden-keyword guard
(db.py). These assert NonSelectQueryError is raised before any database
connection is attempted, so no live Postgres is needed here."""
from unittest.mock import MagicMock, patch

import pytest

import db as db_module
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


async def test_accepts_a_cte_query_and_reaches_the_database():
    """Regression test: a `WITH ... SELECT ...` CTE is a legitimate,
    read-only query (the SQL Analytics Tool's own text-to-SQL step reaches
    for one whenever a question needs a comparison, e.g. week-over-week),
    and used to be rejected outright by a guard that only recognized a
    literal `select` prefix. Asserts the guard lets it through by checking
    that a marker error from a stubbed connection surfaces - i.e. the code
    actually reached the database layer instead of raising
    NonSelectQueryError first."""

    class _ReachedDatabase(Exception):
        pass

    class _FakeConn:
        async def __aenter__(self):
            raise _ReachedDatabase

        async def __aexit__(self, *_args):
            return False

    fake_engine = MagicMock()
    fake_engine.connect.return_value = _FakeConn()
    with patch.object(db_module, "_engine", fake_engine):
        with pytest.raises(_ReachedDatabase):
            await run_select("WITH recent AS (SELECT 1 AS n) SELECT * FROM recent")
