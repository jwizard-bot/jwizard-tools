#  Copyright (c) 2025 by JWizard
#  Originally developed by Miłosz Gilga <https://miloszgilga.pl>

from .packages_extractor import PackagesExtractor


class NodePackagesExtractor(PackagesExtractor):
  """
  Extractor for Node.js package files (specifically yarn.lock format).

  Inherits from PackagesExtractor and specifies the file path for Node.js packages.
  """

  def __init__(self, repo_name: str, branch: str):
    """
    Initializes the NodePackagesExtractor with repository details and a specific file path for Node.js packages.

    :param repo_name: The name of the repository.
    :type repo_name: str

    :param branch: The branch of the repository to fetch.
    :type branch: str
    """
    super().__init__(repo_name, branch, file_path="yarn.lock")

  def _extract_packages(self, raw_content: str):
    """
    Extracts packages names from the Node.js yarn.lock content.

    :param raw_content: The raw content of the yarn.lock file.
    :type raw_content: str
    """
    lines = raw_content.splitlines()
    parsed_lines = set()

    for line in lines:
      if line and not line.startswith((' ', '\t', '#')):
        line = line.strip().strip('"')
        if ',' in line:
          line = line.split(',')[0]

        terminator_count = line.count("@")
        first_at_index = line.find('@')

        if terminator_count == 2:
          if line.startswith('@'):
            second_at_index = line.find('@', first_at_index + 1)
          else:
            second_at_index = line.find('@')
          line = line[:second_at_index]
        elif terminator_count == 1:
          line = line[:first_at_index]

        parsed_lines.add(line)

    self.packages = list(parsed_lines)

  def determinate_package_link(self, package_name: str) -> str:
    """
    Generates the full URL link for a node package based on its name.

    :param package_name: The name of the package for which the link is generated.
    :type package_name: str

    :return: The full URL link to the package.
    :rtype: str
    """
    return f"{self.base_url}/{package_name}"
