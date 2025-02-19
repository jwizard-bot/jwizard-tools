from datetime import datetime, timezone
from logging import info

from requests import get as request_get
from sqlalchemy import Connection, text


class CacheVersion:
  def __init__(self, connection: Connection, repo: str):
    self.connection = connection
    self.repo = repo
    self.last_commit_sha = None
    self.updated_time = None

  def extract_last_sha(self):
    url = f"https://api.github.com/repos/{self.repo}/commits"
    response = request_get(url)
    if response.status_code != 200:
      raise Exception("Unable to find repository commits.")

    commits = response.json()
    self.last_commit_sha = commits[0]["sha"]

    info(f"Fetch last commit SHA: \"{self.last_commit_sha}\" from: \"{self.repo}\".")

  def persist_updated_details(self):
    self.updated_time = datetime.now(timezone.utc)
    query = text("""
      UPDATE projects SET latest_version_long = :version, last_updated_utc = :time_utc
      WHERE name = :project_name
    """)
    result = self.connection.execute(query, parameters={
      "version": self.last_commit_sha,
      "time_utc": self.updated_time,
      "project_name": self.repo.split("/")[1]
    })
    return result.rowcount
