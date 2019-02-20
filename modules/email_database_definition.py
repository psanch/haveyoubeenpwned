import sqlite3
from sqlite3 import Error

import json

import sys

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


def init_emails():

	# create a database connection
	conn = create_connection(db_path)
	with conn:

		cur = conn.cursor()

		emails_table_def = """ CREATE TABLE IF NOT EXISTS emails(
										Email varchar,
										Name varchar,
										PRIMARY KEY(Email, Name),
										FOREIGN KEY (Name) REFERENCES breaches(Name)
									); """

		cur.execute(emails_table_def)

def deinit_emails():

	# create a database connection
	conn = create_connection(db_path)
	with conn:

		cur = conn.cursor()
		cur.execute("DROP TABLE IF EXISTS emails")








