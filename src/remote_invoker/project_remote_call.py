from abc import ABC, abstractmethod
from logging import info
from math import ceil
from os import getenv

from .process_manager import ProcessManager, ProcessDefinition
from .ssh_scp_client import SshScpClient
from ..common.vault import VaultClient


def _get_output_path_prefix() -> str:
  env_name = "JWIZARD_SSH_OUTPUT_PATH_PREFIX"
  output_path_prefix = getenv(env_name)
  if not output_path_prefix:
    raise Exception(f"{env_name} is not defined")
  return output_path_prefix


class ProjectRemoteCall(ABC):
  def __init__(self, input_path: str, output_path_suffix: str):
    self.input_path = input_path
    self.output_path_suffix = output_path_suffix
    self.output_path = f"{_get_output_path_prefix()}-{output_path_suffix}"
    self.ssh_scp_client = SshScpClient()
    self.process_manager = ProcessManager(root_cwd=self.output_path,
                                          ssh_scp_client=self.ssh_scp_client)
    self.vault_client = VaultClient()

  def perform_call(self):
    process_name = f"jwizard-{self.output_path_suffix}"
    info(f"Staring remote call on \"{process_name}\".")

    # create config file, if config is defined
    config_file_content = getenv("JWIZARD_APP_CONFIG_FILE_CONTENT")
    if config_file_content:
      with open(f"{self.input_path}/.env", "w") as env_file:
        env_file.write(config_file_content.strip())
        info(f"[LOCAL] Created config file.")

    processes = self._define_processes(process_name)
    info(f"Defined: {len(processes)} processes: \"{processes}\".")

    # create local archive
    archive_name = self.ssh_scp_client.archive_directory(self.input_path)

    for process in processes:
      name = process.process_name
      # kill
      info(f"[REMOTE] Killing process: \"{name}\"...")
      process_killed = self.process_manager.kill_process(name)
      if process_killed:
        info(f"[REMOTE] Process: \"{name}\" killed.")
      else:
        info(f"[REMOTE] Process: \"{name}\" was not killed.")

    # clean previous files and move files to remote server
    self.ssh_scp_client.move_archive_to_remote(archive_name, self.output_path)

    for process in processes:
      name = process.process_name
      # start
      info(f"[REMOTE] (Re)starting process: \"{name}\"...")
      is_restarted = self.process_manager.spawn_or_restart_process(process)
      info(f"[REMOTE] Process: \"{name}\" {"re" if is_restarted else ""}started.")

  def revoke_access(self):
    self.vault_client.revoke_access()

  # return empty lists, when you can only move files to remote (without (re)start process)
  @abstractmethod
  def _define_processes(self, process_name: str) -> list[ProcessDefinition]:
    raise Exception("Method \"_run_process\" not implemented.")


class CoreProjectRemoteCall(ProjectRemoteCall):
  def __init__(self, input_path: str):
    super().__init__(input_path, output_path_suffix="core")
    self.instances = self.vault_client.get_secrets_list(kv_backend="jwizard", path="core-instance")

  def _define_processes(self, process_name: str) -> list[ProcessDefinition]:
    processes: list[ProcessDefinition] = []
    for (instance_id, values) in self.instances.items():
      server_port = values["V_SERVER_PORT"]
      java_xms = values["V_JAVA_XMS"]
      java_xmx = values["V_JAVA_XMX"]

      shards_per_process = int(values["V_SHARDS_PER_PROCESS"])
      shards_overall_max = int(values["V_SHARD_OVERALL_MAX"])
      # get total processes as shards per process and shard overall max (per instance)
      total_processes = int(ceil(shards_overall_max / shards_per_process))

      shard_number = 0
      for clusterId in range(total_processes):
        end_shard_number = min(shards_overall_max - 1, shard_number + shards_per_process - 1)
        args = [
          f"-Xms{java_xms} -Xmx{java_xmx}",
          "-Druntime.profiles=prod",
          f"-Dserver.port={server_port}",
          "-Denv.enabled=true",
          f"-Djda.instance.name=core-instance/{instance_id}",
          f"-Djda.sharding.offset.start={shard_number}",
          f"-Djda.sharding.offset.end={end_shard_number}",
          f"-Djda.sharding.total-shards={shards_overall_max}",
          "-jar jwizard-core.jar"
        ]
        processes.append(ProcessDefinition(
          process_name=f"{process_name}-{instance_id}-f{shard_number}t{end_shard_number}",
          args=args,
          script="/usr/bin/java",
          withoutInterpreter=True
        ))
        shard_number += shards_per_process
    return processes


class ApiProjectRemoteCall(ProjectRemoteCall):
  def __init__(self, input_path: str):
    super().__init__(input_path, output_path_suffix="api")
    self.secrets = self.vault_client.get_secrets(kv_backend="jwizard", path="api")

  def _define_processes(self, process_name: str) -> list[ProcessDefinition]:
    server_port = self.secrets["V_SERVER_PORT"]
    java_xms = self.secrets["V_JAVA_XMS"]
    java_xmx = self.secrets["V_JAVA_XMX"]
    args = [
      f"-Xms{java_xms} -Xmx{java_xmx}",
      "-Druntime.profiles=prod",
      f"-Dserver.port={server_port}",
      "-Denv.enabled=true",
      "-jar jwizard-api.jar"
    ]
    return [
      ProcessDefinition(
        process_name=process_name,
        args=args,
        script="/usr/bin/java",
        withoutInterpreter=True
      )
    ]


class LandingPageProjectRemoteCall(ProjectRemoteCall):
  def __init__(self, input_path: str):
    super().__init__(input_path, output_path_suffix="landing-page")
    self.secrets = self.vault_client.get_secrets(kv_backend="jwizard", path="landing-page")

  def _define_processes(self, process_name: str) -> list[ProcessDefinition]:
    server_port = self.secrets["V_SERVER_PORT"]
    env = {
      "HOSTNAME": "localhost",
      "PORT": int(server_port),
      "NEXT_SHARP_PATH": "node_modules/sharp",
    }
    return [
      ProcessDefinition(
        process_name=process_name,
        script="server.js",
        env=env
      )
    ]


class DashboardPageProjectRemoteCall(ProjectRemoteCall):
  def __init__(self, input_path: str):
    super().__init__(input_path, output_path_suffix="dashboard-page")

  # do not start or stop process, only move files to remote location

  def _define_processes(self, process_name: str) -> list[ProcessDefinition]:
    return []
