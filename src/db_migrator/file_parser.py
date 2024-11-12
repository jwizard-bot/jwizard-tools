"""
Copyright (c) 2024 by JWizard
Originally developed by Miłosz Gilga <https://miloszgilga.pl>
"""
from glob import glob
from hashlib import md5
from logging import info, warning
from os import path
from re import match, sub as re_sub
from typing import Any
from yaml import safe_load as yaml_load

class FileParser:
  def __init__(self, base_directory):
    """
    Initializes the FileParser with the specified base directory for migration files.

    :param base_directory: The directory where migration files are located.
    :type base_directory: str
    """
    self.base_directory = base_directory
    self.raw_file_content = ""
    self.author_section_name = "author"
    self.sql_section_name = "sql"
    self.rollback_section_name = "rollback"

  def take_migration_files(self) -> list[str]:
    """
    Retrieves and filters migration files from the base directory based on a naming pattern.

    :return: A sorted list of valid migration file paths.
    :rtype: list[str]
    """
    pattern = r"\d{2}-\d{2}-\d{4}_\d{5}_.+\.yml"
    migration_files = glob(path.join(self.base_directory, f"*.yml"))
    filtered_files = [file for file in migration_files if match(pattern, path.basename(file))]
    
    info(f"Found: {len(filtered_files)} migration files in: \"{self.base_directory}\" migration scripts directory.")
    return sorted(filtered_files)

  def read_file_content(self, migration_file: str) -> tuple[str, str, str] | None:
    """
    Reads the content of a migration file and checks for the required structure.

    :param migration_file: The path to the migration file.
    :type migration_file: str

    :return: A tuple containing author, SQL, and rollback sections if they exist and are non-empty, otherwise None.
    :rtype: tuple[str, str, str] | None
    """
    filename = path.basename(migration_file)
    with open(migration_file, 'r') as file:
      migration_yml = file.read()

    if not migration_yml:
      warning(f"File: \"{filename}\" is empty. Skipping migration.")
      return None

    migration_content = yaml_load(migration_yml)

    no_author_field = self.__check_if_field_not_exist(self.author_section_name, migration_content)
    no_sql_field = self.__check_if_field_not_exist(self.sql_section_name, migration_content)
    no_rollback_field = self.__check_if_field_not_exist(self.rollback_section_name, migration_content)

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
    return (author, sql, rollback)

  def __check_if_field_not_exist(self, field_name: str, migration_content: Any):
    """
    Checks if a specific field exists in the migration content.

    :param field_name: The name of the field to check for.
    :type field_name: str
    :param migration_content: The migration content loaded from YAML.
    :type migration_content: Any

    :return: True if the field does not exist in the migration content, False otherwise.
    :rtype: bool
    """
    return not field_name in migration_content

  def calculate_file_content_hash(self) -> str:
    """
    Calculates an MD5 hash of the raw content of the migration file.

    :return: The MD5 hash of the file content.
    :rtype: str
    """
    hash_obj = md5()
    hash_obj.update(self.raw_file_content.encode('utf-8'))
    return hash_obj.hexdigest()

  def extract_subqueries(self, query: str) -> list[str]:
    """
    Splits a SQL query into individual subqueries and cleans up whitespace.

    :param query: The SQL query to split.
    :type query: str

    :return: A list of cleaned subqueries.
    :rtype: list[str]
    """
    queries = query.split(";")
    cleaned_queries = [re_sub(r"\s+", " ", query) for query in queries]
    stripped_queries = [query for query in cleaned_queries if query.strip()]
    return stripped_queries
