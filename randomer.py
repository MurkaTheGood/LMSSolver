from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support.ui import Select
from typing import Tuple
from datetime import datetime
import random
import time
import os

CRED_PATH = 'credentials.txt'
TEXT_ANSWERS_PATH = 'text_answers.txt'
TEXT_ANSWERS = []

def get_auth_data() -> Tuple[str, str]:
	''' returns the saved auth data for the LMS user.
		will ask for credentials interactively and save them if they aren't present
	'''
	try:
		# try to read from file
		with open(CRED_PATH, 'r') as f:
			cred = [s.strip() for s in f.readlines()]
			return (cred[0], cred[1])
	except:
		# failed to read from file, ask for credentials
		login, password = \
			input('LMS login: '), input('LMS password: ')

		# save
		with open(CRED_PATH, 'w') as f:
			f.write(login)
			f.write('\n')
			f.write(password)

		# return
		return (login, password)

def init_text_answers():
	# not exists - add one built-in answer
	if not os.path.isfile(TEXT_ANSWERS_PATH):
		TEXT_ANSWERS.append('i don\'t know(')
		return

	# read all text answers
	with open(TEXT_ANSWERS_PATH, 'r') as f:
		# iterate through all lines
		for t in f.readlines():
			# check if not empty
			if t:
				# strip and add to text answers
				TEXT_ANSWERS.append(t.strip())

def answer_select(select_elem : WebElement) -> None:
	''' answer the dropdown menu; will select the according
		answer if it is present in JSON.
	'''

	# TODO: get the caption of the <select>
	select_caption = 'TODO'

	# get all possible options as list of tuples (value, visual name)
	options = \
		[(i.get_attribute('value'), i.text) \
			for i in select_elem.find_elements(By.TAG_NAME, 'option')]

	# remove the first option, as it's always empty
	options = options[1:]

	# selected options
	selected_option = random.choice(options)

	# get the select field
	select = Select(select_elem)

	# select the random answer (by value)
	select.select_by_value(selected_option[0])

	# log
	print('Selected value \'%s\' for key \'%s\'' % \
		(selected_option[1], select_caption))

def answer_text_input(input_elem : WebElement):
	''' answer the text input; will select the according
		answer if it is present in JSON.
	'''

	# TODO: get the question text
	question_text = 'TODO'

	# get the answer
	answer = random.choice(TEXT_ANSWERS)

	# set the answer
	input_elem.send_keys(answer)

	# log
	print('Typed \'%s\' into question \'%s\'' % \
		(answer, question_text))

def main():
	# init the answers
	init_text_answers()

	# getting the credentials
	login, password = get_auth_data()

	# log
	print('Starting the driver...')

	# open the headless gecko driver
	opts = webdriver.FirefoxOptions()
	opts.headless = False
	driver = webdriver.Firefox(options=opts)

	# naviagate to LMS main page
	print('Navigating to the LMS login page...')
	driver.get('https://online.mospolytech.ru/login/index.php')

	# authorizing
	print('Authorizing...')

	# type the credentials
	driver.find_element(By.ID, 'username').send_keys(login)
	time.sleep(0.1)
	driver.find_element(By.ID, 'password').send_keys(password)
	time.sleep(0.1)
	driver.find_element(By.ID, 'loginbtn').click()

	# asking to paste the 'begin the testing' URL
	driver.get(input('URL of "begin the testing" page: '))

	# log
	print('Clicking on the "Begin the testing" button')

	# looking for the start button
	start_button = \
		driver.find_element(By.CLASS_NAME, 'quizstartbuttondiv'). \
		find_element(By.TAG_NAME, 'button')

	# clicking on the start button
	start_button.click()

	# using infinite loop that will be broken when 
	# there is button to finish the test on the page

	while True:
		# check if there is summary table (the test is finished)
		if driver.find_elements(By.CLASS_NAME, 'generaltable'):
			print('The test is over! Sending the results...')

			# get the second submit button
			finish_button = \
				driver.find_elements(By.CLASS_NAME, 'submitbtns')[1]. \
				find_element(By.TAG_NAME, 'button')

			# click on the finish button
			#finish_button.click()

			# check if there are confiramtion buttons
			confirmation_buttons = driver. \
				find_elements(By.CLASS_NAME, 'confirmation-buttons')
			if confirmation_buttons:
				# get the confirmation button
				confirm_button = confirmation_buttons[0]. \
					find_elements(By.TAG_NAME, 'input')[0]

				# confirm!
				#confirm_button.click()

				# log
				print('Confirmed the results')

			break

		# looking for questions
		questions = driver.find_elements(By.CLASS_NAME, 'que')

		for question in questions:
			# check if there are moving parts (not combined with 
			# the next one because the answering strategy may differ)
			elements_list = question.find_elements(By.CSS_SELECTOR, 'td.control.hiddenifjs > select')
			if elements_list:
				input('Cannot answer the pages with moving parts. Please answer them (do not go to the next page!) and press Enter...')

			# check if there are selects (not combined with 
			# the previous one because the answering strategy may differ)
			elements_list = question.find_elements(By.CSS_SELECTOR, 'span.control.group1 > select')
			if elements_list:
				# iterate through all the <select>'s
				for select_elem in elements_list:
					# answer
					answer_select(select_elem)
					# sleep a bit
					time.sleep(1)

			# check if there are text inputs
			elements_list = question.find_elements(By.CSS_SELECTOR, 'input.form-control.d-inline')
			if elements_list:
				# iterate through all the <input>'s
				for input_elem in elements_list:
					# answer
					answer_text_input(input_elem)
					# sleep a bit
					time.sleep(1)


		# finish the test or go to the next page
		print('Going to the next page...')

		submit_button = driver.find_element(By.NAME, 'next')
		submit_button.click()

	# log
	print('Do anything you need with this page')


	# to prevent a lot of CPU time
	while True: time.sleep(10)

	# done, close the driver
	driver.close()


# entry point
if __name__ == '__main__':
	main()