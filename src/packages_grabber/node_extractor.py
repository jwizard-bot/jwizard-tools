from packages_extractor import PackagesExtractor


class NodePackagesExtractor(PackagesExtractor):
  def __init__(self, repo_name: str, branch: str):
    super().__init__(repo_name, branch, file_path="yarn.lock")

  def _extract_packages(self, raw_content: str):
    lines = raw_content.splitlines()
    parsed_lines = set()

    for line in lines:
      if line and not line.startswith((" ", "\t", "#")):
        line = line.strip().strip('"')
        if "," in line:
          line = line.split(",")[0]

        terminator_count = line.count("@")
        first_at_index = line.find('@')

        if terminator_count == 2:
          if line.startswith("@"):
            second_at_index = line.find("@", first_at_index + 1)
          else:
            second_at_index = line.find("@")
          line = line[:second_at_index]
        elif terminator_count == 1:
          line = line[:first_at_index]

        parsed_lines.add(line)

    self.packages = list(parsed_lines)

  def determinate_package_link(self, package_name: str) -> str:
    return f"{self.base_url}/{package_name}"
