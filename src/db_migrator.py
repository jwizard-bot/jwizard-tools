"""
Copyright (c) 2024 by JWizard
Originally developed by Miłosz Gilga <https://miloszgilga.pl>
"""
from logging import info
from common.logger import *
from common.header import print_header
from common.vault import VaultClient
from common.arg_parser import ArgParser
from common.db import Db

if __name__ == '__main__':
  print_header(initiator=__file__)

  arg_parser = ArgParser()
  args = arg_parser.get_args()

  vault_client = VaultClient(args)
  secrets = vault_client.get_secrets(kv_backend="jwizard", path="common")

  db = Db(
    host=secrets["V_MYSQL_HOST"],
    username=secrets["V_MYSQL_USERNAME"],
    password=secrets["V_MYSQL_PASSWORD"],
    db_name=secrets["V_MYSQL_DB_NAME"],
  )

  info(f"Finished.")