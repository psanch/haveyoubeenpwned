import sqlite3
from sqlite3 import Error

from database_connection import create_connection

def init_breaches():

	# create a database connection
	conn = create_connection()
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
	conn = create_connection()
	with conn:
		cur = conn.cursor()
		cur.execute("DROP TABLE IF EXISTS breaches")










