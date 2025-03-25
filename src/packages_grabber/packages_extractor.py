from abc import ABC, abstractmethod
from hashlib import md5
from logging import info

from requests import get as request_get
from sqlalchemy import Connection, text


def calculate_md5(raw_content) -> str:
  hash_obj = md5()
  hash_obj.update(raw_content.encode("utf-8"))
  return hash_obj.hexdigest()


class PackagesExtractor(ABC):
  def __init__(self, repo_name: str, branch: str, file_path: str):
    self.repo_name = repo_name
    self.branch = branch
    self.file_path = file_path
    self.packages = []
    self.packages_md5 = None
    self.base_url = None

  def _fetch_raw_content(self) -> str:
    url = f"https://raw.githubusercontent.com/{self.repo_name}/{self.branch}/{self.file_path}"
    response = request_get(url)
    if response.status_code != 200:
      raise Exception("Unable to find packages file.")

    info(f"Download packages file: {self.file_path} from: {self.repo_name}.")
    return response.text

  def extract_and_parse(self, db_md5: str | None):
    raw_content = self._fetch_raw_content()
    self.packages_md5 = calculate_md5(raw_content)
    info(f"Calculated incoming MD5: \"{self.packages_md5}\", persisted MD5: \"{db_md5}\".")

    if self.packages_md5 == db_md5:
      info(f"Packages file for: \"{self.repo_name}\" has no changes. Skipping.")
      info("Finished.")
      exit(0)

    self._extract_packages(raw_content)
    info(f"Parsed: {len(self.packages)} libraries from: \"{self.repo_name}\" repository.")

  def find_base_url(self, connection: Connection, parser_name: str):
    query = text("SELECT base_url FROM package_parsers WHERE name = :parser_name")
    result = connection.execute(query, parameters={
      "parser_name": parser_name,
    })
    self.base_url = result.scalar()
    info(f"Determinate base url: \"{self.base_url}\" for package parser: \"{parser_name}\".")

  @abstractmethod
  def _extract_packages(self, raw_format: str):
    raise Exception("Method \"_extract_packages\" not implemented.")

  @abstractmethod
  def determinate_package_link(self, package_name: str) -> str:
    raise Exception("Method \"determinate_package_link\" not implemented.")
