#  Copyright (c) 2025 by JWizard
#  Originally developed by Miłosz Gilga <https://miloszgilga.pl>

import logging
from logging import StreamHandler
from sys import stdout


def init_logger():
  logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[StreamHandler(stdout)]
  )
