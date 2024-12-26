"""
Copyright (c) 2024 by JWizard
Originally developed by Miłosz Gilga <https://miloszgilga.pl>
"""
from datetime import datetime, timezone
from logging import info, warning
from os import path, sep
from sqlalchemy import Connection, text
from db_migrator.file_parser import FileParser

class Migrator:
  def __init__(self, connection: Connection, file_parser: FileParser, table_name: str):
    """
    Initializes the Migrator class with a database connection, a file parser, and the migration table name.

    :param connection: SQLAlchemy database connection used for executing queries.
    :type connection: Connection

    :param file_parser: A FileParser instance responsible for reading and parsing migration files.
    :type file_parser: FileParser

    :param table_name: The name of the database table for storing applied migrations metadata.
    :type table_name: str
    """
    self.table_name = table_name
    self.connection = connection
    self.file_parser = file_parser
    self.applied_migrations = {}
    self.revert_migrations = {}
    self.migration_files = self.file_parser.take_migration_files()

  def _check_if_migrations_table_exist(self) -> bool:
    """
    Checks if the migrations tracking table exists in the database.

    :return: True if the migrations table exists, False otherwise.
    :rtype: bool
    """
    query = text("""
      SELECT EXISTS (
        SELECT 1 FROM information_schema.tables
        WHERE table_name = :table_name
      );
    """)
    result = self.connection.execute(query, parameters={
      "table_name": self.table_name
    })
    return result.scalar()

  def _create_migrations_table(self):
    """
    Creates the migrations table if it does not exist, defining columns for tracking migration files.
    """
    query = text(f"""
      CREATE TABLE IF NOT EXISTS `{self.table_name}` (
        id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
        file_name VARCHAR(255) NOT NULL,
        author VARCHAR(255) NOT NULL,
        applied_at DATETIME NOT NULL,
        base_dir VARCHAR(255) NOT NULL,
        file_md5 VARCHAR(32) NOT NULL,
        PRIMARY KEY (id)
      )
      ENGINE=InnoDB;
    """)
    self.connection.execute(query)

  def extract_applied_migrations(self):
    """
    Extracts metadata about applied migrations from the database.

    Checks for the existence of the migrations table, creates it if necessary, and populates `applied_migrations`
    with data from the table.
    """
    table_exist = self._check_if_migrations_table_exist()
    if not table_exist:
      self._create_migrations_table()
      warning(f"Unable to find \"{self.table_name}\" table. Created via SQL statement.")
      return

    info(f"Table \"{self.table_name}\" exists. Retrieving applied migrations.")
    query = text(f"SELECT file_name, file_md5, base_dir FROM `{self.table_name}`")
    result = self.connection.execute(query)

    self.applied_migrations = {f"{row[2]}/{row[0]}": row[1] for row in result.fetchall()}
    info(f"Already executed: {len(self.applied_migrations)} migrations.")

  def _apply_migration(self, sql: str) -> int:
    """
    Applies a migration by executing each SQL query in the given migration content.

    :param sql: The SQL commands to apply, provided as a single string.
    :type sql: str

    :return: The number of individual SQL queries executed.
    :rtype: int
    """
    queries = self.file_parser.extract_subqueries(sql)
    for query in queries:
      self.connection.execute(text(query))
    return len(queries)

  def _update_migrations_table(self, file_name: str, author: str, file_md5: str) -> int:
    """
    Updates the migrations table to track a new migration as applied.

    :param file_name: The name of the migration file.
    :type file_name: str

    :param author: The author of the migration.
    :type author: str

    :param file_md5: The MD5 hash of the migration file content.
    :type file_md5: str

    :return: The number of rows affected by the insert operation.
    :rtype: int
    """
    now = datetime.now(timezone.utc)
    query = text(f"""
      INSERT INTO `{self.table_name}`
      (file_name, author, applied_at, base_dir, file_md5)
      VALUES (:file_name, :author, :applied_at, :base_dir, :file_md5)
    """)
    result = self.connection.execute(query, parameters={
      "file_name": file_name[:255],
      "author": author[:255],
      "applied_at": now,
      "base_dir": self.file_parser.base_directory,
      "file_md5": file_md5,
    })
    return result.rowcount

  def _check_passed_migration_file_md5(self, full_path: str):
    """
    Verifies that the MD5 hash of a migration file matches the hash stored in the database.

    :param full_path: The full path of the migration file being checked.
    :type full_path: str

    :raises Warning: Logs a warning if the MD5 hashes do not match, indicating potential unauthorized changes.
    """
    file_md5 = self.applied_migrations[full_path]
    calculated_md5 = self.file_parser.calculate_file_content_hash()
    if file_md5 != calculated_md5:
      warning(f"Passed migration file has different hash!. Calculated: \"{calculated_md5}\", persisted: \"{file_md5}\"")
      warning(f"Inserting changes in already passed migration files is strictly prohibited.")

  def execute_migrations(self) -> int:
    """
    Executes all unapplied migrations in the migration directory.

    Checks each migration file, applies new migrations, and updates the migrations table.
    Tracks the number of applied migrations.

    :return: The count of successfully applied migrations.
    :rtype: int
    """
    applied_migrations = 0
    for migration_file in self.migration_files:
      full_path = migration_file.replace(sep, "/")
      base_name = path.basename(migration_file)

      details = self.file_parser.read_file_content(migration_file)
      if not details:
        continue

      if full_path in self.applied_migrations:
        self._check_passed_migration_file_md5(full_path)
        continue

      (author, sql, rollback) = details
      self.revert_migrations[base_name] = rollback
      file_md5 = self.file_parser.calculate_file_content_hash()

      queries_count = self._apply_migration(sql)
      applied_migrations += self._update_migrations_table(base_name, author, file_md5)
      info(f"Executed migration: \"{base_name}\" with: {queries_count} single SQL queries.")

    return applied_migrations

  def _drop_migrations_table_row(self, file_name: str) -> int:
    """
    Removes a specific migration entry from the migrations table.

    :param file_name: The name of the migration file to remove from tracking.
    :type file_name: str

    :return: The number of rows affected by the delete operation.
    :rtype: int
    """
    query = text(f"DELETE FROM `{self.table_name}` WHERE file_name = :file_name")
    result = self.connection.execute(query, parameters={
      "file_name": file_name,
    })
    return result.rowcount

  def execute_revert_migrations(self):
    """
    Executes the rollback for all previously applied migrations in reverse order.

    Applies each SQL command in the rollback section, and removes the entry from the migrations table upon success.
    """
    for file_name, drop_sql in self.revert_migrations.items():
      queries = self.file_parser.extract_subqueries(drop_sql)
      for query in queries:
        self.connection.execute(text(query))

      count_rows = self._drop_migrations_table_row(file_name)
      warning(f"Reverted migration: \"{file_name}\" with: {len(queries) + count_rows} single SQL queries.")
