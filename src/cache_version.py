"""
Copyright (c) 2024 by JWizard
Originally developed by Miłosz Gilga <https://miloszgilga.pl>
"""
from argparse import ArgumentParser
from dotenv import load_dotenv
from logging import error, info
from common.db import Db
from common.header import print_header
from common.logger import *
from common.vault import VaultClient
from cache_version.cache_version import CacheVersion

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
    cache_version = CacheVersion(connection, args.repo)

    cache_version.extract_last_sha()
    affected_rows = cache_version.persist_updated_details()

    transaction.commit()
    info(f"Affected: {affected_rows} rows.")
    info(f"Persisted: \"{cache_version.last_commit_sha}\" version and update time: \"{cache_version.updated_time}\".")

  except Exception as ex:
    transaction.rollback()
    error(f"Unable to execute action. Cause: {ex}.")
    exit(1)

  finally:
    connection.close()

  info("Finished.")

if __name__ == "__main__":
  main()