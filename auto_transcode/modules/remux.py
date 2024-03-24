from auto_transcode.modules.base import WatcherProcess
from auto_transcode.utils.logger import get_logger


logger = get_logger(__name__)


class RemuxProcess(WatcherProcess):
    def __init__(self, flv_dirs: str, days_before_remux: float):
        super().__init__(process_name="Remux")
        self.flv_dirs = flv_dirs.split(",")
        self.days_before_remux = days_before_remux

    def main(self):
        for flv_dir in self.flv_dirs:
            logger.info(f"Watching FLV directory: {flv_dir}")
            self.watch(
                dir=flv_dir,
                delay=self.days_before_remux * 86400,
                callback=self.remux,
            )

    def remux(self, file_path: str):
        logger.info(f"Remuxing: {file_path}")
