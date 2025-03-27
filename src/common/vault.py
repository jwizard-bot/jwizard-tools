from logging import info, error
from os import getenv

from hvac import Client
from hvac.adapters import JSONAdapter


class JsonProxyAdapter(JSONAdapter):
  def request(self, method, url, headers=None, raise_exception=True, **kwargs):
    if headers is None:
      headers = {}
    proxy_verification_token = getenv("JWIZARD_PROXY_VERIFICATION_TOKEN")
    if proxy_verification_token:
      headers["X-Proxy-Verification-Token"] = proxy_verification_token
    return super().request(method, url, headers, raise_exception, **kwargs)


class VaultClient:
  def __init__(self):
    self.token = getenv("ENV_VAULT_TOKEN")
    address = getenv("JWIZARD_VAULT_SERVER", "http://localhost:8761")
    try:
      if self.token is not None:
        self.client = Client(url=address, token=self.token)
      else:
        self.client = Client(url=address, adapter=JsonProxyAdapter)
        self.client.auth.userpass.login(
          username=getenv("JWIZARD_VAULT_USERNAME"),
          password=getenv("JWIZARD_VAULT_PASSWORD"),
        )
      self.client.secrets.kv.default_kv_version = 1
      info(f"Authenticated to Vault server.")
    except Exception as e:
      error(f"Unable authenticate to Vault server. Cause: {e}.")
      exit(1)

  def get_secrets(self, kv_backend: str, path: str):
    try:
      response = self.client.secrets.kv.read_secret(mount_point=kv_backend, path=path)
      return response["data"]
    except Exception as e:
      error(f"Unable to find KV storage: \"{path}\". Cause: {e}.")
      exit(1)

  def get_secrets_list(self, kv_backend: str, path: str):
    try:
      response = self.client.secrets.kv.list_secrets(mount_point=kv_backend, path=path)
      keys = response["data"]["keys"]
      secrets_dict = {}
      for key in keys:
        full_path = f"{path}/{key}"
        secrets_for_key = self.client.secrets.kv.read_secret(mount_point=kv_backend, path=full_path)
        secrets_dict[key] = secrets_for_key["data"]
      return secrets_dict
    except Exception as e:
      error(f"Unable to find KV storage elements: \"{path}\". Cause: {e}.")
      exit(1)

  def revoke_access(self):
    if self.token is not None:
      self.client.auth.token.revoke_self()
      info(f"Revoked Vault server token.")
