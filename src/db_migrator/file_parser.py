from glob import glob
from hashlib import md5
from logging import info, warning
from os import path
from re import match, sub as re_sub
from typing import Any

from yaml import safe_load as yaml_load


def check_if_field_not_exist(field_name: str, migration_content: Any):
  return not field_name in migration_content


def extract_subqueries(query: str) -> list[str]:
  queries = query.split(";")
  cleaned_queries = [re_sub(r"\s+", " ", query) for query in queries]
  stripped_queries = [query for query in cleaned_queries if query.strip()]
  return stripped_queries


def lambda_file_sort_key(file_name: str, pattern: str) -> [int, int, int, int]:
  match_str = match(pattern, file_name)
  if match_str:
    year, month, day, incrementer = match_str.groups()
    return int(year), int(month), int(day), int(incrementer)
  return 0, 0, 0, 0  # we assume, that string is match (filtered_files variable)


class FileParser:
  def __init__(self, base_directory):
    self.base_directory = base_directory
    self.raw_file_content = ""
    self.author_section_name = "author"
    self.sql_section_name = "sql"
    self.rollback_section_name = "rollback"

  def take_migration_files(self) -> list[str]:
    pattern = r"\d{4}-\d{2}-\d{2}_\d{5}_.+\.yml"  # YYYY-MM-dd_XXXXX_[description].yml
    migration_files = glob(path.join(self.base_directory, f"*.yml"))
    filtered_files = [file for file in migration_files if match(pattern, path.basename(file))]

    info(f"Found: {len(filtered_files)} migration "
         f"files in: \"{self.base_directory}\" migration scripts directory.")
    return sorted(filtered_files, key=lambda file_name: lambda_file_sort_key(file_name, pattern))

  def read_file_content(self, migration_file: str) -> tuple[str, str, str] | None:
    filename = path.basename(migration_file)
    with open(migration_file, "r") as file:
      migration_yml = file.read()

    if not migration_yml:
      warning(f"File: \"{filename}\" is empty. Skipping migration.")
      return None

    migration_content = yaml_load(migration_yml)

    no_author_field = check_if_field_not_exist(self.author_section_name, migration_content)
    no_sql_field = check_if_field_not_exist(self.sql_section_name, migration_content)
    no_rollback_field = check_if_field_not_exist(self.rollback_section_name, migration_content)

    if no_author_field or no_sql_field or no_rollback_field:
      warning(f"File: \"{filename}\" has inappropriate structure.")
      return None

    author = migration_content[self.author_section_name]
    sql = migration_content[self.sql_section_name]
    rollback = migration_content[self.rollback_section_name]

    if not author or not sql or not rollback:
      warning(f"File: \"{filename}\" is empty. Skipping migration.")
      return None

    self.raw_file_content = migration_yml
    return author, sql, rollback

  def calculate_file_content_hash(self) -> str:
    hash_obj = md5()
    hash_obj.update(self.raw_file_content.encode("utf-8"))
    return hash_obj.hexdigest()
