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

  def persist_updated_details(self) -> int:
    project_name = self.repo.split("/")[1]

    # check already persisted version
    query = text("SELECT latest_version_long FROM projects WHERE name = :project_name")
    result = self.connection.execute(query, parameters={
      "project_name": project_name
    })
    latest_version_long = result.scalar()

    # persisted only if version was changed (fix deadlock in front-end dashboard and landing-page
    # concurrency ci/cd pipelines, which can be updated db content as same time)
    updated_rows = 0
    if latest_version_long is None or latest_version_long != self.last_commit_sha:
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
      updated_rows = result.rowcount

    return updated_rows
