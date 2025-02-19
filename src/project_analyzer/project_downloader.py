from logging import info, error
from os import path, mkdir, remove, getenv
from shutil import rmtree
from tarfile import open as open_tar
from time import sleep

from humanize import naturalsize
from requests import get as request_get


# download whole GitHub repository for further data processing
# based "repo" property in format organization/repository and branch
class ProjectDownloader:
  def __init__(self, repo: str, branch: str):
    self.repo = repo
    self.branch = branch
    self.root_dir = ".temp"
    self.output_dir_name = None  # will be set after untar archive
    self.tar_archive_name = f"{path.basename(repo)}-{branch}.tar.gz"

  def download_chunked_repo_content(self):
    token = getenv("GITHUB_TOKEN")  # from ci/cd pipeline
    url = f"https://api.github.com/repos/{self.repo}/tarball/{self.branch}"
    headers = {}

    # add bearer only if exists
    if token:
      headers["Authorization"] = f"Bearer {token}"
      info(f"Found GITHUB_TOKEN. Authorize further requests with this token.")

    block_size = 1024  # count of bytes in single request block
    attempt = 0
    max_retries = 10
    delay = 5

    downloaded_size = 0
    while attempt < max_retries:
      rmtree(".temp", ignore_errors=True)  # clear previous directory content
      mkdir(".temp")

      downloaded_size = 0
      try:
        response = request_get(url, headers=headers, stream=True)
        response.raise_for_status()  # raise any none 2XX codes

        with open(self.tar_archive_name, "wb") as file:
          for chunk in response.iter_content(block_size):
            file.write(chunk)
            downloaded_size += len(chunk)

        break
      except Exception as e:
        error(f"Downloading file: \"{self.tar_archive_name}\" error: \"{e}\".")
        attempt += 1
        if attempt < max_retries:
          info(f"Trying again at {delay}s. {attempt} attempt...")
          sleep(delay)
        else:
          raise Exception(f"Unable to download file: \"{self.tar_archive_name}\". Cause: \"{e}\".")

    info(f"Downloaded: \"{self.tar_archive_name}\" file (size: {naturalsize(downloaded_size)}).")

    with open_tar(self.tar_archive_name, "r:gz") as tar:
      members = tar.getmembers()
      # we assume, that tarball return all content inside one root directory
      root_folder_name = path.basename(members[0].name)
      self.output_dir_name = f"{self.root_dir}/{root_folder_name}/"

      tar.extractall(path=self.root_dir)
      info(f"Extracted: \"{self.tar_archive_name}\" to: \"{self.output_dir_name}\".")

    remove(self.tar_archive_name)
    info(f"Removed temporary \"{self.tar_archive_name}\" file.")

  def clean_repo_content(self):
    if path.exists(self.root_dir):
      rmtree(self.root_dir)
      info(f"Removed repository content: \"{self.output_dir_name}\".")
