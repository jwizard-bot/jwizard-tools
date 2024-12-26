"""
Copyright (c) 2024 by JWizard
Originally developed by Miłosz Gilga <https://miloszgilga.pl>
"""
from re import compile as regex_compile
from packages_grabber.packages_extractor import PackagesExtractor

class PipPackagesExtractor(PackagesExtractor):
  """
  Extractor for Python package files (specifically requirements.txt format).

  Inherits from PackagesExtractor and specifies the file path for Python packages.
  """
  def __init__(self, repo_name: str, branch: str):
    """
    Initializes the PipPackagesExtractor with repository details and a specific file path for Python packages.

    :param repo_name: The name of the repository.
    :type repo_name: str

    :param branch: The branch of the repository to fetch.
    :type branch: str
    """
    super().__init__(repo_name, branch, file_path="requirements.txt")

  def _extract_packages(self, raw_content: str):
    """
    Extracts packages names from the requirements.txt content.

    :param raw_content: The raw content of the requirements.txt file.
    :type raw_content: str
    """
    lines = raw_content.strip().splitlines()
    pattern = regex_compile(r'^[A-Za-z0-9_\-]+')

    for line in lines:
      line = line.strip()
      if not line or line.startswith("#"):
        continue

      match = pattern.match(line)
      if match:
        self.packages.append(match.group(0).lower())

  def determinate_package_link(self, package_name: str) -> str:
    """
    Generates the full URL link for a python package based on its name.

    :param package_name: The name of the package for which the link is generated.
    :type package_name: str

    :return: The full URL link to the package.
    :rtype: str
    """
    return f"{self.base_url}/{package_name}"
