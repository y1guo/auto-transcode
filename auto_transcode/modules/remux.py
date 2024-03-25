import os
import shutil

import ffmpeg

from auto_transcode.modules.base import WatcherProcess
from auto_transcode.settings import Settings
from auto_transcode.utils.logger import get_logger


logger = get_logger(__name__)


class RemuxProcess(WatcherProcess):
    def __init__(self):
        super().__init__(process_name="Remux")

    def main(self):
        for flv_dir in Settings.FLV_DIRS:
            self.watch(
                dir=flv_dir,
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
        self.remove(flv_path)
        self.remove(xml_from)

    def validate(self, flv_path: str, mp4_path: str, xml_from: str, xml_to: str):
        """Validate remuxed mp4 and xml files.

        Returns:
            bool: True if mp4 and xml are valid, False otherwise
        """
        # check xml
        try:
            with open(xml_from, "r") as f:
                xml_from_content = f.read()
            with open(xml_to, "r") as f:
                xml_to_content = f.read()
            if xml_from_content != xml_to_content:
                raise ValueError("XML files are different")
        except Exception:
            return False

        # check remux
        try:
            flv_duration = float(ffmpeg.probe(flv_path)["format"]["duration"])
            mp4_duration = float(ffmpeg.probe(mp4_path)["format"]["duration"])
        except Exception:
            return False
        else:
            if abs(flv_duration - mp4_duration) > 1:
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
