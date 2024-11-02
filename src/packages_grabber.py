"""
Copyright (c) 2024 by JWizard
Originally developed by Miłosz Gilga <https://miloszgilga.pl>
"""
from sqlalchemy import text
from logging import info, error
from common.logger import *
from common.header import print_header
from common.vault import VaultClient
from common.arg_parser import ArgParser
from common.db import Db
from packages_grabber.packages_extractor import GradlePackagesExtractor, NodePackagesExtractor

def get_project_parser_provider(project_name: str):
  """
  Retrieves the project ID, current MD5 hash of the dependency file, and the parser provider name for a given project.

  :param project_name: The name of the project to fetch.
  :type project_name: str

  :return: A tuple containing the project ID, file MD5 hash, and parser provider name, or None for each if not found.
  :rtype: tuple[int | None, str | None, str | None]
  """
  query = text("""
    SELECT p.id, p.file_md5, ps.name FROM parsers ps
    INNER JOIN projects p ON p.parser_id = ps.id
    WHERE p.name = :project_name
  """)
  result = connection.execute(query, parameters={
    "project_name": project_name
  })
  row = result.fetchone()
  if row:
    return int(row[0]), row[1], str(row[2])
  return None, None


def determinate_extractor(parser_provider: str):
  """
  Determines the dependency extractor based on the parser provider.

  :param parser_provider: The parser provider (ex. "gradle" or "node").
  :type parser_provider: str

  :return: An instance of GradlePackagesExtractor or NodePackagesExtractor, or None if provider is unknown.
  :rtype: GradlePackagesExtractor | NodePackagesExtractor | None
  """
  extractor = None
  if parser_provider == "gradle":
    extractor = GradlePackagesExtractor(repo_name=args.repo, branch="master")
  elif provider == "node":
    extractor = NodePackagesExtractor(repo_name=args.repo, branch="master")
  else:
    error(f"Unexpected provider: {parser_provider}.")
    info("Finished.")
    exit(0)
  return extractor


def update_file_md5(file_md5: str, project_id: int):
  """
  Updates the MD5 hash of the dependency file in the database.

  :param file_md5: The new MD5 hash of the dependency file.
  :type file_md5: str

  :param project_id: The ID of the project to update.
  :type project_id: int
  """
  query = text("UPDATE projects SET file_md5 = :file_md5 WHERE id = :project_id")
  connection.execute(query, parameters={
    "file_md5": file_md5,
    "project_id": project_id,
  })


def find_already_persisted_packages(project_id: int) -> list[str]:
  """
  Finds packages that are already persisted in the database for a given project.

  :param project_id: The ID of the project to search packages for.
  :type project_id: int

  :return: A list of dependency names already persisted.
  :rtype: list[str]
  """
  query = text("SELECT name FROM project_packages WHERE project_id = :project_id")
  result = connection.execute(query, parameters={
    "project_id": project_id,
  })
  return [row[0] for row in result.fetchall()]


def persist_packages(packages: list[str], project_id: int) -> int:
  """
  Persists a list of new packages into the database for the specified project.

  :param packages: List of dependency names to persist.
  :type packages: list[str]

  :param project_id: The ID of the project to associate packages with.
  :type project_id: int

  :return: The number of rows affected by the insert.
  :rtype: int
  """
  values = ','.join(f"('{name}',{project_id})" for name in packages)
  query = text(f"INSERT INTO project_packages (name, project_id) VALUES {values}")
  return connection.execute(query)


def drop_packages(packages: list[str], project_id: int) -> int:
  query = text(f"DELETE FROM project_packages WHERE project_id = :project_id AND name IN :names")
  return connection.execute(query, parameters={
    "project_id": project_id,
    "names": tuple(packages),
  })


if __name__ == '__main__':
  print_header(initiator=__file__)

  arg_parser = ArgParser()
  arg_parser.add_argument("--repo", type=str, required=True)
  args = arg_parser.get_args()

  vault_client = VaultClient(args)
  secrets = vault_client.get_secrets(kv_backend="jwizard", path="common")

  db = Db(
    host=secrets["V_MYSQL_HOST"],
    username=secrets["V_MYSQL_USERNAME"],
    password=secrets["V_MYSQL_PASSWORD"],
    db_name=secrets["V_MYSQL_DB_NAME"],
  )
  with db.engine.connect() as connection:
    try:
      project_id, file_md5, provider = get_project_parser_provider(args.repo)
      extractor = determinate_extractor(provider)
      extractor.extract_and_parse(file_md5)

      persisted = find_already_persisted_packages(project_id)
      to_persist = list(set(extractor.packages) - set(persisted))
      to_drop = list(set(persisted) - set(extractor.packages))

      for to_persist_package in to_persist:
        info(f"To persist: {to_persist_package}.")

      for to_drop_package in to_drop:
        info(f"To drop: {to_drop_package}.")

      info(f"Already persisted: {len(persisted)}, to persist: {len(to_persist)}, to drop: {len(to_drop)}.")

      persisted_in_db = persist_packages(to_persist, project_id)
      dropped_from_db = drop_packages(to_drop, project_id)
      connection.commit()

      update_file_md5(extractor.file_md5, project_id)
      info(f"Lock file with MD5: {extractor.file_md5}.")

      info(f"Persisted: {persisted_in_db.rowcount} packages, dropped: {dropped_from_db.rowcount} packages.")

    except Exception as ex:
      connection.rollback()
      error(f"Unable to execute action. Cause: {ex}.")

  info("Finished.")
