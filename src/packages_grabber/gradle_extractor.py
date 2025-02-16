from toml import loads as loads_tom

from .packages_extractor import PackagesExtractor


class GradlePackagesExtractor(PackagesExtractor):
  def __init__(self, repo_name: str, branch: str):
    super().__init__(repo_name, branch, file_path="gradle/libs.versions.toml")

  def _extract_packages(self, raw_content):
    parsed_content = loads_tom(raw_content)
    if not "libraries" in parsed_content:
      return
    for _, details in parsed_content["libraries"].items():
      if "module" in details:
        self.packages.append(details["module"].lower())

  def determinate_package_link(self, package_name: str) -> str:
    package_without_semi = package_name.replace(":", "/")
    return f"{self.base_url}/{package_without_semi}"
