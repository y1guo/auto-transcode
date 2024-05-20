import os
import shutil
from typing import Any, cast

import ffmpeg

from auto_transcode.utils.logger import get_logger


logger = get_logger(__name__)


def get_video_metadata(file_path: str):
    """Get the metadata of the video file.

    Returns:
        dict: The metadata of the video file.
        None: Failed to probe the file.
    """
    try:
        metadata = cast(dict[str, Any], ffmpeg.probe(file_path))
    except ffmpeg.Error as e:
        logger.error(f"Failed to probe {repr(file_path)}")
        logger.error(f"stdout: {e.stdout.decode('utf8')}")
        logger.error(f"stderr: {e.stderr.decode('utf8')}")
    else:
        return metadata


def get_video_codec_name(file_path: str):
    """Get the codec name of the video file.

    Returns:
        str: The codec name of the first video stream.
        None: Failed to probe the file.
    """
    metadata = get_video_metadata(file_path)
    if metadata is None:
        return
    for stream in metadata["streams"]:
        if stream["codec_type"] == "video":
            return stream["codec_name"]


def get_video_duration(file_path: str):
    """Get the duration of the video file in seconds.

    Returns:
        float: The duration of the video file in seconds.
        None: Failed to probe the file.
    """
    metadata = ffmpeg.probe(file_path)
    if metadata is None:
        return
    duration = float(metadata["format"]["duration"])
    return duration


def safe_move_and_rename_file(from_path: str, to_path: str, duplicate_count: int = 0):
    """Move and rename file from `from_path` to `to_path`.

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
        safe_move_and_rename_file(from_path, to_path, duplicate_count + 1)
        return

    shutil.copyfile(from_path, acting_to_path)
    os.remove(from_path)
    logger.info(f"Moved and renamed {repr(from_path)} to {repr(acting_to_path)}")
