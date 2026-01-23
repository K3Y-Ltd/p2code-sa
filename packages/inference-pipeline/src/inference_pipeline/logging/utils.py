from typing import Dict


def fmt_msg(
    msg: str, level: int = 1, indent: int = 4, symbol: str | None = None
) -> str:
    """
    Format message based on indentation level.
    """
    symbols = {
        1: ">",
        2: "▶",
        3: "-",
    }

    if symbol is not None:
        _symbol = symbol + " "
    else:
        _symbol = symbols.get(level, "-") + " "

    pfx = " " * level * indent + _symbol

    return pfx + msg


def cntr_msg(msg: str, pad: int = 70) -> str:
    """
    Center message
    """
    return (" " + msg + " ").center(pad, "─")


def get_default_logging_config() -> Dict:
    """
    A default logging configuration.
    """
    return {
        "version": 1,
        "formatters": {
            "standard": {
                "format": "[%(asctime)s] %(levelname)-7s - %(message)s",
                "datefmt": "%m/%d/%Y %I:%M:%S %p",
            }
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "level": "DEBUG",
                "formatter": "standard",
            },
        },
        "loggers": {
            "inference_pipeline.api.app": {
                "handlers": ["console"],
                "level": "DEBUG",
            },
        },
        "root": {
            "handlers": ["console"],
            "level": "DEBUG",
        },
    }
