from sqlalchemy import (
    String,
)
from sqlalchemy.orm import Mapped, mapped_column, registry
from models.model_base import ModelBase

mapper_registry = registry()

class Organization(ModelBase):
    __tablename__ = "organizations"
    name: Mapped[str] = mapped_column(String(60))
