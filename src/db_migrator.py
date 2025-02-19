from argparse import ArgumentParser
from logging import info, error

from dotenv import load_dotenv

from common.db import Db
from common.header import print_header
from common.logger import init_logger
from common.vault import VaultClient
from db_migrator.file_parser import FileParser
from db_migrator.migrator import Migrator

init_logger()
load_dotenv()

table_name = "_applied_migrations"
base_directory = "migrations"


def main():
  print_header(initiator=__file__)

  arg_parser = ArgumentParser()
  arg_parser.add_argument("--pipeline", type=str, required=True)
  args = arg_parser.parse_args()

  vault_client = VaultClient()
  secrets = vault_client.get_secrets(kv_backend="jwizard", path="common")

  db = Db(secrets)
  connection = db.engine.connect()
  transaction = connection.begin()

  migrator = None
  try:
    file_parser = FileParser(f"{base_directory}/{args.pipeline}")
    migrator = Migrator(connection, file_parser, table_name)

    migrator.extract_applied_migrations()
    applied_migrations_count = migrator.execute_migrations()

    info(f"End up executed migrations. Applied: {applied_migrations_count} migrations.")
    transaction.commit()

  except Exception as ex:
    error(f"Unable to execute action. Rollback passed migration. Cause: \"{ex}\".")
    if migrator:
      migrator.execute_revert_migrations()
    exit(1)

  finally:
    connection.close()

  info("Finished.")


if __name__ == "__main__":
  main()
