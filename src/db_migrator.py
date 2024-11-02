"""
Copyright (c) 2024 by JWizard
Originally developed by Miłosz Gilga <https://miloszgilga.pl>
"""
from logging import info
from dotenv import load_dotenv
from common.logger import *
from common.header import print_header
from common.vault import VaultClient
from common.db import Db

load_dotenv()

if __name__ == '__main__':
  print_header(initiator=__file__)

  vault_client = VaultClient()
  secrets = vault_client.get_secrets(kv_backend="jwizard", path="common")

  db = Db(
    host=secrets["V_MYSQL_HOST"],
    username=secrets["V_MYSQL_USERNAME"],
    password=secrets["V_MYSQL_PASSWORD"],
    db_name=secrets["V_MYSQL_DB_NAME"],
  )

  info(f"Finished.")