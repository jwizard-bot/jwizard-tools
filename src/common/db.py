#  Copyright (c) 2025 by JWizard
#  Originally developed by Miłosz Gilga <https://miloszgilga.pl>

from typing import Any
from urllib import parse as url_parse

from sqlalchemy import create_engine


class Db:
  """
  A class to handle connections and interactions with a MySQL database.
  """

  def __init__(self, secrets: Any):
    """
    Initializes a new instance of the Db class, establishing a database connection.

    :param secrets: The secrets dictionary for secrets from Vault KV storage
    :type secrets: Any
    """
    host = secrets["V_MYSQL_HOST"]
    username = secrets["V_MYSQL_USERNAME"]
    password = secrets["V_MYSQL_PASSWORD"]
    db_name = secrets["V_MYSQL_DB_NAME"]

    encoded_password = url_parse.quote(password)
    url = f"mysql+pymysql://{username}:{encoded_password}@{host}/{db_name}"
    self.engine = create_engine(url, pool_pre_ping=True)
