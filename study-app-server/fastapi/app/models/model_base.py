import datetime

from sqlalchemy import INTEGER, TIMESTAMP, ColumnElement, MetaData, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.ext.declarative import as_declarative
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql.functions import current_timestamp
from typing_extensions import Annotated, Self

intpk = Annotated[int, mapped_column(primary_key=True, autoincrement=True)]
timestamp = Annotated[
    datetime.datetime,
    mapped_column(nullable=False, server_default=func.CURRENT_TIMESTAMP()),
]


@as_declarative()
class ModelBase:
    __abstract__ = True

    id: Mapped[intpk] = mapped_column(INTEGER, primary_key=True, autoincrement=True, sort_order=-10)

    created_at: Mapped[timestamp] = mapped_column(
        "created_at",
        TIMESTAMP(timezone=True),
        default=current_timestamp(),
        nullable=False,
        comment="登録日時",
    )

    updated_at: Mapped[timestamp] = mapped_column(
        "updated_at",
        TIMESTAMP(timezone=True),
        onupdate=current_timestamp(),
        nullable=False,
        comment="最終更新日時",
        default=current_timestamp(),
    )

    metadata = MetaData()
