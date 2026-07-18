"""SQLAlchemy declarative models for nova_core - the ORM source of truth
Alembic migrations are generated from (see alembic/env.py's target_metadata).

Message content and agent state are NOT modeled here - those live in
LangGraph's own checkpoint tables (checkpointer.py, ADR-0012), created by
setup_checkpointer.py, not by this file or Alembic.

One module per entity (base/user/business_unit/conversation/document);
this file just re-exports so `from app.models import X` keeps working
regardless of which module actually defines X.
"""
from app.models.base import Base
from app.models.business_unit import BusinessUnit, BusinessUnitRole, UserBusinessUnit
from app.models.conversation import Conversation
from app.models.document import Document
from app.models.user import User

__all__ = [
    "Base",
    "User",
    "BusinessUnit",
    "BusinessUnitRole",
    "UserBusinessUnit",
    "Conversation",
    "Document",
]
