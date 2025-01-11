#  Copyright (c) 2025 by JWizard
#  Originally developed by Miłosz Gilga <https://miloszgilga.pl>

from argparse import ArgumentParser
from logging import info, error

from dotenv import load_dotenv

from common.db import Db
from common.header import print_header
from common.logger import init_logger
from common.vault import VaultClient
from packages_grabber.packages_grabber import PackagesGrabber

init_logger()
load_dotenv()


def main():
  print_header(initiator=__file__)

  arg_parser = ArgumentParser()
  arg_parser.add_argument("--repo", type=str, required=True)
  args = arg_parser.parse_args()

  vault_client = VaultClient()
  secrets = vault_client.get_secrets(kv_backend="jwizard", path="common")

  db = Db(secrets)
  connection = db.engine.connect()
  transaction = connection.begin()

  try:
    packages_grabber = PackagesGrabber(connection, args.repo)
    persisted_in_db, dropped_from_db = packages_grabber.grab_and_persist_packages()

    transaction.commit()
    info(f"Persisted: {persisted_in_db} packages, dropped: {dropped_from_db} packages.")

  except Exception as ex:
    transaction.rollback()
    error(f"Unable to execute action. Cause: {ex}.")
    exit(1)

  finally:
    connection.close()

  info("Finished.")


if __name__ == '__main__':
  main()
