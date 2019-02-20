import sqlite3
from sqlite3 import Error

import json

import sys
import io
#sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="UTF-8")


import os.path
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
db_path = os.path.join(BASE_DIR, "../db/breaches.db")


def create_connection(db_file):
	""" create a database connection to the SQLite database
		specified by the db_file
	:param db_file: database file
	:return: Connection object or None
	"""
	try:
		conn = sqlite3.connect(db_file)
		return conn
	except Error as e:
		print(e)

	return None


def init_breaches():

	# create a database connection
	conn = create_connection(db_path)
	with conn:

		cur = conn.cursor()

		breaches_table_def = """ CREATE TABLE IF NOT EXISTS breaches(
										Name varchar PRIMARY KEY,
										Title varchar NOT NULL,
										Domain varchar NOT NULL,
										BreachDate varchar NOT NULL,
										AddedDate varchar NOT NULL,
										ModifiedDate varchar NOT NULL,
										PwnCount integer NOT NULL,
										Description varchar NOT NULL,
										DataClasses varchar NOT NULL,
										IsVerified integer NOT NULL,
										IsFabricated integer NOT NULL,
										IsSensitive integer NOT NULL,
										IsRetired integer NOT NULL,
										IsSpamList integer NOT NULL,
										LogoPath varchar NOT NULL
									); """

		cur.execute("DROP TABLE IF EXISTS breaches")
		cur.execute(breaches_table_def)

def deinit_breaches():

	# create a database connection
	conn = create_connection(db_path)
	with conn:
		cur = conn.cursor()
		cur.execute("DROP TABLE IF EXISTS breaches")










