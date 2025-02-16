from logging import info, error

from sqlalchemy import Connection, text

from .gradle_extractor import GradlePackagesExtractor
from .node_extractor import NodePackagesExtractor
from .packages_extractor import PackagesExtractor
from .pip_extractor import PipPackagesExtractor


class PackagesGrabber:
  def __init__(self, connection: Connection, repo: str):
    self.connection = connection
    self.repo = repo
    self.project_id = None
    self.packages_md5 = None
    self.provider = None
    self.extractor = None
    self.extractors = {
      "gradle": GradlePackagesExtractor,
      "node": NodePackagesExtractor,
      "pip": PipPackagesExtractor,
    }

  def _extract_project_parser_provider(self):
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

  def _determinate_extractor(self):
    extractor: PackagesExtractor = self.extractors.get(self.provider, None)(
      repo_name=self.repo,
      branch="master"
    )
    if not extractor:
      error(f"Unexpected provider: \"{self.provider}\".")
      info("Finished.")
      exit(0)
    self.extractor = extractor

  def _find_already_persisted_packages(self) -> list[str]:
    query = text("SELECT name FROM project_packages WHERE project_id = :project_id")
    result = self.connection.execute(query, parameters={
      "project_id": self.project_id,
    })
    return [row[0] for row in result.fetchall()]

  def _persist_packages(self, packages: list[str]):
    if not packages:
      return 0
    link_creator = self.extractor.determinate_package_link
    values = ','.join(f"('{name}','{link_creator(name)}',{self.project_id})" for name in packages)
    query = text(f"INSERT INTO project_packages (name, link, project_id) VALUES {values}")
    result = self.connection.execute(query)
    return result.rowcount

  def _drop_packages(self, packages: list[str]):
    if not packages:
      return 0
    query = text(f"DELETE FROM project_packages WHERE project_id = :project_id AND name IN :names")
    result = self.connection.execute(query, parameters={
      "project_id": self.project_id,
      "names": tuple(packages),
    })
    return result.rowcount

  def _update_packages_md5(self):
    query = text("UPDATE projects SET packages_md5 = :packages_md5 WHERE id = :project_id")
    self.connection.execute(query, parameters={
      "packages_md5": self.extractor.packages_md5,
      "project_id": self.project_id,
    })

  def grab_and_persist_packages(self) -> tuple[int, int]:
    self._extract_project_parser_provider()

    self._determinate_extractor()
    self.extractor.find_base_url(self.connection, self.provider)
    self.extractor.extract_and_parse(self.packages_md5)

    persisted = self._find_already_persisted_packages()
    to_persist = list(set(self.extractor.packages) - set(persisted))
    to_drop = list(set(persisted) - set(self.extractor.packages))

    for to_persist_package in to_persist:
      info(f"To persist: \"{to_persist_package}\".")

    for to_drop_package in to_drop:
      info(f"To drop: \"{to_drop_package}\".")

    info(f"Already persisted: {len(persisted)}, to persist: {len(to_persist)}, "
         f"to drop: {len(to_drop)}.")
    persisted_in_db = self._persist_packages(to_persist)
    dropped_from_db = self._drop_packages(to_drop)

    self._update_packages_md5()
    info(f"Lock file with MD5: \"{self.extractor.packages_md5}\".")
    return persisted_in_db, dropped_from_db
