"""
Copyright (c) 2024 by JWizard
Originally developed by Miłosz Gilga <https://miloszgilga.pl>
"""
from argparse import ArgumentParser
from datetime import datetime, timezone
from dotenv import load_dotenv
from logging import error, info
from requests import get as request_get
from sqlalchemy import text
from common.db import Db
from common.logger import *
from common.header import print_header
from common.vault import VaultClient

load_dotenv()

def get_last_sha(repo: str):
  url = f"https://api.github.com/repos/{repo}/commits"
  response = request_get(url)
  if response.status_code != 200:
      error(f"Unable to find repository commits. Stopping pipeline.")
      info("Finished.")
      exit(1)

  commits = response.json()
  last_commit_sha = commits[0]['sha']

  info(f"Fetch last commit SHA: {last_commit_sha} from: {repo}.")
  return last_commit_sha


def persist_updated_details(version: str, time_utc: datetime, repo: str) -> int:
  query = text("""
    UPDATE projects SET latest_version_long = :version, last_updated_utc = :time_utc
    WHERE name = :project_name
  """)
  result = connection.execute(query, parameters={
    "version": version,
    "time_utc": time_utc,
    "project_name": repo.split("/")[1]
  })
  return result.rowcount


if __name__ == "__main__":
  print_header(initiator=__file__)

  arg_parser = ArgumentParser()
  arg_parser.add_argument("--repo", type=str, required=True)
  args = arg_parser.parse_args()

  vault_client = VaultClient()
  secrets = vault_client.get_secrets(kv_backend="jwizard", path="common")

  db = Db(
    host=secrets["V_MYSQL_HOST"],
    username=secrets["V_MYSQL_USERNAME"],
    password=secrets["V_MYSQL_PASSWORD"],
    db_name=secrets["V_MYSQL_DB_NAME"],
  )
  with db.engine.connect() as connection:
    try:
      version = get_last_sha(args.repo)
      update_time = datetime.now(timezone.utc)

      affected_rows = persist_updated_details(version, update_time, args.repo)

      connection.commit()
      info(f"Affected: {affected_rows} rows. Persisted: {version} version and update time: {update_time}.")

    except Exception as ex:
      connection.rollback()
      error(f"Unable to execute action. Cause: {ex}.")
      exit(1)

  info("Finished.")
