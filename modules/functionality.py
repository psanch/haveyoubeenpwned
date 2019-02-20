import os
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="UTF-8")

import breach_database_definition
import email_database_definition
import breach_handler
import email_handler
import multiprocess_email_handler

import time

# 1
def get_breaches():
	ret = breach_handler.load_breaches()
	if ret == True:
		print("Loading breaches successful.", flush=True)
	else:
		print("Loading breaches unsuccessful.", flush=True)

# 2
def check_domains():
	breach_handler.read_and_check_domains()

# 3
def check_emails():
	number_processes = input("How many worker processes would you like to have? (1 <= X <= 16)\n")
	if int(number_processes) >= 1 and int(number_processes) <= 16:
		multiprocess_email_handler.start_k_email_checker_processes(int(number_processes))
	else:
		print("Error: Invalid number of processes.")

# 4
def consume_breaches_daily(wait=(60*60*24)):
	user_sleep = input("How many seconds between requests? (>= 1.3 as per the API)")
	if int(wait) >= 1.3:
		wait = float(user_sleep)
	else:
		print("Unexpected number. Defaulting to daily.")

	while(1):
		get_breaches()
		time.sleep(wait)

# 5
def init_databases():
	email_database_definition.deinit_emails()
	breach_database_definition.deinit_breaches()
	
	breach_database_definition.init_breaches()
	email_database_definition.init_emails()

# 8
def reset_breaches_logs():
	fp = open('../logs/breaches.log','w')
	fp.close()

# 9
def reset_emails_logs():
	fp = open('../logs/emails.log','w')
	fp.close()


def main_loop():
	while(1):
		os.system('clear')
		os.system('clear')

		prompt = """Welcome to the HaveYouBeenPwned Menu.
	1 - Load breaches from API into Breaches.db
	2 - Check domains against database (from inputs/domains.txt)
	3 - Check emails against breaches database (from inputs/emails.txt)
	4 - Get all known breaches on a daily basis (*BLOCKING PROCESS)
	5 - Cat Breaches.log
	6 - Cat Emails.log
	7 - Clean Databases
	8 - Clean Breaches Log
	9 - Clean Emails Log
	Else - Quit
			"""
			
		ui = input(prompt)

		if ui == "1":
			get_breaches()
		elif ui == "2":
			check_domains()
		elif ui == "3":
			check_emails()
		elif ui == "4":
			consume_breaches_daily()
		elif ui == "5":
			os.system('cat ../logs/breaches.log')
		elif ui == "6":
			os.system('cat ../logs/emails.log')
		elif ui == "7":
			init_databases()
		elif ui == "8":
			reset_breaches_logs()
		elif ui == "9":
			reset_emails_logs()
		else:
			os.system('clear')
			os.system('clear')
			exit()

		input("\nPress Enter to continue.")

main_loop()
