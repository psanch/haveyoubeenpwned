import sqlite3
from sqlite3 import Error

import requests as requests
import time
import json

import sys

from database_connection import create_connection

# Breaches Log File Path
log_path = "../logs/breaches.log"

from logbook import Logger, FileHandler, StreamHandler, Processor

stream_handler_status_code = StreamHandler(sys.stdout, level='ERROR', bubble=True,\
	format_string="""[{record.level_name} @ {record.time:%Y-%m-%d %H:%M:%S}]{record.channel}: {record.message} 
		Status: {record.extra[Status]}""" )

stream_handler = StreamHandler(sys.stdout, level='NOTICE', bubble=True,\
	format_string="""[{record.level_name} @ {record.time:%Y-%m-%d %H:%M:%S}]{record.channel}: {record.message}
		Domain: {record.extra[Domain]} 
	""" )

file_handler = FileHandler(log_path, level='WARNING', bubble=True, \
	format_string="""[{record.level_name} @ {record.time:%Y-%m-%d %H:%M:%S}]{record.channel}: {record.message} 
		{record.extra[Name]} 
		{record.extra[Title]} 
		{record.extra[Domain]} 
		{record.extra[BreachDate]} 
		{record.extra[AddedDate]} 
		{record.extra[ModifiedDate]} 
		{record.extra[PwnCount]} 
		{record.extra[Description]} 
		{record.extra[LogoPath]} 
		{record.extra[DataClasses]} 
		{record.extra[IsVerified]} 
		{record.extra[IsFabricated]} 
		{record.extra[IsSensitive]} 
		{record.extra[IsRetired]} 
		{record.extra[IsSpamList]} 
	""")

log = Logger("BREACH-HANDLER-LOGGER")


def get_request_breaches():
	
	def logging_status_code(record):
		record.extra['Status'] = response.status_code

	headers = {
		'User-Agent': 'HaveIBeenPwned Daily Crawler', #API asks for us to specify user agent
	}

	response = requests.get("https://haveibeenpwned.com/api/v2/breaches", headers = headers)
	response.encoding = 'utf-8'

	if str(response.status_code) == "200":
		return response

	elif str(response.status_code) == "404":
		with stream_handler_status_code.applicationbound():
			with Processor(logging_status_code).applicationbound():
				log.error("Erroneous status code. Failed to load breaches.")
		return None

	elif str(response.status_code) == "429": 
		with stream_handler_status_code.applicationbound():
			with Processor(logging_status_code).applicationbound():
				log.error("Erroneous status code. Failed to load breaches.")
		return None

	else:
		with stream_handler_status_code.applicationbound():
			with Processor(logging_status_code).applicationbound():
				log.error("Erroneous status code. Failed to load breaches.")
		return None


def get_queries_from_breaches(response_text):
	breach_queries = []

	for breach in response_text:
		query = (breach['Name'], breach['Title'], breach['Domain'], breach['BreachDate'], breach['AddedDate'], breach['ModifiedDate'], breach['PwnCount'], breach['Description'], breach['LogoPath'], str(breach['DataClasses']), breach['IsVerified'], breach['IsFabricated'], breach['IsSensitive'], breach['IsRetired'], breach['IsSpamList'])
		breach_queries.append(query)

	return breach_queries


def insert_or_replace_breaches(conn, breaches):
	"""
	conn: db connection object
	breach: List[breach] - in query format; returned by get_queries_from_breaches
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
		except Error as e:
			print(e)

	conn.commit()

	return


def check_domain(domain):
	conn = create_connection()
	cur = conn.cursor()

	cur.execute("SELECT * from breaches where upper(Domain) = upper('{}')".format(domain))
	rows = cur.fetchall()

	def logging_no_arguments(record):
		record.extra['Domain'] = domain

	with stream_handler.applicationbound():
		if len(rows) == 0:
			with Processor(logging_no_arguments).applicationbound():
				log.notice('No breaches found for domain. ')
		else:
			for row in rows:
				logging_stream_helper(row)

def logging_stream_helper(row):
	def logging_arguments(record):
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
			log.warning('Breach found! See breaches.log file for more info.')
		
def read_and_check_domains(filename='../inputs/domains.txt'):
	with open(filename) as fp:
		domains = fp.read().splitlines()

		for domain in domains:
			check_domain(domain)

# Standalone Functions

def load_breaches():
	# Make a GET request to 
	httpResponse = get_request_breaches()
	if httpResponse == None:
		return False

	jsonData = json.loads(httpResponse.text)

	# List of breaches into query format for insertion into SQLite
	queryList = get_queries_from_breaches(jsonData)

	# create a database connection and cursor
	conn = create_connection()

	insert_or_replace_breaches(conn, queryList)

	return True


