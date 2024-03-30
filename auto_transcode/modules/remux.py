import os
import shutil

import ffmpeg

from auto_transcode.modules.base import WatcherProcess
from auto_transcode.settings import Settings
from auto_transcode.utils.logger import get_logger


# from datetime import datetime


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
        dir, filename = os.path.split(flv_path)
        basename, ext = os.path.splitext(filename)

        # check that file is FLV
        if ext != ".flv":
            logger.error(f"File {flv_path} is not an FLV file")
            return

        mp4_path = os.path.join(Settings.CACHE_DIR, f"{basename}.mp4")
        xml_from = os.path.join(dir, f"{basename}.xml")
        xml_to = os.path.join(Settings.CACHE_DIR, f"{basename}.xml")

        # TODO: empty video file might cause ffmpeg to fail

        if self.validate(flv_path, mp4_path, xml_from, xml_to):
            logger.info(f"File {repr(flv_path)} has already been remuxed")
        else:
            self.copy_xml(xml_from, xml_to)
            self.remux(flv_path, mp4_path)
            if not self.validate(flv_path, mp4_path, xml_from, xml_to):
                logger.error(f"Failed to remux {repr(flv_path)}")
                self.remove(mp4_path)
                self.remove(xml_to)
                return
        self.rename_mp4_xml(basename)
        self.remove(flv_path)
        self.remove(xml_from)

    def validate(self, flv_path: str, mp4_path: str, xml_from: str, xml_to: str):
        """Validate remuxed mp4 and xml files.

        Returns:
            bool: True if mp4 and xml are valid, False otherwise
        """
        # check xml
        logger.info(f"Validating {repr(xml_to)}")

        def read(file_path: str):
            try:
                with open(file_path, "r") as f:
                    content = f.read()
            except FileNotFoundError:
                logger.warning(f"File not found: {repr(file_path)}")
            except Exception as e:
                logger.error(f"Failed to read {repr(file_path)}: {repr(e)}")
            else:
                return content

        xml_from_content = read(xml_from)
        xml_to_content = read(xml_to)
        if xml_from_content is None or xml_to_content is None:
            return False
        if xml_from_content != xml_to_content:
            logger.warning("XML files are different")
            return False

        # check remux
        logger.info(f"Validating {repr(mp4_path)}")

        def get_duration(file_path: str):
            try:
                duration = float(ffmpeg.probe(file_path)["format"]["duration"])
            except Exception:
                logger.error(f"Failed to probe {repr(file_path)}")
            else:
                return duration

        flv_duration = get_duration(flv_path)
        mp4_duration = get_duration(mp4_path)
        if flv_duration is None or mp4_duration is None:
            return False
        diff = abs(flv_duration - mp4_duration)
        if diff > 1:
            logger.warning(f"FLV and MP4 durations are different by {diff:.1f} sec")
            return False

        return True

    def copy_xml(self, xml_from: str, xml_to: str) -> None:
        logger.info(f"Copying {repr(xml_from)} to {repr(xml_to)}")
        try:
            shutil.copyfile(xml_from, xml_to)
        except FileNotFoundError:
            logger.error(f"File {repr(xml_from)} not found")
        except FileExistsError:
            logger.error(f"File {repr(xml_to)} already exists")
        except IsADirectoryError:
            logger.error(f"File {repr(xml_from)} is a directory")
        except PermissionError:
            logger.error(f"Permission denied to copy {repr(xml_from)}")
        except Exception as e:
            logger.error(f"Failed to copy {repr(xml_from)}: {e}")
        else:
            logger.info(f"Copied {repr(xml_from)} to {repr(xml_to)}")

    def remux(self, flv_path: str, mp4_path: str) -> None:
        logger.info(f"Remuxing {repr(flv_path)} to {repr(mp4_path)}")
        try:
            ffmpeg.input(flv_path).output(mp4_path, c="copy").run(
                overwrite_output=True, capture_stdout=True, capture_stderr=True
            )
        except ffmpeg.Error as e:
            logger.error(f"Failed to remux {repr(flv_path)}")
            print("stdout:", e.stdout.decode("utf8"))
            print("stderr:", e.stderr.decode("utf8"))
        else:
            logger.info(f"Remuxed {repr(flv_path)} to {repr(mp4_path)}")

    def remove(self, file_path: str):
        logger.info(f"Removing {repr(file_path)}")
        try:
            os.remove(file_path)
        except FileNotFoundError:
            logger.error(f"File {repr(file_path)} not found")
        except IsADirectoryError:
            logger.error(f"File {repr(file_path)} is a directory")
        except PermissionError:
            logger.error(f"Permission denied to remove {repr(file_path)}")
        except Exception as e:
            logger.error(f"Failed to remove {repr(file_path)}: {e}")
        else:
            logger.info(f"Removed {repr(file_path)}")

    def rename_mp4_xml(self, basename: str):
        mp4_path = os.path.join(Settings.CACHE_DIR, f"{basename}.mp4")
        xml_path = os.path.join(Settings.CACHE_DIR, f"{basename}.xml")

        try:
            # parse basename
            if basename.startswith("录制"):
                roomid, date_str, time_str, title = [
                    basename.split("-", 6)[i] for i in [1, 2, 3, 5]
                ]
            else:
                roomid, date_str, time_str, title = basename.split("_", 4)

            probe = ffmpeg.probe(mp4_path)
            duration = float(probe["format"]["duration"])
            # remove recordings that are less than 30 seconds
            # TODO: add this setting to env
            if duration < 30:
                logger.info(f"Removed ({duration:.0f} sec) {basename}")
                os.remove(mp4_path)
                os.remove(xml_path)
                return
            # correct the time zone
            record_time_str = (
                probe["format"]["tags"]["comment"].split("录制时间: ")[1].split("\n")[0]
            )
            # TODO: this line should be removed in production, when user time zone is not us-west
            assert record_time_str[-6:] in ["-07:00", "-08:00"]
            date_str = record_time_str[:10].replace("-", "")
            time_str = record_time_str[11:19].replace(":", "")
            new_basename = "_".join([roomid, date_str, time_str, title])
            # start_time = datetime.strptime(date_str + time_str, "%Y%m%d%H%M%S").timestamp()
            # end_time = start_time + duration
            # TODO: add overlap detection
        except Exception as e:
            # If video file is empty, remove it. Ffmpeg failed to probe empty file.
            file_size = os.path.getsize(mp4_path)
            if file_size < 1000:
                logger.info(f"Removed ({file_size} B) {basename}")
                os.remove(mp4_path)
                os.remove(xml_path)
            else:
                logger.exception(f"Error occured while renaming {repr(mp4_path)}", repr(e))
            return
        else:
            new_mp4_path = os.path.join(Settings.REMUX_DIR, f"{new_basename}.mp4")
            new_xml_path = os.path.join(Settings.REMUX_DIR, f"{new_basename}.xml")
            self.rename(mp4_path, new_mp4_path)
            self.rename(xml_path, new_xml_path)

    def rename(self, from_path: str, to_path: str, duplicate_count: int = 0):
        """Move file from `from_path` to `to_path`.

        If `to_path` already exists, append a number to the file name according to `duplicate_count`

        Example:
            ```python
            move("a.txt", "b.txt") -> "a.txt" -> "b.txt"
            move("a.txt", "b.txt") -> "a.txt" -> "b_2.txt"
            move("a.txt", "b.txt") -> "a.txt" -> "b_3.txt"
            ```
        """
        if duplicate_count:
            basename, ext = os.path.splitext(to_path)
            acting_to_path = f"{basename}_{duplicate_count+1}{ext}"
        else:
            acting_to_path = to_path

        if os.path.exists(acting_to_path):
            self.rename(from_path, to_path, duplicate_count + 1)
            return

        logger.info(f"Renaming {repr(from_path)} to {repr(acting_to_path)}")
        try:
            shutil.move(from_path, acting_to_path)
        except FileNotFoundError:
            logger.error(f"File {repr(from_path)} not found")
        except FileExistsError:
            logger.error(f"File {repr(acting_to_path)} already exists")
        except IsADirectoryError:
            logger.error(f"File {repr(from_path)} is a directory")
        except PermissionError:
            logger.error(f"Permission denied to rename {repr(from_path)}")
        except Exception as e:
            logger.error(f"Failed to rename {repr(from_path)} to {repr(acting_to_path)}: {repr(e)}")
        else:
            logger.info(f"Renamed {repr(from_path)} to {repr(acting_to_path)}")
