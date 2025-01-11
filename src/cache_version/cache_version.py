#  Copyright (c) 2025 by JWizard
#  Originally developed by Miłosz Gilga <https://miloszgilga.pl>

from datetime import datetime, timezone
from logging import error, info

from requests import get as request_get
from sqlalchemy import Connection, text


class CacheVersion:
  def __init__(self, connection: Connection, repo: str):
    """
    Initializes the CacheVersion instance for tracking the latest commit SHA and update details of a repository.

    :param connection: The database connection used to execute SQL queries.
    :type connection: sqlalchemy.Connection

    :param repo: The GitHub repository in the format 'owner/repository'.
    :type repo: str
    """
    self.connection = connection
    self.repo = repo
    self.last_commit_sha = None
    self.updated_time = None

  def extract_last_sha(self):
    """
    Fetches the SHA of the latest commit from a GitHub repository.

    This function sends a request to GitHub's API to retrieve the list of commits for the specified repository and
    extracts the SHA of the latest commit. If the request is unsuccessful, it logs an error and stops the pipeline.

    :raises SystemExit: If the GitHub API request fails, the function logs an error and exits the program.
    """
    url = f"https://api.github.com/repos/{self.repo}/commits"
    response = request_get(url)
    if response.status_code != 200:
      error(f"Unable to find repository commits. Stopping pipeline.")
      info("Finished.")
      exit(1)

    commits = response.json()
    self.last_commit_sha = commits[0]["sha"]

    info(f"Fetch last commit SHA: \"{self.last_commit_sha}\" from: \"{self.repo}\".")

  def persist_updated_details(self):
    """
    Updates the details of a project in the database, including the latest version and the timestamp of the last update.

    This function performs an UPDATE operation on the `projects` table, setting the `latest_version_long` and
    `last_updated_utc` fields based on the provided parameters. The project name is extracted from the `repo` parameter
    (in the form 'owner/repository').

    :return: The number of rows affected by the update (ex. the number of records modified).
    :rtype: int
    """
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
