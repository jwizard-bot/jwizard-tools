from logging import info, error
from os import getenv

from hvac import Client


class VaultClient:
  def __init__(self):
    token = getenv("ENV_VAULT_TOKEN")
    address = getenv("JWIZARD_VAULT_SERVER", "http://localhost:8761")
    try:
      if token is not None:
        self.client = Client(url=address, token=token)
      else:
        self.client = Client(url=address)
        self.client.auth.userpass.login(
          username=getenv("JWIZARD_VAULT_USERNAME"),
          password=getenv("JWIZARD_VAULT_PASSWORD"),
        )
      self.client.secrets.kv.default_kv_version = 1
      info(f"Authenticated to Vault server.")
    except Exception as e:
      error(f"Unable authenticate to Vault server. Cause: {e}.")
      info("Finished.")
      exit(1)

  def get_secrets(self, kv_backend: str, path: str):
    try:
      response = self.client.secrets.kv.read_secret(mount_point=kv_backend, path=path)
      return response["data"]
    except Exception as e:
      error(f"Unable to find KV storage: \"{path}\". Cause: {e}.")
