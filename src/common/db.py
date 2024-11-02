"""
Copyright (c) 2024 by JWizard
Originally developed by Miłosz Gilga <https://miloszgilga.pl>
"""
from urllib import parse as url_parse
from sqlalchemy import create_engine

class Db:
  """
  A class to handle connections and interactions with a MySQL database.
  """

  def __init__(self, host: str, username: str, password: str, db_name: str):
    """
    Initializes a new instance of the Db class, establishing a database connection.

    :param host: The database host, ex. 'localhost' or the server's IP address.
    :type host: str

    :param username: The database username.
    :type username: str

    :param password: The password for the database user.
    :type password: str

    :param db_name: The name of the database to connect to.
    :type db_name: str
    """
    encoded_password = url_parse.quote(password)
    url = f"mysql+pymysql://{username}:{encoded_password}@{host}/{db_name}"
    self.engine = create_engine(url)
