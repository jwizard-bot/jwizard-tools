from io import StringIO
from logging import error, info
from os import getenv, walk, path, makedirs
from re import match as regex_match
from shutil import rmtree
from tarfile import open as tar_open
from textwrap import fill as text_fill
from time import time
from uuid import uuid4

from paramiko import RSAKey, SSHClient, AutoAddPolicy
from scp import SCPClient


class SshScpClient:
  def __init__(self):
    self.host = getenv("JWIZARD_SSH_HOST")
    self.port = getenv("JWIZARD_SSH_PORT")
    self.username = getenv("JWIZARD_SSH_USERNAME")
    self.key = getenv("JWIZARD_SSH_KEY")
    self.passphrase = getenv("JWIZARD_SSH_PASSPHRASE")
    self.private_key = self._extract_and_format_private_key()
    self.client = SSHClient()
    self.client.set_missing_host_key_policy(AutoAddPolicy())
    self.temp_dir = ".temp"

  def perform_command(self, command: str) -> str:
    out = ""
    try:
      self.client.connect(self.host, int(self.port), self.username, pkey=self.private_key)
      stdin, stdout, stderr = self.client.exec_command(command)

      out = stdout.read().decode()
      error_out = stderr.read().decode()
      if error_out:
        error(f"Remote command execution error: \"{error_out}\".")
        raise Exception(error)
    except Exception as e:
      raise e
    finally:
      self.client.close()
      return out

  def _move_file_to_remote(self, file_path: str, remote_path: str):
    try:
      self.client.connect(self.host, int(self.port), self.username, pkey=self.private_key)
      with SCPClient(self.client.get_transport()) as scp:
        scp.put(file_path, remote_path)
        info(f"[LOCAL] File: \"{file_path}\" was copied into remote path.")
    except Exception as e:
      raise e
    finally:
      self.client.close()

  def archive_directory(self, input_dir_path: str) -> str:
    archive_name = f"{uuid4()}.tar.gz"

    rmtree(self.temp_dir, ignore_errors=True)
    makedirs(self.temp_dir)

    files_list = []
    for root, _, files in walk(input_dir_path):
      for file in files:
        files_list.append(path.join(root, file))
    total_files = len(files_list)

    count_of_files = 0
    last_progress = 0
    progress_percentage_step = 10
    start_time = time()

    info(f"[LOCAL] Start packing content...")
    info(f"[LOCAL] Packing progress: 0%")

    # move all files from directory to tar.gz archive
    with tar_open(f"{self.temp_dir}/{archive_name}", "w:gz") as archive:
      for file_path in files_list:
        count_of_files += 1
        archive.add(file_path, arcname=path.relpath(file_path, input_dir_path))

        progress = (count_of_files / total_files) * 100
        if progress - last_progress >= progress_percentage_step:
          last_progress = progress // progress_percentage_step * progress_percentage_step
          info(f"[LOCAL] Packing progress: {int(last_progress)}%")

    elapsed_time = time() - start_time

    info(f"[LOCAL] Pack content from: \"{input_dir_path}\" to \"{archive_name}\" archive "
         f"with {count_of_files} files (completed in {elapsed_time:.2f} seconds).")

    return archive_name

  def move_archive_to_remote(self, archive_name: str, output_remote_path: str):
    # create remote directories structure
    self.perform_command(f"mkdir -p {output_remote_path}")
    info("[REMOTE] Create remote directory structure.")

    # remove previous files
    self.perform_command(f"rm -rf {output_remote_path}/*")
    info("[REMOTE] Remove previous files in remote directory.")

    # move archive into remote server
    info(f"[LOCAL] Start moving files on remote...")
    self._move_file_to_remote(f"{self.temp_dir}/{archive_name}",
                              f"{output_remote_path}/{archive_name}")

    # remove archive in local temp directory
    rmtree(self.temp_dir)
    info(f"[LOCAL] Remove \"{self.temp_dir}\" from local directory.")

    # extract archive on remote server
    self.perform_command(f"tar -xvzf {output_remote_path}/{archive_name} -C {output_remote_path}")
    info(f"[REMOTE] Extracted moved archive: \"{archive_name}\" on remote.")

    # remove extracted archive on remote server
    self.perform_command(f"rm -f {output_remote_path}/{archive_name}")
    info(f"[REMOTE] Delete archive: \"{archive_name}\" on remote.")

  def _extract_and_format_private_key(self) -> RSAKey:
    # extract type of private key
    match = regex_match(r"-----BEGIN (\w+) PRIVATE KEY-----", self.key)
    if not match:
      raise Exception("Unable to find private key file type.")

    key_type = match.group(1).upper()
    key_header = f"-----BEGIN {key_type} PRIVATE KEY-----"
    key_footer = f"-----END {key_type} PRIVATE KEY-----"

    private_key_str = self.key
    private_key_str = private_key_str.replace(key_header, f"{key_header}\n")
    private_key_str = private_key_str.replace(key_footer, f"\n{key_footer}")

    lines = private_key_str.split("\n")
    if len(lines) == 3:
      key_body = text_fill(lines[1], 64)
      private_key_str = f"{lines[0]}\n{key_body}\n{lines[2]}"

    virtual_key_file = StringIO(private_key_str)
    return RSAKey.from_private_key(file_obj=virtual_key_file, password=self.passphrase)
