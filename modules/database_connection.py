import sqlite3
from sqlite3 import Error

import os.path
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
db_path = os.path.join(BASE_DIR, "../db/breaches.db")

def create_connection():
	""" create a database connection to the SQLite database
		specified by the db_file
	:param db_file: database file
	:return: Connection object or None
	"""
	try:
		conn = sqlite3.connect(db_path)
		return conn
	except Error as e:
		print(e)

	return None