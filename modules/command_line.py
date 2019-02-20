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

# 1 - Load breaches from API into Breaches.db
def get_breaches():
	ret = breach_handler.load_breaches()
	if ret == True:
		print("Loading breaches successful.", flush=True)
	else:
		print("Loading breaches unsuccessful.", flush=True)

# 2 - Check domains against database (from inputs/domains.txt)
def check_domains():
	breach_handler.read_and_check_domains()

# 3 - Check emails against breaches database (from inputs/emails.txt)
def check_emails(n=1):
	if int(n) >= 1 and int(n) <= 16:
		multiprocess_email_handler.start_k_email_checker_processes(int(n))
	else:
		print("Error: Invalid number of processes. Defaulting to 1 process.")


# 4 - Get all known breaches at a user-defined rate and check domains against newest breach data
def consume_breaches_rate(wait=(60*60*24)):
	user_sleep = input("How many seconds between requests? (>= 1.3 as per the API)")
	if int(wait) >= 1.3: # As recommended by API
		wait = float(user_sleep)
	else:
		print("Unexpected number. Defaulting to daily.")

	while(1):
		get_breaches()
		check_domains()
		time.sleep(wait)

# 5 - Get all known breaches at a user-defined rate and check emails against newest breach data
def consume_emails_rate(wait=(60*60*24), n=1):
	# Get user defined rate, if valid
	user_sleep = input("How many seconds between requests? (>= 1.3 as per the API)")
	if int(wait) >= 1.3: # As recommended by API
		wait = float(user_sleep)
	else:
		print("Unexpected number. Defaulting to daily.")

	# Get user-defined number of worker processes, if valid
	number_processes = input("How many worker processes would you like to have? (1 <= X <= 16)\n")
	if int(number_processes) >= 1 and int(number_processes) <= 16:
		n = number_processes
	else:
		print("Invalid number of processes. Defaulting to 1 process.")

	while(1):
		get_breaches()
		check_emails(n)
		time.sleep(wait)

# 6 - Cat Log Files
def cat_logs():
	print("== EMAILS.LOG:", flush=True)
	os.system('cat ../logs/emails.log')
	print("== END EMAILS.LOG:\n==", flush=True)
	print("== BREACHES.LOG:", flush=True)
	os.system('cat ../logs/breaches.log')
	print("== END BREACHES.LOG:", flush=True)

# 7 - Clean Databases 
def init_databases():
	# Note that email table has a dependency (foreign key) on breaches table
	# So they should be initialized in order: 	breaches -> emails
	# and backwards for de-init: 				emails -> breaches
	email_database_definition.deinit_emails()
	breach_database_definition.deinit_breaches()
	
	breach_database_definition.init_breaches()
	email_database_definition.init_emails()

# 8 - Clean breaches logs
def reset_breaches_logs():
	fp = open('../logs/breaches.log','w')
	fp.close()

# 9 - Clean emails logs
def reset_emails_logs():
	fp = open('../logs/emails.log','w')
	fp.close()


def main_loop():
	""" 
	Main loop that provides interactive functionality from the Command Line
	"""

	while(1):
		os.system('clear')
		os.system('clear')

		prompt = """Welcome to the HaveYouBeenPwned Menu.
	1 - Load breaches from API into Breaches.db
	2 - Check domains against database (from inputs/domains.txt)
	3 - Check emails against breaches database (from inputs/emails.txt)
	4 - Get all known breaches at a user-defined rate and check domains against new data (*BLOCKING PROCESS)
	5 - Get all known breaches at a user-defined rate and check emails against new breaches (*BLOCKING PROCESS)
	6 - Cat Log Files
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
			number_processes = input("How many worker processes would you like to have? (1 <= X <= 16)\n")
			check_emails(number_processes)
		elif ui == "4":
			consume_breaches_rate()
		elif ui == "5":
			consume_emails_rate()
		elif ui == "6":
			cat_logs()

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
