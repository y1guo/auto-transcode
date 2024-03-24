from contextlib import asynccontextmanager

from fastapi import FastAPI

from .watcher import WatcherProcess


@asynccontextmanager
async def lifespan(app: FastAPI):
    watcher_process = WatcherProcess()
    watcher_process.start()

    yield
    # Clean up
    watcher_process.join()


app = FastAPI(lifespan=lifespan)
