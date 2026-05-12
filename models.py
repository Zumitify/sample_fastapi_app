"""Pydantic + SQLAlchemy models for the sample FastAPI app fixture."""
from __future__ import annotations

from pydantic import BaseModel
from sqlalchemy.orm import DeclarativeBase, mapped_column, Mapped


class Base(DeclarativeBase):
    """```python
    class Base(DeclarativeBase):
        """Base class for all SQLAlchemy ORM models.

        Serves as the declarative base providing a common foundation for
        all database-mapped classes in the application. Inherits from
        SQLAlchemy's ``DeclarativeBase`` to enable the declarative ORM
        mapping pattern.
        """
    ```"""
    pass


class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column()


class UserCreate(BaseModel):
    email: str
    password: str


class UserOut(BaseModel):
    id: int
    email: str