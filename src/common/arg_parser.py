"""
Copyright (c) 2024 by JWizard
Originally developed by Miłosz Gilga <https://miloszgilga.pl>
"""
from argparse import ArgumentParser
from typing import Type, Any

class ArgParser:
  """
  A class for parsing command-line arguments for a Vault client.

  This class uses the argparse module to define and parse command-line arguments required for connecting to a
  Vault service. It includes default arguments specific to Vault configuration, but additional arguments can be
  added as needed.
  """

  def __init__(self):
    """
    Initializes the ArgParser instance and sets up the default arguments.

    Calls the method `with_default_arguments` to define the standard arguments needed for the Vault client.
    """
    self.parser = ArgumentParser()
    self.with_default_arguments()

  def with_default_arguments(self):
    """
    Defines default command-line arguments for the Vault client.

    Adds arguments for Vault address, token, username, and password with some default values and optional requirement
    settings.
    """
    self.parser.add_argument("--vault-address", type=str, required=False, default="http://localhost:8761")
    self.parser.add_argument("--vault-token", type=str, required=False)
    self.parser.add_argument("--vault-username", type=str, required=False)
    self.parser.add_argument("--vault-password", type=str, required=False)
  
  def add_argument(self, name: str, type: Type[Any], required: bool, default=None):
    """
    Adds a custom argument to the parser.

    :param name: The name of the argument.
    :type name: str

    :param type: The expected data type for the argument value.
    :type type: Type[Any]

    :param required: Specifies if the argument is required.
    :type required: bool

    :param default: The default value for the argument, if any.
    :type default: Any, optional
    """
    self.parser.add_argument(name, type=type, required=required, default=default)

  def get_args(self):
    """
    Parses the command-line arguments.

    :return: An argparse.Namespace object containing the parsed arguments as attributes.
    :rtype: argparse.Namespace
    """
    return self.parser.parse_args()
