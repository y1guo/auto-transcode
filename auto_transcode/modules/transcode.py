import os
import shutil

import ffmpeg

from auto_transcode.modules.base import WatcherProcess
from auto_transcode.settings import Settings
from auto_transcode.utils.file import (
    get_video_codec_name,
    get_video_duration,
    safe_move_and_rename_file,
)
from auto_transcode.utils.logger import get_logger


logger = get_logger(__name__)


class TranscodeProcess(WatcherProcess):
    def __init__(self):
        super().__init__(process_name="Transcode")

    def main(self):
        self.watch(
            dir=Settings.REMUX_DIR,
            ext=".mp4",
            delay=Settings.DAYS_BEFORE_TRANSCODE * 86400,
            callback=self.callback,
        )

    def callback(self, source_path: str):
        """Transcode x264 videos to av1. Move the transcoded mp4 and xml files to SAVE_DIR."""
        dir, filename = os.path.split(source_path)
        basename, ext = os.path.splitext(filename)
        assert ext == ".mp4"
        target_path = os.path.join(Settings.CACHE_DIR, f"{basename}.mp4")
        xml_from = os.path.join(dir, f"{basename}.xml")
        xml_to = os.path.join(Settings.CACHE_DIR, f"{basename}.xml")

        # Transcode
        if self.validate_video(target_path, source_path, quiet=True):
            logger.info(f"File already transcoded: {repr(source_path)}")
        else:
            if os.path.exists(xml_from):
                shutil.copyfile(xml_from, xml_to)
            logger.info(f"Transcodeing {repr(source_path)}")
            self.transcode(source_path, target_path)
            if not self.validate_video(target_path, source_path):
                logger.error(f"Failed to transcode {repr(source_path)}")
                if os.path.exists(target_path):
                    os.remove(target_path)
                return
            logger.info(f"Transcoded {repr(source_path)}")

        # Check compression rate. Use the source file if compression rate >= 1.0
        source_size = os.path.getsize(source_path)
        target_size = os.path.getsize(target_path)
        compression_rate = source_size / target_size
        if compression_rate >= 1.0:
            logger.warn(f"Compression rate: {compression_rate:.2f} >= 1.0, using source file")
            os.remove(target_path)
            shutil.copyfile(source_path, target_path)

        # Rename
        new_target_path = os.path.join(Settings.SAVE_DIR, f"{basename}.mp4")
        safe_move_and_rename_file(target_path, new_target_path)
        new_xml_path = os.path.join(Settings.SAVE_DIR, f"{basename}.xml")
        safe_move_and_rename_file(xml_to, new_xml_path)
        if self.validate_video(new_target_path, source_path):
            os.remove(source_path)
            os.remove(xml_from)

    def validate_video(self, target_path: str, source_path: str, quiet: bool = False):
        """Validate the transcoded mp4 file.

        Returns:
            bool: True if the transcoded mp4 is valid, otherwise False
        """

        def info(msg):
            if not quiet:
                logger.info(msg)

        source_duration = get_video_duration(source_path)
        assert source_duration is not None

        if os.path.exists(target_path):
            target_duration = get_video_duration(target_path)
        else:
            info(f"File not found: {repr(target_path)}")
            return False
        if target_duration is None:
            info(f"Failed to probe {repr(target_path)}")
            return False

        diff = abs(source_duration - target_duration)
        if diff > 1:
            info(
                f"Transcoded video duration differ from source by {diff:.1f} sec: {repr(target_path)}"
            )
            return False

        source_codec = get_video_codec_name(source_path)
        target_codec = get_video_codec_name(target_path)
        if source_codec == "av1" or target_codec != "av1":
            info(f"Invalid codec: source_codec={source_codec}, target_codec={target_codec}")
            return False

        return True

    def transcode(self, source_path: str, target_path: str):
        try:
            ffmpeg.input(source_path).output(
                target_path, vcodec="av1_nvenc", cq=Settings.CONSTANT_QUALITY, acodec="copy"
            ).run(overwrite_output=True, capture_stdout=True, capture_stderr=True)
        except ffmpeg.Error as e:
            logger.error(f"Failed to transcode {repr(source_path)}")
            logger.error("stdout:", e.stdout.decode("utf8"))
            logger.error("stderr:", e.stderr.decode("utf8"))
            if os.path.exists(target_path):
                os.remove(target_path)
