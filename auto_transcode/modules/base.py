import multiprocessing
import os
import signal
import time
from typing import Callable, Literal

from auto_transcode.settings import Settings
from auto_transcode.utils.logger import get_logger


Settings.init()

logger = get_logger(__name__)


class WatcherProcess(multiprocessing.Process):
    def __init__(self, process_name: str, wakeup_time: float = Settings.WAKEUP_TIME):
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

    def watch(
        self, dir: str, ext: Literal[".flv", ".mp4"], delay: float, callback: Callable[[str], None]
    ):
        """Watch the directory for files with the specified extension. Call a function upon the file
        when it has not been modified for the specified amount of time.

        Parameters:
        - dir: The directory to watch
        - ext: The file extension to watch
        - delay: In seconds. The amount of time the file has to exist, counted from the last
        modification time, before the watcher calls the callback function upon the file.
        - callback: The function to call upon the file. Takes one argument, the full file path.
        """
        for root, _, files in os.walk(dir):
            for file in files:
                # filter out files with the wrong extension
                _, file_ext = os.path.splitext(file)
                if file_ext != ext:
                    continue

                # check if the elapsed time since last modification is greater than the delay
                file_path = os.path.join(root, file)
                last_modified = os.path.getmtime(file_path)
                if time.time() - last_modified > delay:
                    callback(file_path)
