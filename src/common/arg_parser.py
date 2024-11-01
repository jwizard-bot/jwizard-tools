#
# Copyright (c) 2024 by JWizard
# Originally developed by Miłosz Gilga <https://miloszgilga.pl>
#
import argparse

class ArgParser:
  """
  A class for parsing command-line arguments for a Vault client.

  This class uses the argparse module to define and parse command-line arguments that are required for connecting to a
  Vault service. It provides default values for some of the parameters and allows for the addition of custom arguments.

  :param parser (argparse.ArgumentParser): An instance of ArgumentParser to handle command-line arguments.
  """

  def __init__(self):
    """
    Initializes the ArgParser instance and sets up the default arguments.

    Calls the method `with_default_arguments` to define the standard arguments needed for the Vault client.
    """
    self.parser = argparse.ArgumentParser()
    self.with_default_arguments()

  def with_default_arguments(self):
    """
    Defines default command-line arguments for the Vault client.
    """
    self.parser.add_argument("--vault-address", type=str, required=False, default="http://localhost:8761")
    self.parser.add_argument("--vault-token", type=str, required=False)
    self.parser.add_argument("--vault-username", type=str, required=False)
    self.parser.add_argument("--vault-password", type=str, required=False)
  
  def add_argument(self, key, type, required, default=None):
    """
    Adds a custom argument to the parser.
    """
    self.parser.add_argument(key, type, required, default)

  def get_args(self):
    """
    Parses the command-line arguments.

    :return Namespace: An object containing the parsed arguments as attributes.
    """
    return self.parser.parse_args()
