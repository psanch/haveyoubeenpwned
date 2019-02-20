import multiprocessing
from multiprocessing import Process

import email_handler

def start_k_email_checker_processes(k=1):
	"""
	Function starts k processes to query the HIBP API and insert the relevant breaches into the database.
	Then, the father process looks up these relevant breaches and provides more info on these breaches.
	NOTE that in order to get meaningful breach data, the breaches database must be loaded with breaches.
	
	k: int
	"""

	# Read emails from inputs/emails.txt into list
	emailList = email_handler.get_emails_from_file()
	
	# Create a python.multiprocessing Queue to delegate task among worker procesess
	# Note that the Queue is thread and process safe.
	emailsToBeChecked = multiprocessing.Queue()

	for email in emailList:
		emailsToBeChecked.put(email)

	# Spawn a K-Process list targeting the "check_emails_parallel" function
	# All of them share the emailsToBeChecked Queue as a job queue
	processes = [ Process(target=email_handler.check_emails_parallel, args=(emailsToBeChecked,)) for i in range(k) ]

	# While the queue is not empty, start processes to pull jobs off the queue and deal with them
	while not emailsToBeChecked.empty():
		for i in range(k):
			processes[i].start()

		for i in range(k):
			processes[i].join()

	# After worker processes done, lookup each email and see if there are relevant breaches
	for email in emailList:
		email_handler.lookup_email(email)



