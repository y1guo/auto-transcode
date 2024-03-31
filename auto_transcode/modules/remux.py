import os
import shutil

import ffmpeg

from auto_transcode.modules.base import WatcherProcess
from auto_transcode.settings import Settings
from auto_transcode.utils.file import (
    get_video_duration,
    get_video_metadata,
    safe_move_and_rename_file,
)
from auto_transcode.utils.logger import get_logger


logger = get_logger(__name__)


class RemuxProcess(WatcherProcess):
    def __init__(self):
        super().__init__(process_name="Remux")

    def main(self):
        for flv_dir in Settings.FLV_DIRS:
            self.watch(
                dir=flv_dir,
                ext=".flv",
                delay=Settings.DAYS_BEFORE_REMUX * 86400,
                callback=self.callback,
            )

    def callback(self, flv_path: str):
        """Remux the flv file to mp4. Move the mp4 and xml files to REMUX_DIR. Rename the filenames
        with trailing "_2", "_3", etc. if the file already exists in REMUX_DIR.
        """
        dir, filename = os.path.split(flv_path)
        basename, ext = os.path.splitext(filename)
        assert ext == ".flv"
        mp4_path = os.path.join(Settings.CACHE_DIR, f"{basename}.mp4")
        xml_from = os.path.join(dir, f"{basename}.xml")
        xml_to = os.path.join(Settings.CACHE_DIR, f"{basename}.xml")

        # Remove small files
        flv_size = os.path.getsize(flv_path)
        if flv_size < Settings.MIN_FLV_SIZE:
            os.remove(mp4_path)
            if os.path.exists(xml_from):
                os.remove(xml_from)
            logger.info(f"Removed small file ({flv_size} B): {flv_path}")
            return

        # Remove short videos
        duration = get_video_duration(flv_path)
        if duration is None:
            logger.error(f"Flv is invalid: {repr(flv_path)}")
            return
        if duration < Settings.MIN_FLV_DURATION:
            os.remove(flv_path)
            if os.path.exists(xml_from):
                os.remove(xml_from)
            logger.info(f"Removed short video ({duration:.0f} sec): {flv_path}")
            return

        # Remux
        if self.validate_video(mp4_path, flv_path, quiet=True):
            logger.info(f"File already remuxed: {repr(flv_path)}")
        else:
            if os.path.exists(xml_from):
                shutil.copyfile(xml_from, xml_to)
            logger.info(f"Remuxing {repr(flv_path)}")
            self.remux(flv_path, mp4_path)
            if not self.validate_video(mp4_path, flv_path):
                logger.error(f"Failed to remux {repr(flv_path)}")
                if os.path.exists(mp4_path):
                    os.remove(mp4_path)
                return
            logger.info(f"Remuxed {repr(flv_path)}")

        # Rename
        new_basename = self.get_new_basename(basename)
        logger.info(f"Renaming {repr(basename)} to {repr(new_basename)}")
        new_mp4_path = os.path.join(Settings.REMUX_DIR, f"{new_basename}.mp4")
        safe_move_and_rename_file(mp4_path, new_mp4_path)
        new_xml_path = os.path.join(Settings.REMUX_DIR, f"{new_basename}.xml")
        safe_move_and_rename_file(xml_to, new_xml_path)
        if self.validate_video(new_mp4_path, flv_path):
            os.remove(flv_path)
            os.remove(xml_from)

    def validate_video(self, mp4_path: str, flv_path: str, quiet: bool = False):
        """Validate the remuxed mp4 file.

        Returns:
            bool: True if the remuxed mp4 is valid, otherwise False
        """

        def info(msg):
            if not quiet:
                logger.info(msg)

        flv_duration = get_video_duration(flv_path)
        assert flv_duration is not None

        if os.path.exists(mp4_path):
            mp4_duration = get_video_duration(mp4_path)
        else:
            info(f"File not found: {repr(mp4_path)}")
            return False
        if mp4_duration is None:
            info(f"Failed to probe {repr(mp4_path)}")
            return False

        diff = abs(flv_duration - mp4_duration)
        if diff > 1:
            info(f"Mp4 duration differ from flv by {diff:.1f} sec: {repr(mp4_path)}")
            return False

        return True

    def remux(self, flv_path: str, mp4_path: str):
        try:
            ffmpeg.input(flv_path).output(mp4_path, c="copy").run(
                overwrite_output=True, capture_stdout=True, capture_stderr=True
            )
        except ffmpeg.Error as e:
            logger.error(f"Failed to remux {repr(flv_path)}")
            logger.error("stdout:", e.stdout.decode("utf8"))
            logger.error("stderr:", e.stderr.decode("utf8"))
            if os.path.exists(mp4_path):
                os.remove(mp4_path)

    def get_new_basename(self, basename: str):
        mp4_path = os.path.join(Settings.CACHE_DIR, f"{basename}.mp4")

        # parse basename
        if basename.startswith("录制"):
            roomid, date_str, time_str, title = [basename.split("-", 5)[i] for i in [1, 2, 3, 5]]
        else:
            roomid, date_str, time_str, title = basename.split("_", 3)

        # correct the time zone
        metadata = get_video_metadata(mp4_path)
        assert metadata is not None
        record_time_str = (
            metadata["format"]["tags"]["comment"].split("录制时间: ")[1].split("\n")[0]
        )
        # check that user time zone is Pacific, modify this line if you are in a different time zone
        assert record_time_str[-6:] in ["-07:00", "-08:00"]
        date_str = record_time_str[:10].replace("-", "")
        time_str = record_time_str[11:19].replace(":", "")
        new_basename = "_".join([roomid, date_str, time_str, title])
        # TODO: add overlap detection

        return new_basename
