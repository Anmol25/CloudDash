import os

from logger.custom_logger import _apply_file_paths


def test_apply_file_paths_resolves_and_creates_dirs():
    config = {
        "handlers": {
            "file": {"filename": "logs/app.log"},
            "error_file": {"filename": "logs/error.log"},
        }
    }
    result = _apply_file_paths(config)
    for handler_name in ("file", "error_file"):
        filename = result["handlers"][handler_name]["filename"]
        assert os.path.isabs(filename)
        assert os.path.isdir(os.path.dirname(filename))
