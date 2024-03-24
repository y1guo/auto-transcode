from auto_transcode.modules.base import WatcherProcess
from auto_transcode.utils.logger import get_logger
from auto_transcode.settings import Settings


logger = get_logger(__name__)


class RemuxProcess(WatcherProcess):
    def __init__(self):
        super().__init__(process_name="Remux")
        self.flv_dirs = Settings.FLV_DIRS
        self.remux_dir = Settings.REMUX_DIR
        self.days_before_remux = Settings.DAYS_BEFORE_REMUX

    def main(self):
        for flv_dir in self.flv_dirs:
            self.watch(
                dir=flv_dir,
                delay=self.days_before_remux * 86400,
                callback=self.remux,
            )

    def remux(self, file_path: str):
        logger.info(f"Remuxing: {file_path}")
