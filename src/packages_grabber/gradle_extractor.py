"""
Copyright (c) 2024 by JWizard
Originally developed by Miłosz Gilga <https://miloszgilga.pl>
"""
from toml import loads as loads_tom
from packages_grabber.packages_extractor import PackagesExtractor

class GradlePackagesExtractor(PackagesExtractor):
  """
  Extractor for Gradle packages files (specifically libs.versions.toml format).

  Inherits from PackagesExtractor and specifies the file path for Gradle packages.
  """

  def __init__(self, repo_name: str, branch: str):
    """
    Initializes the GradlePackagesExtractor with repository details and a specific file path for Gradle packages.

    :param repo_name: The name of the repository.
    :type repo_name: str

    :param branch: The branch of the repository to fetch.
    :type branch: str
    """
    super().__init__(repo_name, branch, file_path="gradle/libs.versions.toml")

  def _extract_packages(self, raw_content):
    """
    Extracts packages names from the parsed Gradle TOML content.

    :param raw_content: The raw content of the TOML file.
    :type raw_content: str
    """
    parsed_content = loads_tom(raw_content)
    if not "libraries" in parsed_content:
      return
    for _, details in parsed_content["libraries"].items():
      if "module" in details:
        self.packages.append(details["module"].lower())