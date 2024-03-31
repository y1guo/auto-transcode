import os
import sys

from dotenv import load_dotenv

from auto_transcode.utils.logger import get_logger


load_dotenv()

logger = get_logger(__name__)


class Settings:
    FLV_DIRS: list[str]
    REMUX_DIR: str
    SAVE_DIR: str
    CACHE_DIR: str
    MINIMUM_FILE_SIZE: int
    MINIMUM_VIDEO_DURATION: float
    DAYS_BEFORE_REMUX: float
    DAYS_BEFORE_TRANSCODE: float
    WAKEUP_TIME: float

    @classmethod
    def init(cls):
        FLV_DIRS = cls.load_dirs("FLV_DIRS")
        REMUX_DIR = cls.load_dir("REMUX_DIR")
        SAVE_DIR = cls.load_dir("SAVE_DIR")
        CACHE_DIR = cls.load_dir("CACHE_DIR")
        MINIMUM_FILE_SIZE = cls.load_non_negative_int("MINIMUM_FILE_SIZE")
        MINIMUM_VIDEO_DURATION = cls.load_non_negative_float("MINIMUM_VIDEO_DURATION")
        DAYS_BEFORE_REMUX = cls.load_non_negative_float("DAYS_BEFORE_REMUX")
        DAYS_BEFORE_TRANSCODE = cls.load_non_negative_float("DAYS_BEFORE_TRANSCODE")
        WAKEUP_TIME = cls.load_non_negative_float("WAKEUP_TIME", "60")

        if (
            FLV_DIRS is None
            or REMUX_DIR is None
            or SAVE_DIR is None
            or CACHE_DIR is None
            or MINIMUM_FILE_SIZE is None
            or MINIMUM_VIDEO_DURATION is None
            or DAYS_BEFORE_REMUX is None
            or DAYS_BEFORE_TRANSCODE is None
            or WAKEUP_TIME is None
        ):
            logger.critical("Environment variable check failed")
            sys.exit(1)

        cls.FLV_DIRS = FLV_DIRS
        cls.REMUX_DIR = REMUX_DIR
        cls.SAVE_DIR = SAVE_DIR
        cls.CACHE_DIR = CACHE_DIR
        cls.MINIMUM_FILE_SIZE = MINIMUM_FILE_SIZE
        cls.MINIMUM_VIDEO_DURATION = MINIMUM_VIDEO_DURATION
        cls.DAYS_BEFORE_REMUX = DAYS_BEFORE_REMUX
        cls.DAYS_BEFORE_TRANSCODE = DAYS_BEFORE_TRANSCODE
        cls.WAKEUP_TIME = WAKEUP_TIME

    @classmethod
    def load_str(cls, var_name: str, default: str | None = None):
        value = os.getenv(var_name)
        if value is None:
            if default is None:
                logger.critical(f"{var_name} is not set")
            else:
                logger.warning(f"{var_name} is not set. Defaulting to {default}")
            return default
        return value

    @classmethod
    def load_dir(cls, var_name: str, default: str | None = None):
        value = cls.load_str(var_name, default)
        if value is None:
            return
        if not os.path.isdir(value):
            logger.critical(f"{var_name}={value} directory does not exist")
            return
        return value

    @classmethod
    def load_dirs(cls, var_name: str, default: str | None = None):
        value = cls.load_str(var_name, default)
        if value is None:
            return
        dirs = value.split(",")
        for dir in dirs:
            if not os.path.isdir(dir):
                logger.critical(f"{var_name}={dirs} directory does not exist: {repr(dir)}")
                return
        return dirs

    @classmethod
    def load_float(cls, var_name: str, default: str | None = None):
        value = cls.load_str(var_name, default)
        if value is None:
            return
        try:
            res = float(value)
        except ValueError:
            logger.critical(f"{var_name}={value} is not a float number")
            return
        else:
            return res

    @classmethod
    def load_int(cls, var_name: str, default: str | None = None):
        value = cls.load_str(var_name, default)
        if value is None:
            return
        try:
            res = int(value)
        except ValueError:
            logger.critical(f"{var_name}={value} is not an integer number")
            return
        else:
            return res

    @classmethod
    def load_non_negative_float(cls, var_name: str, default: str | None = None):
        value = cls.load_float(var_name, default)
        if value is None:
            return
        if value < 0:
            logger.critical(f"{var_name}={value} must be greater or equal to 0")
            return
        return value

    @classmethod
    def load_non_negative_int(cls, var_name: str, default: str | None = None):
        value = cls.load_int(var_name, default)
        if value is None:
            return
        if value < 0:
            logger.critical(f"{var_name}={value} must be greater or equal to 0")
            return
        return value


if __name__ == "__main__":
    Settings.init()
    logger.info(f"FLV_DIRS: {Settings.FLV_DIRS}")
    logger.info(f"REMUX_DIR: {Settings.REMUX_DIR}")
    logger.info(f"SAVE_DIR: {Settings.SAVE_DIR}")
    logger.info(f"CACHE_DIR: {Settings.CACHE_DIR}")
    logger.info(f"MINIMUM_FILE_SIZE: {Settings.MINIMUM_FILE_SIZE}")
    logger.info(f"MINIMUM_VIDEO_DURATION: {Settings.MINIMUM_VIDEO_DURATION}")
    logger.info(f"DAYS_BEFORE_REMUX: {Settings.DAYS_BEFORE_REMUX}")
    logger.info(f"DAYS_BEFORE_TRANSCODE: {Settings.DAYS_BEFORE_TRANSCODE}")
    logger.info(f"WAKEUP_TIME: {Settings.WAKEUP_TIME}")
