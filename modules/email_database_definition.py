import sqlite3
from sqlite3 import Error

from database_connection import create_connection

def init_emails():

	# create a database connection
	conn = create_connection()
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
	conn = create_connection()
	with conn:

		cur = conn.cursor()
		cur.execute("DROP TABLE IF EXISTS emails")








