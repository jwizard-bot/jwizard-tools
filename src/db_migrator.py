#
# Copyright (c) 2024 by JWizard
# Originally developed by Miłosz Gilga <https://miloszgilga.pl>
#
from common.vault import VaultClient
from common.arg_parser import ArgParser

if __name__ == '__main__':
  arg_parser = ArgParser()
  args = arg_parser.get_args()

  vault_client = VaultClient(args)
  secrets = vault_client.get_secrets(kv_backend="jwizard", path="common")