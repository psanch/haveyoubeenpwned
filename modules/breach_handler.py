import sqlite3
from sqlite3 import Error

import requests as requests
import time
import json

import sys

from database_connection import create_connection

# Breaches Log File Path
log_path = "../logs/breaches.log"

# Logging

from logbook import Logger, FileHandler, StreamHandler, Processor, SyslogHandler

stream_handler_status_code = StreamHandler(sys.stdout, level='ERROR', bubble=True,\
	format_string="""[{record.level_name}] {record.channel} {record.message}; 
		Status:{record.extra[Status]}""" )

stream_handler = StreamHandler(sys.stdout, level='NOTICE', bubble=True,\
	format_string="""[{record.level_name}] {record.channel} {record.message};
		Domain: {record.extra[Domain]} 
	""" )

file_handler = SyslogHandler(application_name="breach_handler", level='WARNING', bubble=True, \
	format_string="""[{record.level_name}]{record.message}; Name: {record.extra[Name]} Title: {record.extra[Title]} Domain: {record.extra[Domain]} BreachDate: {record.extra[BreachDate]} AddedDate: {record.extra[AddedDate]} ModifiedDate: {record.extra[ModifiedDate]} PwnCount: {record.extra[PwnCount]} Description: {record.extra[Description]} LogoPath: {record.extra[LogoPath]} DataClasses: {record.extra[DataClasses]} IsVerified: {record.extra[IsVerified]} IsFabricated: {record.extra[IsFabricated]} IsSensitive: {record.extra[IsSensitive]} IsRetired: {record.extra[IsRetired]} IsSpamList: {record.extra[IsSpamList]} """)

log = Logger("HYBP_breaches")

# Networking Functions

def get_request_breaches():
	""" 
	Make a HTTP GET request to the HIBP API requesting all known breaches
	Additionally, handle/log the variety of HTTP Status Codes

	:return: HTTP Response Object (requests library) OR None to indicate failure
	"""
	
	def logging_status_code(record):
		""" 
		Use dynamic scoping to add the HTTP Response's status code into the log record.
		So, response.status_code comes from the HTTP Response in get_request_breaches()

		:param email: str(user email)
		:return: HTTP Response Object or None
		"""
		record.extra['Status'] = response.status_code


	headers = {
		'User-Agent': 'HaveIBeenPwned Daily Crawler', #API asks for us to specify user agent
	}

	response = requests.get("https://haveibeenpwned.com/api/v2/breaches", headers=headers)
	response.encoding = 'utf-8'

	if str(response.status_code) == "200":
		return response

	else:
		with stream_handler_status_code.applicationbound():
			with Processor(logging_status_code).applicationbound():
				log.error("Erroneous status code. Failed to load breaches.")
		return None

# Database Functions

def insert_or_replace_breaches(conn, breaches):
	"""
	Take a list of tuples (structured in query format) and insert/replace them into the database

	:param conn: db connection object
	:param breaches: List[Tuple(breach[Name], breach[Title], ...)]; returned by get_queries_from_breaches
	"""

	sql = ''' INSERT OR REPLACE INTO breaches(
		Name, 
		Title, 
		Domain, 
		BreachDate, 
		AddedDate, 
		ModifiedDate, 
		PwnCount, 
		Description, 
		DataClasses, 
		IsVerified, 
		IsFabricated, 
		IsSensitive, 
		IsRetired, 
		IsSpamList, 
		LogoPath) 
		VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?) '''
	
	cur = conn.cursor()

	for breach in breaches:
		try:
			cur.execute(sql, breach)

			# Commit changes to database every time a change is made
			# Minimizes data loss at expense of (constant amount) of performance
			conn.commit()

		except Error as e:
			print(e)

	return


def lookup_domain(domain):
	"""
	Check a domain against our database of known breaches
	Log a NOTICE if no breach found. (Only to stream)
	Log a WARNING if breach found. 
	Log blurb goes into stream. Entire log goes into log file.

	:param domain: str(URL)
	"""

	conn = create_connection()
	cur = conn.cursor()

	# Case sensitivity has to be handled since no control over user/API formatting
	cur.execute("SELECT * from breaches where upper(Domain) = upper('{}')".format(domain))
	rows = cur.fetchall()

	def logging_no_arguments(record):
		""" 
		Use dynamic scoping to inject the domain argument into the log record.
		So "domain" on the RHS of the '=' comes from the lookup_domain(domain) argument.
		
		:param record: log record
		"""
		record.extra['Domain'] = domain

	with stream_handler.applicationbound():
		if len(rows) == 0:
			with Processor(logging_no_arguments).applicationbound():
				log.notice('No breaches found for domain. ')
		else:
			for row in rows:

				# Helper to prevent excessive nesting/indentation
				logging_stream_helper(row)


# Helper Functions

def get_queries_from_breaches(response_text):
	"""
	Take HTTP Response JSON data and format it into tuples for insertion into database.

	:param response_text: HTTP_Response.text passed in as a JSON object
	:return: List[Tuples()] where the tuples hold the different columns of a given breach
	"""
	breach_queries = []

	for breach in response_text:
		query = (breach['Name'], breach['Title'], breach['Domain'], breach['BreachDate'], breach['AddedDate'], breach['ModifiedDate'], breach['PwnCount'], breach['Description'], breach['LogoPath'], str(breach['DataClasses']), breach['IsVerified'], breach['IsFabricated'], breach['IsSensitive'], breach['IsRetired'], breach['IsSpamList'])
		breach_queries.append(query)

	return breach_queries


def logging_stream_helper(row):
	"""
	Helper function to log a detected breach for a given domain.

	:param row: List[] returned from SQL SELECT query. Contains the columns of a given breach.
	"""

	def logging_arguments(record):
		""" 
		Use dynamic scoping to load the contents of logging_stream_helper(row)'s "row" argument into log record
		So, row[] used below is the argument to logging_stream_helper

		:param record: log record
		"""

		record.extra['Name'] = row[0]		#['Name']
		record.extra['Title'] = row[1]		#['Title']
		record.extra['Domain'] = row[2]		#['Domain']
		record.extra['BreachDate'] = row[3]		#['BreachDate']
		record.extra['AddedDate'] = row[4]		#['AddedDate']
		record.extra['ModifiedDate'] = row[5]		#['ModifiedDate']
		record.extra['PwnCount'] = row[6]		#['PwnCount']
		record.extra['Description'] = row[7]		#['Description']
		record.extra['LogoPath'] = row[8]		#['LogoPath']
		record.extra['DataClasses'] = row[9]		#['DataClasses']
		record.extra['IsVerified'] = row[10]		#['IsVerified']
		record.extra['IsFabricated'] = row[11]		#['IsFabricated']
		record.extra['IsSensitive'] = row[12]		#['IsSensitive']
		record.extra['IsRetired'] = row[13]		#['IsRetired']
		record.extra['IsSpamList'] = row[14]		#['IsSpamList']
		
	with file_handler.applicationbound():
		with Processor(logging_arguments).applicationbound():
			log.warning('Breach found! See syslog file for more info.')


def read_and_check_domains(filename='../inputs/domains.txt'):
	"""
	Check a domain against our database of known breaches.
	Log a NOTICE if no breach found.
	Log a WARNING if breach found. 
	Log blurb goes into stream. Entire log goes into log file.

	:param domain: str(URL)
	"""
	with open(filename) as fp:
		domains = fp.read().splitlines()

		for domain in domains:
			lookup_domain(domain)

# Standalone Functions

def load_breaches():
	"""
	Function that takes data from HIBP API and loads it into Database.
	Specifically, HTTP GET Request -> HTTP Response -> JSON -> List[Tuples] -> Database

	:return: True if succesful, False otherwise.
	"""

	# HTTP GET request
	httpResponse = get_request_breaches()
	if httpResponse == None:
		return False

	# Process raw text into JSON object
	jsonData = json.loads(httpResponse.text)

	# List of breaches into query format for insertion into SQLite
	queryList = get_queries_from_breaches(jsonData)

	# Connect to and insert to database
	conn = create_connection()
	insert_or_replace_breaches(conn, queryList)

	return True


