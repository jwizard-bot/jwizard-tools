from re import compile as regex_compile

from .packages_extractor import PackagesExtractor


class PipPackagesExtractor(PackagesExtractor):
  def __init__(self, repo_name: str, branch: str):
    super().__init__(repo_name, branch, file_path="requirements.txt")

  def _extract_packages(self, raw_content: str):
    lines = raw_content.strip().splitlines()
    pattern = regex_compile(r"^[A-Za-z0-9_\-]+")

    for line in lines:
      line = line.strip()
      if not line or line.startswith("#"):
        continue

      match = pattern.match(line)
      if match:
        self.packages.append(match.group(0).lower())

  def determinate_package_link(self, package_name: str) -> str:
    return f"{self.base_url}/{package_name}"
