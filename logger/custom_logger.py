import logging
import logging.config
import os
from typing import Optional

import yaml

_CONFIGURED = False


def _resolve_config_path(config_path: Optional[str]) -> str:
    if config_path:
        return config_path
    return os.path.join(os.path.dirname(__file__), "logging.yaml")


def _apply_file_paths(config: dict) -> dict:
    base_dir = os.path.dirname(__file__)
    handlers = config.get("handlers", {})
    for handler_name in ("file", "error_file"):
        handler = handlers.get(handler_name)
        if not handler:
            continue
        filename = handler.get("filename")
        if filename:
            handler["filename"] = os.path.join(base_dir, filename)
            os.makedirs(os.path.dirname(handler["filename"]), exist_ok=True)
    return config


def configure_logging(config_path: Optional[str] = None) -> None:
    global _CONFIGURED
    if _CONFIGURED:
        return
    resolved_path = _resolve_config_path(config_path)
    with open(resolved_path, "r", encoding="utf-8") as handle:
        config = yaml.safe_load(handle)
    config = _apply_file_paths(config)
    logging.config.dictConfig(config)
    _CONFIGURED = True


def get_logger(name: str) -> logging.Logger:
    configure_logging()
    return logging.getLogger(name)
