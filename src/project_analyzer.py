from argparse import ArgumentParser
from logging import info, error

from dotenv import load_dotenv

from common.db import Db
from common.header import print_header
from common.logger import init_logger
from common.vault import VaultClient
from project_analyzer.code_lines_analyzer import CodeLinesAnalyzer
from project_analyzer.project_downloader import ProjectDownloader

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

  repo_downloader = None
  repo = args.repo
  try:
    repo_downloader = ProjectDownloader(repo, branch="master")
    repo_downloader.download_chunked_repo_content()

    code_lines_analyzer = CodeLinesAnalyzer(connection, repo, repo_downloader.output_dir_name)
    persisted, dropped, updated = code_lines_analyzer.analyze_and_persist()

    transaction.commit()
    info(f"Persisted: {persisted}, dropped: {dropped}, updated: {updated}.")

  except Exception as ex:
    transaction.rollback()
    error(f"Unable to execute action. Cause: \"{ex}\".")
    exit(1)

  finally:
    if repo_downloader:
      repo_downloader.clean_repo_content()  # clean temp files
    connection.close()
    vault_client.revoke_access()

  info("Finished.")


if __name__ == "__main__":
  main()
