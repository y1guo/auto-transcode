import os
import sys

from dotenv import load_dotenv

from auto_transcode.utils.logger import get_logger


load_dotenv()

logger = get_logger(__name__)


class Settings:
    FLV_DIRS: list[str] = ["test/flv"]
    REMUX_DIR: str = "test/remux"
    SAVE_DIR: str = "test/save"
    CACHE_DIR: str = "test/cache"
    MIN_FLV_SIZE: int = 1000
    MIN_FLV_DURATION: float = 30
    DAYS_BEFORE_REMUX: float = 0
    DAYS_BEFORE_TRANSCODE: float = 0
    CONSTANT_QUALITY: int = 51
    WAKEUP_TIME: float = 60

    @classmethod
    def init(cls):
        # Skip initialization if running in development mode
        USE_DEV_SETTINGS = cls.load_bool("USE_DEV_SETTINGS", "false")
        if USE_DEV_SETTINGS:
            cls.print_settings()
            logger.warning("Running in development mode, using preset settings")
            return

        # Load environment variables
        loaders = [
            ("FLV_DIRS", cls.load_dirs, None),
            ("REMUX_DIR", cls.load_dir, None),
            ("SAVE_DIR", cls.load_dir, None),
            ("CACHE_DIR", cls.load_dir, None),
            ("MIN_FLV_SIZE", cls.load_non_negative_int, None),
            ("MIN_FLV_DURATION", cls.load_non_negative_float, None),
            ("DAYS_BEFORE_REMUX", cls.load_non_negative_float, None),
            ("DAYS_BEFORE_TRANSCODE", cls.load_non_negative_float, None),
            ("CONSTANT_QUALITY", cls.load_int, cls.CONSTANT_QUALITY),
            ("WAKEUP_TIME", cls.load_non_negative_float, cls.WAKEUP_TIME),
        ]

        check_passed = True
        for name, loader, default in loaders:
            value = loader(name, default)
            if value is None:
                check_passed = False
            setattr(cls, name, value)

        if not check_passed:
            logger.critical("Environment variable check failed")
            sys.exit(1)

        cls.print_settings()
        logger.info("Successfully loaded environment variables")

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
    def load_bool(cls, var_name: str, default: str | None = None):
        value = cls.load_str(var_name, default)
        if value is None:
            return
        if value.lower() == "true":
            return True
        if value.lower() == "false":
            return False
        logger.critical(f"{var_name}={value} is not a boolean")
        return

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

    @classmethod
    def print_settings(cls):
        for key, value in cls.__dict__.items():
            if key.startswith("_"):
                continue
            if isinstance(value, classmethod):
                continue
            logger.info(f"{key}: {value}")


if __name__ == "__main__":
    Settings.init()
