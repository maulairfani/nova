from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool

from app.core.config import settings
from app.models import Base

config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Alembic always runs migrations synchronously - use the admin (DDL) URL,
# never the async runtime URL (matches mcp_servers/*/alembic's convention,
# ADR-0016).
config.set_main_option("sqlalchemy.url", settings.core_database_admin_url)

# app/models/ is the ORM source of truth - migrations are generated from
# it (alembic revision --autogenerate), not hand-written independently.
target_metadata = Base.metadata

# LangGraph's checkpointer owns these tables (created by
# setup_checkpointer.py, not Alembic) - exclude them from autogenerate's
# comparison entirely, or every future `revision --autogenerate` would
# propose dropping them (they're absent from our own Base.metadata).
_CHECKPOINTER_OWNED_TABLES = {"checkpoints", "checkpoint_blobs", "checkpoint_writes", "checkpoint_migrations"}


def include_object(object, name, type_, reflected, compare_to):
    if type_ == "table" and name in _CHECKPOINTER_OWNED_TABLES:
        return False
    return True


def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        include_object=include_object,
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata, include_object=include_object)
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
