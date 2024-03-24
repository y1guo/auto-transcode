import os
import sys
from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import FastAPI

from auto_transcode.modules.remux import RemuxProcess
from auto_transcode.utils.logger import get_logger


load_dotenv()

logger = get_logger(__name__)


# Validate environment variables
env_var_names = [
    "FLV_DIRS",
    "REMUX_DIR",
    "SAVE_DIR",
    "CACHE_DIR",
    "DAYS_BEFORE_REMUX",
    "DAYS_BEFORE_TRANSCODE",
]
env_vars: dict[str, str] = {}
valid = True
for env_var_name in env_var_names:
    value = os.getenv(env_var_name)
    if value:
        env_vars[env_var_name] = value
    else:
        logger.critical(f"{env_var_name} is not set")
        valid = False
if not valid:
    sys.exit(1)


@asynccontextmanager
async def lifespan(app: FastAPI):
    remux_process = RemuxProcess(
        flv_dirs=env_vars["FLV_DIRS"], days_before_remux=float(env_vars["DAYS_BEFORE_REMUX"])
    )
    remux_process.start()

    yield

    # Clean up
    remux_process.join()


app = FastAPI(lifespan=lifespan)
