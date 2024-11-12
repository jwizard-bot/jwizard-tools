"""
Copyright (c) 2024 by JWizard
Originally developed by Miłosz Gilga <https://miloszgilga.pl>
"""
from logging import info, error
from sqlalchemy import Connection, text
from packages_grabber.gradle_extractor import GradlePackagesExtractor
from packages_grabber.node_extractor import NodePackagesExtractor
from packages_grabber.packages_extractor import PackagesExtractor
from packages_grabber.pip_extractor import PipPackagesExtractor

class PackagesGrabber:
  def __init__(self, connection: Connection, repo: str):
    """
    Initializes the PackagesGrabber instance.

    :param connection: The database connection used to execute SQL queries.
    :type connection: sqlalchemy.Connection

    :param repo: The repository name, used to fetch project data (e.g., 'user/repo').
    :type repo: str
    """
    self.connection = connection
    self.repo = repo
    self.project_id = None
    self.packages_md5 = None
    self.provider = None
    self.extractor = None
    self.extractors: dict[str, PackagesExtractor] = {
      "gradle": GradlePackagesExtractor,
      "node": NodePackagesExtractor,
      "pip": PipPackagesExtractor,
    }

  def __extract_project_parser_provider(self):
    """
    Retrieves the project ID, current MD5 hash of the dependency file, and the parser provider name for the given
    project.

    This information is fetched from the database using the repository name to match the project.
    """
    query = text("""
      SELECT p.id, p.packages_md5, ps.name FROM package_parsers ps
      INNER JOIN projects p ON p.parser_id = ps.id
      WHERE p.name = :project_name
    """)
    result = self.connection.execute(query, parameters={
      "project_name": self.repo.split("/")[1],
    })
    row = result.fetchone()
    if row:
      self.project_id = int(row[0])
      self.packages_md5 = str(row[1])
      self.provider = str(row[2])

  def __determinate_extractor(self):
    """
    Determines the appropriate extractor class based on the parser provider.

    This method selects the appropriate class for extracting package data based on the repository's provider (ex.
    Gradle, Node, or Pip). If the provider is unrecognized, it logs an error and terminates the process.
    """
    extractor: PackagesExtractor = self.extractors.get(self.provider, None)(repo_name=self.repo, branch="master")
    if not extractor:
      error(f"Unexpected provider: \"{self.provider}\".")
      info("Finished.")
      exit(0)
    self.extractor = extractor

  def __find_already_persisted_packages(self) -> list[str]:
    """
    Finds packages that are already persisted in the database for a given project.

    :return: A list of dependency names already persisted.
    :rtype: list[str]
    """
    query = text("SELECT name FROM project_packages WHERE project_id = :project_id")
    result = self.connection.execute(query, parameters={
      "project_id": self.project_id,
    })
    return [row[0] for row in result.fetchall()]

  def __persist_packages(self, packages: list[str]) -> int:
    """
    Persists a list of new packages into the database for the specified project.

    :param packages: List of dependency names to persist.
    :type packages: list[str]

    :return: The number of rows affected by the insert.
    :rtype: int
    """
    if not packages:
      return 0
    values = ','.join(f"('{name}',{self.project_id})" for name in packages)
    query = text(f"INSERT INTO project_packages (name, project_id) VALUES {values}")
    result = self.connection.execute(query)
    return result.rowcount

  def __drop_packages(self, packages: list[str]) -> int:
    """
    Deletes specified packages from the project_packages table in the database.

    :param packages: A list of package names to be removed.
    :type packages: list[str]

    :return: The number of rows affected (i.e., the number of packages deleted).
    :rtype: int
    """
    if not packages:
      return 0
    query = text(f"DELETE FROM project_packages WHERE project_id = :project_id AND name IN :names")
    result = self.connection.execute(query, parameters={
      "project_id": self.project_id,
      "names": tuple(packages),
    })
    return result.rowcount

  def __update_packages_md5(self):
    """
    Updates the MD5 hash of the dependency file in the database.

    This method updates the project's `packages_md5` field in the `projects` table to reflect the latest MD5 hash of 
    the dependency file after the packages have been processed.
    """
    query = text("UPDATE projects SET packages_md5 = :packages_md5 WHERE id = :project_id")
    self.connection.execute(query, parameters={
      "packages_md5": self.extractor.packages_md5,
      "project_id": self.project_id,
    })

  def grab_and_persist_packages(self) -> tuple[int, int]:
    """
    Grabs the packages for the specified repository, determines which packages need to be persisted or removed, 
    and updates the database accordingly.

    This method is the main entry point for grabbing package data, comparing it to existing entries in the database, 
    and performing insertions and deletions as necessary.

    :return: A tuple containing two integers: the number of packages persisted and the number of packages deleted.
    :rtype: tuple[int, int]
    """
    self.__extract_project_parser_provider()

    self.__determinate_extractor()
    self.extractor.extract_and_parse(self.packages_md5)

    persisted = self.__find_already_persisted_packages()
    to_persist = list(set(self.extractor.packages) - set(persisted))
    to_drop = list(set(persisted) - set(self.extractor.packages))

    for to_persist_package in to_persist:
      info(f"To persist: \"{to_persist_package}\".")

    for to_drop_package in to_drop:
      info(f"To drop: \"{to_drop_package}\".")

    info(f"Already persisted: {len(persisted)}, to persist: {len(to_persist)}, to drop: {len(to_drop)}.")
    persisted_in_db = self.__persist_packages(to_persist)
    dropped_from_db = self.__drop_packages(to_drop)

    self.__update_packages_md5()
    info(f"Lock file with MD5: \"{self.extractor.packages_md5}\".")
    return persisted_in_db, dropped_from_db
