import logging
import logging.config
import yaml


def configure(path="./config/logging.yaml"):
    with open(path, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)
    logging.config.dictConfig(config)

def log_exception(type, value, tb):
    logging.exception("Uncaught exception: {0}".format(str(value)))
