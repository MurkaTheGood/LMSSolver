from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support.ui import Select
from typing import Tuple, List
from datetime import datetime
import random
import time
import os
import enum
import json

class QuestionType(enum.Enum):
	''' enum for question types.
		More information in README.md
	'''

	unknown, multichoice, gapselect, shortanswer = \
		range(4)

CRED_PATH = 'credentials.txt'
TEXT_ANSWERS_PATH = 'text_answers.txt'
TEXT_ANSWERS = []

CORRECT_ANSWERS = {}
CORRECT_RATIO = None

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
			cred = '%s\n%s' % (login, password)
			f.write(cred)

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

	print('Loaded text answers: %s' % len(TEXT_ANSWERS))

def init_correct_answers():
	''' loads the correct answers from 'answers.json' '''
	global CORRECT_ANSWERS, CORRECT_RATIO

	try:
		# try to load answers
		with open('answers.json', 'r') as f:
			CORRECT_ANSWERS = json.loads(f.read())

		# ok, log
		print('! Loaded correct answers!')

		# ask for percent
		while not CORRECT_RATIO:
			try:
				# read the percent
				correct_percent = \
					input('Desired correct answers ratio? Type percent, for example \'95\', \'67\', etc... ')
				correct_percent = float(correct_percent)

				# check range
				if correct_percent < 0 or correct_percent > 100:
					raise Exception('Out of range')

				# calculate the ratio
				CORRECT_RATIO = correct_percent / 100
			except:
				# fail
				print('Must be a number in range [0..100] with \'%\' sign! Try again.')

		# log
		print('! Ok, %s%% will be correct' % int(CORRECT_RATIO * 100))
	except:
		print('! No answers supplied, answering randomly')
		pass

def remove_extra_whitespaces(original : str) -> str:
	''' this function removes extra whitespaces inside string '''
	# replace newlines with spaces
	original = original.replace('\n', ' ')

	# remove dublicated spaces
	while original.find(' ' * 2) != -1:
		original = original.replace(' ' * 2, ' ')

	return original

def get_question_type(question_elem : WebElement) -> QuestionType:
	# getting the classes of question WebElement
	classes = question_elem.get_attribute('class').split(' ')

	if 'multichoice' in classes: return QuestionType.multichoice
	if 'gapselect' in classes: return QuestionType.gapselect
	if 'shortanswer' in classes: return QuestionType.shortanswer

	# failed to determite the type of question
	return QuestionType.unknown


def answer_gapselect(select_elem : WebElement, s_text : str) -> None:
	''' answers the dropdown menu; will select the according
		answer if it is present in JSON.
	'''

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
	print('gapselect \'%s\': \'%s\'' % \
		(s_text, selected_option))

def answer_shortanswer(input_elem : WebElement, q_text : str) -> None:
	''' answers the text input; will select the according
		answer if it is present in JSON.
	'''

	# TODO: check if can find the answer in JSON

	# get the answer
	answer = random.choice(TEXT_ANSWERS)

	# set the answer
	input_elem.send_keys(answer)

	# log
	print('shortanswer \'%s\': \'%s\'' % \
		(q_text, answer))

def answer_multichoice(answer_boxes : List[WebElement], q_text : str) -> None:
	''' answers multichoice; will select the according
		answer if it is present in JSON.
	'''

	# TODO: check if can find the answer in JSON

	# get options list of tuples
	#	(input_WebElement : WebElement, answer_text : str)
	options = []
	for a_box in answer_boxes:
		options.append(
			(a_box.find_element(By.TAG_NAME, 'input'),
			remove_extra_whitespaces(
				a_box.find_element(By.CSS_SELECTOR, 'div.d-flex').text.strip()
			))
		)

	# find the correct option
	if 'multichoice' in CORRECT_ANSWERS:
		# questions with the same text in json
		questions_in_json = \
			[x for x in CORRECT_ANSWERS['multichoice'] if x['title'] == q_text]

		# not found
		if not questions_in_json:
			correct_options = [random.choice(options)]

			# log
			print('Not found correct answers, choosing randomly')
		else:
			# create the list of correct options
			correct_options = []

			# found, specify the correct options
			# iterate through all questions in JSON
			for q in questions_in_json:
				for correct_answer in q['answers']:
					try:
						correct_options.append(
							next(x for x in options if correct_answer in x[1]))
					except:
						# this question in JSON does not contain the corrent answer
						pass

			# log
			print('Found correct answers')
	# random options
	else:
		correct_options = [random.choice(options)]

	# select
	for correct_option in correct_options:
		correct_option[0].click()

	# log
	print('multichoice \'%s\': \'%s\'' % \
		(q_text, correct_option[1]))


def main():
	# getting the credentials
	login, password = get_auth_data()

	# init the answers
	init_text_answers()
	# correct answers load
	init_correct_answers()

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

	# check if not first question
	if driver.find_element(By.CSS_SELECTOR, 'h3.no').text.strip().split(' ')[-1] != '1':
		# go to the first question
		driver.find_element(By.CSS_SELECTOR, '#quiznavbutton1').click()
		# log
		print('Going to the first question...')

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

		# looking for questions on this page
		questions = driver.find_elements(By.CLASS_NAME, 'que')

		for q_elem in questions:
			# get the type of the question
			q_type = get_question_type(q_elem)

			# shortanswer
			if q_type == QuestionType.shortanswer:
				# get the question title
				q_text = q_elem. \
					find_element(By.CLASS_NAME, 'qtext').text.strip()

				# remove whitespaces
				q_text = remove_extra_whitespaces(q_text)

				# get the text input
				q_input = q_elem. \
					find_element(By.CSS_SELECTOR, 'input.d-inline.form-control')

				# answer
				answer_shortanswer(q_input, q_text)
			# gapselect
			elif q_type == QuestionType.gapselect:
				# iterate through <select> parent boxes
				select_parent_boxes = \
					q_elem.find_elements(By.CSS_SELECTOR, 'div.qtext > p')

				# iterate through all boxes
				for box in select_parent_boxes:
					# check if box does not have select inside
					if not box.find_elements(By.TAG_NAME, 'select'):
						continue

					# get the select text
					s_text = box.text.strip()

					# remove whitespaces
					s_text = remove_extra_whitespaces(s_text)

					# get the <select> tag
					s_input = box.find_element(By.TAG_NAME, 'select')

					# answer
					answer_gapselect(s_input, s_text)
			# multichoice
			elif q_type == QuestionType.multichoice:
				# get the question text
				q_text = q_elem. \
					find_element(By.CSS_SELECTOR, 'div.qtext'). \
					text.strip()

				# remove whitespaces
				q_text = remove_extra_whitespaces(q_text)

				# get answers list
				q_answer_boxes = q_elem. \
					find_elements(By.CSS_SELECTOR, 'div.answer > div')

				# answer
				answer_multichoice(q_answer_boxes, q_text)
			# unknown
			else:
				print('Unknown question type with classes %s, skipped' % \
					q_elem.get_attribute('class'))

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