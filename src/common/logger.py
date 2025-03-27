import logging
from logging import StreamHandler
from sys import stdout


def init_logger():
  logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[StreamHandler(stdout)]
  )
  logging.getLogger("paramiko").setLevel(logging.CRITICAL)
