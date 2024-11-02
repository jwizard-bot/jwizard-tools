"""
Copyright (c) 2024 by JWizard
Originally developed by Miłosz Gilga <https://miloszgilga.pl>
"""
from hvac import Client
from logging import info, error

class VaultClient:
  """
  A client for interacting with HashiCorp Vault to retrieve secrets from key-value (KV) storage.

  :param args: Dictionary containing the Vault connection parameters.
    Expected keys:
      - vault_address (str): The Vault server's address.
      - vault_token (str, optional): The Vault token for authentication.
      - vault_username (str, optional): The Vault username for userpass authentication.
      - vault_password (str, optional): The Vault password for userpass authentication.
  """

  def __init__(self, args: dict):
    """
    Initializes the Vault client, attempting authentication with the provided arguments.
    Tries token-based authentication first if a token is provided, else falls back to username-password authentication.

    :param args: A dictionary with required and optional authentication details.
    :raises SystemExit: If connection or authentication to Vault server fails.
    """
    try:
      if args.vault_token != None:
        self.client = Client(url=args.vault_address, token=args.vault_token)
        self.client.secrets.kv.default_kv_version = 1
      else:
        self.client = Client(url=args.vault_address)
        self.client.auth_userpass(args.vault_username, args.vault_password)
    
      info(f"Authenticated to Vault server.")
    except Exception as e:
      error(f"Unable authenticate to Vault server. Cause: {e}.")
      info("Finished.")
      exit(1)

  def get_secrets(self, kv_backend: str, path: str):
    """
    Retrieves secrets from a specified key-value backend in Vault.

    :param kv_backend: The mount point of the KV backend where secrets are stored.
    :type kv_backend: str

    :param path: The path within the KV backend to the desired secret.
    :type path: str

    :return: A dictionary containing the secret data if retrieval is successful, or None if not.
    :rtype: Optional[Dict[str, str]]
    :raises Exception: If the KV storage path is invalid or inaccessible.
    """
    try:
      response = self.client.secrets.kv.read_secret(mount_point=kv_backend, path=path)
      return response["data"]
    except Exception as e:
      error(f"Unable to find KV storage: \"{path}\". Cause: {e}.")
