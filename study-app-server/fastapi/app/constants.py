import os
from typing import Final, Literal, cast


class Constants:
    ENV: Final[Literal["local", "dev", "prod", "stg", "qa"]] = os.getenv("ENV")  # type: ignore
