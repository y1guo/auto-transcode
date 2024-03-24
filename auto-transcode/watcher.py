import multiprocessing
import os
import signal
import time

from dotenv import load_dotenv

from .utils.logger import get_logger


load_dotenv()

WAKEUP_TIME = float(os.getenv("WAKEUP_TIME", "5"))

logger = get_logger(__name__)


class WatcherProcess(multiprocessing.Process):
    def __init__(self):
        super().__init__()

    def run(self):
        signal.signal(signal.SIGINT, self.__signal_handler)
        signal.signal(signal.SIGTERM, self.__signal_handler)

        while True:
            try:
                self.watch()
                time.sleep(WAKEUP_TIME)
            except KeyboardInterrupt:
                logger.info("Watcher process received a keyboard interrupt")
                break
            except SystemExit:
                logger.info("Watcher process received a system exit")
                break
            except Exception as e:
                logger.exception(f"Watcher encountered an error: {repr(e)}")

        logger.info("Watcher process stopped")

    def __signal_handler(self, signum, frame):
        logger.info(f"Received signal: {signum}")
        if signum == signal.SIGINT:
            raise KeyboardInterrupt()
        elif signum == signal.SIGTERM:
            raise SystemExit()

    def watch(self):
        logger.info("Watching for new files")
        pass
