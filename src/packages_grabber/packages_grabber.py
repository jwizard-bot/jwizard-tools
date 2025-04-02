from logging import info

from sqlalchemy import Connection, text

from .gradle_extractor import GradlePackagesExtractor
from .node_extractor import NodePackagesExtractor
from .packages_extractor import PackagesExtractor
from .pip_extractor import PipPackagesExtractor


class PackagesGrabber:
  def __init__(self, connection: Connection, repo: str, root_dir: str):
    self.connection = connection
    self.repo = repo
    self.root_dir = root_dir
    self.subproject_id = None
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
      SELECT s.id, s.packages_md5, pp.name FROM subprojects s
      INNER JOIN package_parsers pp ON pp.id = s.parser_id
      INNER JOIN projects p ON p.id = s.project_id
      WHERE p.name = :project_name AND s.root_dir = :root_dir
    """)
    result = self.connection.execute(query, parameters={
      "project_name": self.repo.split("/")[1],
      "root_dir": self.root_dir,
    })
    row = result.fetchone()
    if row:
      self.subproject_id = int(row[0])
      self.packages_md5 = str(row[1])
      self.provider = str(row[2])

  def _determinate_extractor(self):
    extractor: PackagesExtractor = self.extractors.get(self.provider, None)(
      repo_name=self.repo,
      branch="master",
      root_dir=f"{self.root_dir}/" if self.root_dir != "/" else self.root_dir,
    )
    if not extractor:
      raise Exception(f"Unexpected extractor provider: \"{self.provider}\".")

    self.extractor = extractor

  def _find_already_persisted_packages(self) -> list[str]:
    query = text("SELECT name FROM project_packages WHERE subproject_id = :subproject_id")
    result = self.connection.execute(query, parameters={
      "subproject_id": self.subproject_id,
    })
    return [row[0] for row in result.fetchall()]

  def _persist_packages(self, packages: list[str]):
    if not packages:
      return 0
    link_creator = self.extractor.determinate_package_link
    values = ",".join(
      f"('{name}','{link_creator(name)}',{self.subproject_id})" for name in packages
    )
    query = text(f"INSERT INTO project_packages (name, link, subproject_id) VALUES {values}")
    result = self.connection.execute(query)
    return result.rowcount

  def _drop_packages(self, packages: list[str]):
    if not packages:
      return 0
    query = text(f"""
      DELETE FROM project_packages WHERE subproject_id = :subproject_id AND name IN :names
    """)
    result = self.connection.execute(query, parameters={
      "subproject_id": self.subproject_id,
      "names": tuple(packages),
    })
    return result.rowcount

  def _update_packages_md5(self):
    query = text("UPDATE subprojects SET packages_md5 = :packages_md5 WHERE id = :subproject_id")
    self.connection.execute(query, parameters={
      "packages_md5": self.extractor.packages_md5,
      "subproject_id": self.subproject_id,
    })

  def grab_and_persist_packages(self) -> tuple[int, int]:
    info(f"Init packages grabber for subproject with root dir: \"{self.root_dir}\".")

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
