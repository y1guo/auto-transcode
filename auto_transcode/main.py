from contextlib import asynccontextmanager

from fastapi import FastAPI

from auto_transcode.modules.remux import RemuxProcess
from auto_transcode.modules.transcode import TranscodeProcess
from auto_transcode.settings import Settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    remux_process = RemuxProcess()
    remux_process.start()
    transcode_process = TranscodeProcess()
    transcode_process.start()

    yield

    # Clean up
    remux_process.join()
    transcode_process.join()


Settings.init()
app = FastAPI(lifespan=lifespan)
