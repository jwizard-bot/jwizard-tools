from datetime import datetime, timezone
from logging import info, warning
from os import path, sep

from sqlalchemy import Connection, text

from .file_parser import FileParser, extract_subqueries


class Migrator:
  def __init__(self, connection: Connection, file_parser: FileParser, table_name: str):
    self.table_name = table_name
    self.connection = connection
    self.file_parser = file_parser
    self.applied_migrations = {}
    self.revert_migrations = {}
    self.migration_files = self.file_parser.take_migration_files()

  def _check_if_migrations_table_exist(self) -> bool:
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
    queries = extract_subqueries(sql)
    for query in queries:
      self.connection.execute(text(query))
    return len(queries)

  def _update_migrations_table(self, file_name: str, author: str, file_md5: str):
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
    file_md5 = self.applied_migrations[full_path]
    calculated_md5 = self.file_parser.calculate_file_content_hash()
    if file_md5 != calculated_md5:
      warning(f"Passed migration file has different hash!. "
              f"Calculated: \"{calculated_md5}\", persisted: \"{file_md5}\"")
      warning(f"Inserting changes in already passed migration files is strictly prohibited.")

  def execute_migrations(self) -> int:
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

  def _drop_migrations_table_row(self, file_name: str):
    query = text(f"DELETE FROM `{self.table_name}` WHERE file_name = :file_name")
    result = self.connection.execute(query, parameters={
      "file_name": file_name,
    })
    return result.rowcount

  def execute_revert_migrations(self):
    for file_name, drop_sql in self.revert_migrations.items():
      queries = extract_subqueries(drop_sql)
      for query in queries:
        self.connection.execute(text(query))

      count_rows = self._drop_migrations_table_row(file_name)
      warning(f"Reverted migration: \"{file_name}\" "
              f"with: {len(queries) + count_rows} single SQL queries.")
