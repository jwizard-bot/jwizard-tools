#
# Copyright (c) 2024 by JWizard
# Originally developed by Miłosz Gilga <https://miloszgilga.pl>
#
import hvac

class VaultClient:
  """
  A client for interacting with a HashiCorp Vault server.

  This class provides methods to authenticate with a Vault server and to retrieve
  secrets from a specified Key-Value (KV) backend.

  Attributes:
    client (hvac.Client): An instance of the hvac.Client used to interact with the Vault server.
  """

  def __init__(self, args):
    """
    Initializes the VaultClient instance. Attempts to authenticate with the Vault server using either a token or
    user/pass credentials.

    Parameters:
      args (Namespace): An object containing the parsed arguments as attributes.

    Raises:
      SystemExit: If the authentication fails, prints an error message and exits the program.
    """
    try:
      if args.vault_token != None:
        self.client = hvac.Client(url=args.vault_address, token=args.vault_token)
        self.client.secrets.kv.default_kv_version = 1
      else:
        self.client = hvac.Client(url=args.vault_address)
        self.client.auth_userpass(args.vault_username, args.vault_password)
    except Exception as e:
      print(f"Unable login to Vault server: \"{args.vault_address}\". Cause: {e}.")
      exit(1)

  def get_secrets(self, kv_backend, path):
    """
    Retrieves secrets from the specified Key-Value (KV) backend.

    Parameters:
      kv_backend (str): The mount point of the KV backend.
      path (str): The path of the secret to retrieve.

    Returns:
      dict: The secret data retrieved from the specified path.

    Raises:
      Exception: If the secret cannot be found, prints an error message.
    """
    try:
      response = self.client.secrets.kv.read_secret(mount_point=kv_backend, path=path)
      return response["data"]
    except Exception as e:
      print(f"Unable to find KV storage: \"{path}\". Cause: {e}.")
