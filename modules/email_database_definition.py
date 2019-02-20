import sqlite3
from sqlite3 import Error

from database_connection import create_connection


def init_emails():
	""" 
	Initalizes emails table in breaches.db
	
	:return: None
	"""

	conn = create_connection()
	with conn:

		cur = conn.cursor()

		#define emails table schema
		emails_table_def = """ CREATE TABLE IF NOT EXISTS emails(
										Email varchar NOT NULL,
										Name varchar NOT NULL,
										PRIMARY KEY(Email, Name),
										FOREIGN KEY (Name) REFERENCES breaches(Name)
									); """

		
		try:
			cur.execute("DROP TABLE IF EXISTS emails")
		except Error as e:
			print(e)

		try:
			cur.execute(emails_table_def)
		except Error as e:
			print(e)
		


def deinit_emails():
	""" 
	Delete emails table in breaches.db
	
	:return: None
	"""

	# create a database connection
	conn = create_connection()
	with conn:

		cur = conn.cursor()
		
		try:
			cur.execute("DROP TABLE IF EXISTS emails")
		except Error as e:
			print(e)
		


