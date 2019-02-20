import sqlite3
from sqlite3 import Error

import requests as requests
import time
import json

import sys

from database_connection import create_connection

# Emails Log File Path
log_path = '../logs/emails.log'

# Logging 

from logbook import Logger, FileHandler, StreamHandler, Processor, SyslogHandler

stream_handler_status_code = StreamHandler(sys.stdout, level='ERROR', bubble=True,\
	format_string="""[{record.level_name}] {record.channel} {record.message};
		Status: {record.extra[Status]}
		Email: {record.extra[Email]}""" )

stream_handler = StreamHandler(sys.stdout, level='NOTICE', bubble=True,\
	format_string="""[{record.level_name}] {record.channel} {record.message}; 
		Email: {record.extra[Email]}
		Name: {record.extra[Name]} 
	""" )

file_handler = SyslogHandler(application_name="email_handler", level='WARNING', bubble=True, \
	format_string="""[{record.level_name}] {record.message}; Email: {record.extra[Email]} Name: {record.extra[Name]}""")

log = Logger("HYBP_emails")

# Networking Functions

def get_request_emails(email):
	""" 
	Make a HTTP GET request to the HIBP API requesting all relevant breaches to given email
	Additionally, handle/log the variety of HTTP Status Codes

	:param email: str(user email)
	:return: HTTP Response Object or None
	"""

	def logging_status_code(record):
		""" 
		Use dynamic scoping to load the email argument and status code into the log record
		So, response.status_code comes from the get_request_emails function
		So, email comes from the get_request_emails argument

		:param record: log record
		"""

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
		# Note that this return value cannot be None, since a 404 is not erroneous behavior when querying API for emails
		# 404 simply means that no breaches were found for the email that was provided

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


# Database Functions

def insert_or_replace_emails(conn, emails):
	"""
	Take a list of tuples (structured in query format) and insert them into the database

	:param conn: db connection object
	:param emails: List[Tuple(email)] - in query format; returned by get_queries_from_emails
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

# Helper Functions

def get_queries_from_emails(response_text, email):
	""" 
	Create a list of tuples of the form (email, breach[Name]) for insertion into database
	The breach[Name] field will be used as a foreign key to reference a breach in the breaches table

	:param response_text:
	:param email: str(user email)
	:return: List[Tuple(email)]
	"""

	email_queries = []

	for breach in response_text:
		query = (email, breach['Name'])
		email_queries.append(query)

	return email_queries


def logging_stream_helper(row):
	""" 
	Helper function for logging relevant breaches corresponding to a given email

	:param row: Tuple(email, breach_name)
	"""
	def logging_arguments(record):
		""" 
		Use dynamic scoping to inject the Email and Name into the log record.
		So, row comes from the argument in logging_stream_helper()

		:param record: log record
		"""
		record.extra['Email'] = row[0]		#['Email']
		record.extra['Name'] = row[1]		#['Name']
		
	with file_handler.applicationbound():
		with Processor(logging_arguments).applicationbound():
			log.warning('Email found in breach! See emails.log file for more info.')

# Multiprocessing functions

def get_emails_parallel(emailQueue):
	""" 
	A process to load the HTTP Response from a query for a given email into the database
	NOTE that this function relies on emailQueue being a process-safe Queue
	NOTE that this function should only be called from multiprocess_email_handler.py

	:param emailQueue: Python.Multiprocessing.Queue() used as a job queue, holding emails that have yet to be queried against API
	"""

	if emailQueue.empty():
		return True
	else:
		email = emailQueue.get()

	httpResponse = get_request_emails(email)
	
	# If request fails, put job back on queue and terminate.
	# Let multiprocess_email_handler do recovery.
	if httpResponse == None:
		emailQueue.put(email)
		return False
	# Catches the status_code == 404 case
	# For this use of the API, this simply means there are no breaches corresponding to the given email
	elif type(httpResponse) == str: 
		return True

	jsonData = json.loads(httpResponse.text)
	queryList = get_queries_from_emails(jsonData, email)

	conn = create_connection()

	insert_or_replace_emails(conn, queryList)

	return True


# Standalone Functions

def check_email(email):
	""" 
	Function that looks up a given email in our database and logs any relevant breaches found
	Log a NOTICE if no breach found. (Only to stream)
	Log a WARNING if breach found. 
	Log blurb goes into stream. Entire log goes into log file. 

	:param email: str(email)
	"""
	if email == None:
		return False

	def logging_no_arguments(record):
		""" 
		Use dynamic scoping to include email as part of the log record
		So, email comes from the argument to check_email()

		:param record: log record
		"""
		record.extra['Email'] = email

	conn = create_connection()
	cur = conn.cursor()

	cur.execute("SELECT Email, Name from emails NATURAL JOIN breaches where upper(Email) = upper('{}')".format(email))
	rows = cur.fetchall()

	with stream_handler.applicationbound():
		if len(rows) == 0:
			with Processor(logging_no_arguments).applicationbound():
				log.notice('No breaches found for email. ')
		else:
			for row in rows:
				logging_stream_helper(row)


