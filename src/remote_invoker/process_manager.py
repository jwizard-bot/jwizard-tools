from .ssh_scp_client import SshScpClient


class ProcessDefinition:
  def __init__(self,
               process_name: str,
               script: str,
               args: list[str] | None = None,
               env: dict[str, str] | None = None,
               root_dir: str | None = None,
               withoutInterpreter: bool = False):
    self.process_name = process_name
    if not root_dir:
      self.root_dir = self.process_name
    self.args = args
    self.script = script
    self.env = env
    self.withoutInterpreter = withoutInterpreter

  def __repr__(self):
    return self.process_name


class ProcessManager:
  def __init__(self, root_cwd, ssh_scp_client: SshScpClient):
    self.env_command = "source ~/.nvm/nvm.sh"
    self.manager_command = "pm2"
    self.root_cwd = root_cwd
    self.ssh_scp_client = ssh_scp_client

  def _perform_command(self, cmd: str) -> str:
    return self.ssh_scp_client.perform_command(cmd)

  def _check_if_process_exists(self, process_name: str) -> bool:
    check_cmd = (f"{self.env_command} && {self.manager_command} list | "
                 f"grep -q \"{process_name}\" && echo 1 || echo 0")
    return int(self._perform_command(check_cmd)) == 1

  def kill_process(self, process_name: str) -> bool:
    # kill process, only if exists
    process_exists = self._check_if_process_exists(process_name)
    if process_exists:
      kill_cmd = f"{self.env_command} && {self.manager_command} stop {process_name} --silent"
      self._perform_command(kill_cmd)
    return process_exists

  def spawn_or_restart_process(self, process_definition: ProcessDefinition) -> bool:
    name = process_definition.process_name
    process_exists = self._check_if_process_exists(name)
    # restart, if proces already exists
    if process_exists:
      process_cmd = f"{self.env_command} && {self.manager_command} restart {name} --silent"
    else:
      spawn_cmd = [
        f"{self.env_command} &&"
      ]
      if process_definition.env:
        for key, value in process_definition.env.items():
          spawn_cmd.append(f"{key}={value}")
      spawn_cmd.extend([
        f"{self.manager_command} start {process_definition.script}",
        f"--name {process_definition.process_name}",
        "--update-env",
        f"--cwd {self.root_cwd}",
      ])
      if process_definition.withoutInterpreter:
        spawn_cmd.append("--interpreter none")
      spawn_cmd.append("--silent")

      if process_definition.args:
        spawn_cmd.append("--")
        for arg in process_definition.args:
          spawn_cmd.append(arg)
      process_cmd = " ".join(spawn_cmd)

    self._perform_command(process_cmd)
    self._perform_command(f"{self.env_command} && {self.manager_command} save")  # dump process
    return process_exists
