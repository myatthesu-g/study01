import os
from typing import Final, List, cast

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

db_main_host: Final[str] = cast(str, os.getenv("DB_HOST"))
db_rep_hosts: Final[List[str]] = eval(cast(str, os.getenv("DB_HOST_REPLICATIONS")))
db_name: Final[str] = cast(str, os.getenv("DB_NAME"))
db_password: Final[str] = cast(str, os.getenv("DB_PASSWORD"))
db_user: Final[str] = cast(str, os.getenv("DB_USER"))
db_pool_size: Final[int] = int(os.environ["DB_POOL_SIZE"])


def db_uri(host: str, schema: str) -> str:
    return (
        f"mysql+aiomysql://{db_user}:{db_password}@{host}/{schema}?charset=utf8mb4"
        if db_password
        else f"mysql+aiomysql://{db_user}@{host}/{schema}?charset=utf8mb4"
    )


main_engine = create_async_engine(
    db_uri(db_main_host, db_name),
    pool_pre_ping=True,
    pool_size=db_pool_size,
    max_overflow=5,
    pool_recycle=3600,
    logging_name="<main>",
    isolation_level="READ COMMITTED",
)
MainSessionLocal = sessionmaker(
    autocommit=False, autoflush=False, bind=main_engine, class_=AsyncSession, expire_on_commit=False  # type: ignore
)
ReplicationSessionLocals = []

for rep_hosts in db_rep_hosts:
    engine = create_async_engine(
        db_uri(rep_hosts, db_name),
        pool_pre_ping=True,
        pool_size=db_pool_size,
        max_overflow=5,
        pool_recycle=3600,
        logging_name="<replication>",
        isolation_level="READ COMMITTED",
    )
    ReplicationSessionLocals.append(sessionmaker(autocommit=False, autoflush=False, bind=engine, class_=AsyncSession))  # type: ignore
