import sqlite3
from sqlite3 import Error

import requests as requests
import time
import json

import sys

import os.path
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
db_path = os.path.join(BASE_DIR, "../db/breaches.db")

# Emails Log File Path
log_path = '../logs/emails.log'

from logbook import Logger, FileHandler, StreamHandler, Processor

stream_handler_status_code = StreamHandler(sys.stdout, level='ERROR', bubble=True,\
	format_string="""[{record.level_name} @ {record.time:%Y-%m-%d %H:%M:%S}]{record.channel}: {record.message} 
		Status: {record.extra[Status]}
		Email: {record.extra[Email]}""" )

stream_handler = StreamHandler(sys.stdout, level='NOTICE', bubble=True,\
	format_string="""[{record.level_name} @ {record.time:%Y-%m-%d %H:%M:%S}]{record.channel}: {record.message}
		Email: {record.extra[Email]}
		Name: {record.extra[Name]} 
	""" )

file_handler = FileHandler(log_path, level='WARNING', bubble=True, \
	format_string="""[{record.level_name} @ {record.time:%Y-%m-%d %H:%M:%S}]{record.channel}: {record.message} 
		Email: {record.extra[Email]}
		Name: {record.extra[Name]} 
	""")

log = Logger("EMAIL-HANDLER-LOGGER")


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


def get_request_emails(email):

	def logging_status_code(record):
		record.extra['Status'] = response.status_code
		record.extra['Email'] = email

	headers = {
		'User-Agent': 'HaveIBeenPwned Daily Crawler', #API asks for us to specify user agent
	}

	response = requests.get("https://haveibeenpwned.com/api/v2/breachedaccount/{acc}".format(acc=email), headers=headers)
	response.encoding = 'utf-8'

	if str(response.status_code) == "200":
		return response

	elif str(response.status_code) == "404":
		return "Page Not Found"
		# Note that this return value cannot be None, since a 404 is not erroneous behavior
		# 404 means that no breaches were found for the email that was provided

	elif str(response.status_code) == "429": 
		with stream_handler_status_code.applicationbound():
			with Processor(logging_status_code).applicationbound():
				log.error("Erroneous status code. Failed to query email against breaches.")
		return None

	else:
		with stream_handler_status_code.applicationbound():
			with Processor(logging_status_code).applicationbound():
				log.error("Erroneous status code. Failed to query email against breaches.")
		return None


def get_queries_from_emails(response_text, email):
	email_queries = []

	for breach in response_text:
		query = (email, breach['Name'])
		email_queries.append(query)

	return email_queries


def insert_or_replace_emails(conn, emails):
	"""
	conn: db connection object
	emails: List[email] - in query format; returned by get_queries_from_emails
	"""

	sql = ''' INSERT OR REPLACE INTO emails(
		Email,
		Name) 
		VALUES(?,?) '''
	
	cur = conn.cursor()

	for email in emails:
		try:
			cur.execute(sql, email)
		except Error as e:
			print(e)

	conn.commit()
	return


def check_emails_parallel(emailQueue):
	if emailQueue.empty():
		return True
	else:
		email = emailQueue.get()

	httpResponse = get_request_emails(email)
	if httpResponse == None:
		emailQueue.put(email)
		return False
	elif type(httpResponse) == str:
		return True

	jsonData = json.loads(httpResponse.text)
	queryList = get_queries_from_emails(jsonData, email)

	# create a database connection
	conn = create_connection(db_path)
	cur = conn.cursor()

	insert_or_replace_emails(conn, queryList)

	return True


def logging_stream_helper(row):
	def logging_arguments(record):
		record.extra['Email'] = row[0]		#['Email']
		record.extra['Name'] = row[1]		#['Name']
		
	with file_handler.applicationbound():
		with Processor(logging_arguments).applicationbound():
			log.warning('Email found in breach! See emails.log file for more info.')


def get_emails_from_file(filename="../inputs/emails.txt"):
	with open(filename) as fp:
		emails = fp.read().splitlines()
	return emails


# Standalone Functions

def lookup_email(email):
	if email == None:
		return False

	def logging_no_arguments(record):
		record.extra['Email'] = email

	conn = create_connection(db_path)
	cur = conn.cursor()

	cur.execute("SELECT Email, Name from emails NATURAL JOIN breaches where Email = '{}'".format(email))
	rows = cur.fetchall()

	with stream_handler.applicationbound():
		if len(rows) == 0:
			with Processor(logging_no_arguments).applicationbound():
				log.notice('No breaches found for email. ')
		else:
			for row in rows:
				logging_stream_helper(row)


