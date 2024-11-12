"""
Copyright (c) 2024 by JWizard
Originally developed by Miłosz Gilga <https://miloszgilga.pl>
"""
from requests import get as request_get
from logging import info, error
from hashlib import md5
from abc import ABC, abstractmethod

class PackagesExtractor(ABC):
  """
  Abstract base class for extracting packages from various file formats.

  :param repo_name: The name of the repository.
  :type repo_name: str

  :param branch: The branch of the repository to fetch the file from.
  :type branch: str

  :param file_path: The path to the packages file in the repository.
  :type file_path: str
  """

  def __init__(self, repo_name: str, branch: str, file_path: str):
    """
    Initializes the packages extractor with repository details.

    :param repo_name: The name of the repository.
    :type repo_name: str

    :param branch: The branch of the repository to fetch.
    :type branch: str

    :param file_path: The path to the packages file.
    :type file_path: str
    """
    self.repo_name = repo_name
    self.branch = branch
    self.file_path = file_path
    self.packages = []
    self.packages_md5 = None

  def __fetch_raw_content(self) -> str:
    """
    Fetches the raw content of the packages file from the GitHub repository.

    :return: The raw content of the packages file.
    :rtype: str
    :raises SystemExit: If the request fails with a non-200 status code.
    """
    url = f"https://raw.githubusercontent.com/{self.repo_name}/{self.branch}/{self.file_path}"
    response = request_get(url)
    if response.status_code != 200:
      error(f"Unable to find packages file. Stopping pipeline.")
      info("Finished.")
      exit(1)

    info(f"Download packages file: {self.file_path} from: {self.repo_name}.")
    return response.text

  def extract_and_parse(self, db_md5: str | None):
    """
    Extracts and parses packages from the raw content, comparing file content against the provided database MD5 hash to
    determine if parsing is needed.

    :param db_md5: The MD5 hash of the current database content to compare against.
    :type db_md5: str | None
    """
    raw_content = self.__fetch_raw_content()
    self.packages_md5 = self.__calculate_md5(raw_content)
    info(f"Calculated incoming MD5: \"{self.packages_md5}\", persisted MD5: \"{db_md5}\".")

    if self.packages_md5 == db_md5:
      info(f"Packages file for: \"{self.repo_name}\" has no changes. Skipping.")
      info("Finished.")
      exit(0)

    self._extract_packages(raw_content)
    info(f"Parsed: {len(self.packages)} libraries from: \"{self.repo_name}\" repository.")

  def __calculate_md5(self, raw_content) -> str:
    """
    Calculates the MD5 hash of the provided raw content.

    :param raw_content: The raw content to hash.
    :type raw_content: str

    :return: The MD5 hash of the content.
    :rtype: str
    """
    hash_obj = md5()
    hash_obj.update(raw_content.encode('utf-8'))
    return hash_obj.hexdigest()

  @abstractmethod
  def _extract_packages(raw_format: str):
    """
    Abstract method for extracting packages from raw content.
    Must be implemented by subclasses.

    :param raw_format: The raw content to extract packages from.
    :type raw_format: str
    """
    pass
