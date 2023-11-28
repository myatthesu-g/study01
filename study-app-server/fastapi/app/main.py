import logging as baseLogging
import os
from typing import List

import coloredlogs
from fastapi import FastAPI,Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from api_service import get_aiohttp_client, get_main_db_session, get_rep_db_session
from models.models import Organization
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import  select
is_local = os.getenv("ENV") == "local"

app = FastAPI()

if is_local:
    baseLogging.basicConfig(level=baseLogging.INFO)
    baseLogger = baseLogging.getLogger("sqlalchemy.engine")
    baseLogger.setLevel(baseLogging.DEBUG)
    coloredlogs.install(level="DEBUG", logger=baseLogger)


origins: List[str] = [
    "http://localhost:4200",
    "https://*.kakeai.dev",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(GZipMiddleware, minimum_size=1000)



@app.on_event("startup")
async def startup():
    get_aiohttp_client.init()


@app.on_event("shutdown")
async def shutdown():
    await get_aiohttp_client.close()


@app.get("/api/hello")
async def root():
    return {"message": "Hello World"}

@app.get("/api/organizations")
async def organizations(session: AsyncSession = Depends(get_rep_db_session),) -> List[str]:
    query = select(Organization)
    return [x.name for x in (await session.execute(query)).scalars().all()]