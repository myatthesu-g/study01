import os
import random
from types import SimpleNamespace
from typing import AsyncGenerator, Final

import aiohttp
from fastapi import Header, HTTPException

from sqlalchemy import text

from db import MainSessionLocal, ReplicationSessionLocals


is_local: Final[bool] = os.getenv("ENV") == "local"


async def get_main_db_session(x_authorization: str | None = Header(default=None)) -> AsyncGenerator:
    try:
        async with MainSessionLocal() as session:  # type: ignore
            yield session
    except HTTPException:
        session.rollback()  # type: ignore
        raise
    finally:
        await session.close()  # type: ignore


def get_ip_address(x_forwarded_for: str | None = Header(default=None)) -> str:
    if is_local:
        return "1.1.1.1"
    if not x_forwarded_for:
        raise HTTPException(
            status_code=400,
            detail="ERROR.AUTH.INVALID_IPADDRESS",
        )
    return x_forwarded_for.split(",")[-2].strip()


async def get_rep_db_session(x_authorization: str | None = Header(default=None)) -> AsyncGenerator:
    current_session = random.choice(ReplicationSessionLocals)
    try:
        async with current_session() as session:
            if is_local:
                await session.execute(text("SET TRANSACTION READ ONLY"))
            yield session
    except HTTPException:
        session.rollback()  # type: ignore
        raise
    finally:
        await session.close()  # type: ignore


class AioHttpClient:
    """
    aiohttp singleton session (client)
    https://github.com/tiangolo/fastapi/discussions/8301
    https://docs.aiohttp.org/en/latest/http_request_lifecycle.html
    """

    session: aiohttp.ClientSession | None = None

    def __set_new_session(self) -> None:
        if self.session is None:
            trace_config = aiohttp.TraceConfig()
            trace_config.on_request_start.append(self.on_request_start)
            self.session = aiohttp.ClientSession(trace_configs=[trace_config])

    def init(self) -> None:
        self.__set_new_session()

    async def close(self) -> None:
        if self.session is not None:
            await self.session.close()
            self.session = None

    def __call__(self) -> aiohttp.ClientSession:
        self.__set_new_session()
        assert self.session is not None
        return self.session

    async def on_request_start(
        self, session: aiohttp.ClientSession, context: SimpleNamespace, params: aiohttp.TraceRequestStartParams
    ):
        import logging

        logging.basicConfig(level=logging.DEBUG)
        logger = logging.getLogger("aiohttp.client")
        logger.debug(f"[aiohttp] starting request...")
        logger.debug(f"[aiohttp] method: {params.method}")
        logger.debug(f"[aiohttp] url: {params.url}")
        logger.debug(f"[aiohttp] headers: {params.headers}")


get_aiohttp_client = AioHttpClient()
