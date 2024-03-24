import multiprocessing
import os
import signal
import time
from typing import Callable

from dotenv import load_dotenv

from auto_transcode.utils.logger import get_logger


load_dotenv()

logger = get_logger(__name__)

WAKEUP_TIME_STR = os.getenv("WAKEUP_TIME")
if WAKEUP_TIME_STR:
    WAKEUP_TIME = float(WAKEUP_TIME_STR)
else:
    WAKEUP_TIME = 60.0
    logger.warning(f"WAKEUP_TIME is not set. Defaulting to {WAKEUP_TIME} seconds.")


class WatcherProcess(multiprocessing.Process):
    def __init__(self, process_name: str, wakeup_time: float = WAKEUP_TIME):
        super().__init__(name=process_name)
        self.process_name = process_name
        self.wakeup_time = wakeup_time

    def run(self):
        signal.signal(signal.SIGINT, self.__signal_handler)
        signal.signal(signal.SIGTERM, self.__signal_handler)
        logger.info(f"{self.process_name} process started")

        while True:
            try:
                self.main()
                time.sleep(self.wakeup_time)
            except KeyboardInterrupt:
                logger.info(f"{self.process_name} process received a keyboard interrupt")
                break
            except SystemExit:
                logger.info(f"{self.process_name} process received a system exit")
                break
            except Exception as e:
                logger.exception(f"{self.process_name} encountered an error: {repr(e)}")

        logger.info(f"{self.process_name} process stopped")

    def __signal_handler(self, signum, frame):
        logger.info(f"Received signal: {signum}")
        if signum == signal.SIGINT:
            raise KeyboardInterrupt()
        elif signum == signal.SIGTERM:
            raise SystemExit()

    def main(self):
        raise NotImplementedError()

    def watch(self, dir: str, delay: float, callback: Callable[[str], None]):
        """Watch the directory and call a function upon the file when a file has existed for a
        certain amount of time.

        Parameters:
        - dir: The directory to watch
        - delay: In seconds. The amount of time the file has to exist, counted from the last
        modification time, before the watcher calls the callback function upon the file.
        - callback: The function to call upon the file. Takes one argument, the full file path.
        """
        for root, _, files in os.walk(dir):
            for file in files:
                file_path = os.path.join(root, file)
                basename, ext = os.path.splitext(file)

                # filter out non-flv files
                if ext != ".flv":
                    continue

                # check if the danmaku file exists and is valid
                danmaku_file_path = os.path.join(root, f"{basename}.xml")
                if not os.path.exists(danmaku_file_path):
                    logger.warning(f"Danmaku file does not exist: {danmaku_file_path}")
                    continue

                # check if the elapsed time since last modification is greater than the delay
                last_modified = os.path.getmtime(file_path)
                if time.time() - last_modified > delay:
                    callback(file_path)
