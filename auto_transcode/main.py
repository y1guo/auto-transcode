from contextlib import asynccontextmanager

from fastapi import FastAPI

from auto_transcode.modules.remux import RemuxProcess


@asynccontextmanager
async def lifespan(app: FastAPI):
    remux_process = RemuxProcess()
    remux_process.start()

    yield

    # Clean up
    remux_process.join()


app = FastAPI(lifespan=lifespan)
