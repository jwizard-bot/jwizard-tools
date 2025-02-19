from logging import info, error
from os import walk, path
from typing import Dict, List

from sqlalchemy import Connection, text


class FileStats:
  def __init__(self):
    self.files_count = 0
    self.lines_count = 0

  def add_file(self, line_count):
    self.files_count += 1
    self.lines_count += line_count

  def as_tuple(self):
    return self.files_count, self.lines_count

  def __repr__(self):
    return f"(files: {self.files_count}, lines: {self.lines_count})"


# extracting all file properties (based FileStats class and file extension)
# and persisting into database
class CodeLinesAnalyzer:
  def __init__(self, connection: Connection, repo: str, root_dir: str):
    self.connection = connection
    self.repo = repo
    self.root_dir = root_dir
    self.stats: Dict[str, FileStats] = {}
    self.unknown_name = "others"
    # extensions ignored by analyzer script
    self.ignorable_extensions = {
      ".lock",
      ".ttf",
      ".png",
      ".jpg",
      ".svg",
      ".jpeg",
      ".mp3",
      ".gif",
      ".ico",
      ".jar",
      ".editorconfig",
      ".env",
      ".gitignore",
      ".md",
      ".iml",
    }

  def _extract_ext_with_stats(self):
    all_files = 0
    for root, _, files in walk(self.root_dir):
      for file in files:
        file_path = path.join(root, file)
        _, extension = path.splitext(file)

        all_files += 1
        # set unknown key for unknown extensions, but handle unix style hidden files
        # (files starts with dot)
        if not extension:
          if file.startswith("."):
            extension = file
          else:
            extension = self.unknown_name

        if extension.lower() in self.ignorable_extensions:
          continue

        if extension not in self.stats:
          self.stats[extension] = FileStats()
        try:
          with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            line_count = sum(1 for _ in f)
          self.stats[extension].add_file(line_count)
        except Exception as e:
          error(f"Unable to process file: \"{file_path}\". Cause: \"{e}\".")

    all_processed_files = sum(stats.files_count for stats in self.stats.values())
    info(f"Successfully processed: {all_processed_files} files. "
         f"Skipped: {all_files - all_processed_files} files. Fully report below.")

    sorted_files = list(self.stats.items())
    sorted_files = sorted(sorted_files, reverse=True,
                          key=lambda fs: (fs[1].files_count + fs[1].lines_count))  # sort by sum

    result_table = [f"[{"": <20} {"files": <12} {"lines": <12}]"]
    for ext, file_info in sorted_files:
      result_table.append(f"[{ext: <20} {file_info.files_count: <12} {file_info.lines_count: <12}]")

    for row in result_table:
      info(row)

  def _persist_stats_in_db(self) -> [int, int, int]:
    # fetch repository id or terminate if repository with this id not exists
    query = text("SELECT id FROM projects WHERE name = :project_name")
    project_name = self.repo.split("/")[1]
    result = self.connection.execute(query, parameters={
      "project_name": project_name,
    })
    project_id = result.scalar()
    if not project_id:
      raise Exception(f"Unable to find persisted project: \"{project_name}\".")

    project_id = int(project_id)

    # fetch previous saved extensions for project
    query = text(f"""
      SELECT extension, id FROM project_analyzer_results WHERE project_id = :project_id
    """)
    result = self.connection.execute(query, parameters={
      "project_id": project_id,
    })
    persisted_ext_with_id = {
      (ext if ext is not None else self.unknown_name): int(id_)
      for ext, id_ in result.fetchall()
    }

    founded_ext = set(self.stats.keys())
    persisted_ext = set(persisted_ext_with_id.keys())

    to_persist_ext = list(founded_ext - persisted_ext)
    to_drop_ext = list(persisted_ext - founded_ext)
    to_update_ext = list(founded_ext & persisted_ext)

    info(f"To persist: {to_persist_ext}.")
    info(f"To drop: {to_drop_ext}.")
    info(f"To update: {to_update_ext}.")

    to_persist = self._filter_base_dictionary(to_persist_ext)
    to_update = self._filter_base_dictionary(to_update_ext)

    persisted = 0
    dropped = 0
    updated = 0

    # persist newest extension file reports
    if to_persist:
      values = ",".join(
        f"({'NULL' if ext == self.unknown_name else f"'{ext}'"},{files},{lines},{project_id})"
        for ext, file_info in to_persist.items()
        for files, lines in [file_info.as_tuple()]
      )
      query = text(f"""
        INSERT INTO project_analyzer_results (extension, files_count, lines_count, project_id)
        VALUES {values}
      """)
      result = self.connection.execute(query)
      persisted = result.rowcount

    # drop previous extension file reports
    if to_drop_ext:
      query = text(f"""
        DELETE FROM project_analyzer_results
        WHERE project_id = :project_id AND extension IN :extensions
      """)
      result = self.connection.execute(query, parameters={
        "project_id": project_id,
        "extensions": tuple(to_drop_ext),
      })
      dropped = result.rowcount

    # update already existing extensions
    if to_update:
      values = []
      for ext, file_info in to_update.items():
        files, lines = file_info.as_tuple()
        ext_value = "NULL" if ext == self.unknown_name else f"'{ext}'"
        values.append(f"({persisted_ext_with_id[ext]},{ext_value},{files},{lines},{project_id})")
      values = ",".join(values)

      # use bulk update statement (updating only files_count and lines_count columns)
      query = text(f"""
        INSERT INTO project_analyzer_results (id, extension, files_count, lines_count, project_id)
        VALUES {values}
        ON DUPLICATE KEY UPDATE
          files_count = VALUES(files_count),
          lines_count = VALUES(lines_count);
      """)
      result = self.connection.execute(query)
      updated = result.rowcount

    return persisted, dropped, updated

  def _filter_base_dictionary(self, available_keys: List[str]):
    return dict(filter(lambda item: item[0] in available_keys, self.stats.items()))

  def analyze_and_persist(self) -> [int, int, int]:
    self._extract_ext_with_stats()
    return self._persist_stats_in_db()
