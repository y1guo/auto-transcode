import multiprocessing
import os
import signal
import time

from dotenv import load_dotenv

from .utils.logger import get_logger


load_dotenv()

WAKEUP_TIME = float(os.getenv("WAKEUP_TIME", "5"))
FLV_DIRS = os.getenv("FLV_DIRS")


logger = get_logger(__name__)


class WatcherProcess(multiprocessing.Process):
    def __init__(self):
        super().__init__()

    def run(self):
        signal.signal(signal.SIGINT, self.__signal_handler)
        signal.signal(signal.SIGTERM, self.__signal_handler)

        while True:
            try:
                self.watcher()
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

    def watcher(self):
        if not FLV_DIRS:
            logger.critical("FLV_DIRS is not set")
            return

        for flv_dir in FLV_DIRS.split(","):
            logger.info(f"Watching FLV directory: {flv_dir}")
            self.watch_dir(flv_dir)

    def watch_dir(self, root_dir: str):
        for root, dirs, files in os.walk(root_dir):
            for dir in dirs:
                self.watch_dir(dir)
            for file in files:
                basename, ext = os.path.splitext(file)

                # filter out non-flv files
                if ext != ".flv":
                    continue

                logger.debug(f"Found recording: {basename}")
