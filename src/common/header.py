#  Copyright (c) 2025 by JWizard
#  Originally developed by Miłosz Gilga <https://miloszgilga.pl>

from os import path

from pyfiglet import figlet_format
from rich.console import Console
from rich.panel import Panel

title = "JWizard Tools"

panel_text = """Source code repository: https://github.com/jwizard-bot/jwizard-tools
Originally developed by: Miłosz Gilga (https://miloszgilga.pl)
Application license you will find in the LICENSE file"""


def print_header(initiator: str):
  """
  Prints a styled header for the application.

  This function uses ASCII art to display the title of the application and the name of the file that initiated the call.
  It also displays a panel with information about the source code repository and the author.

  :param initiator: The name of the file that initiates this function.
  :type initiator: str
  """
  fancy_header = figlet_format(title, font="slant")
  print(fancy_header, end="")
  print(f"Initiator: {path.basename(initiator)}. Launching...")

  console = Console()
  panel = Panel(panel_text, safe_box=True, expand=False)
  console.print(panel)
