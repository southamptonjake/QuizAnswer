
# answering bot for trivia HQ and Cash Show
import json
import urllib.request as urllib2
from bs4 import BeautifulSoup
import bs4
from google import google
from PIL import Image
import pytesseract
import argparse
import cv2
import os
import pyscreenshot as Imagegrab
import sys
from halo import Halo
import urllib.parse
from urllib.parse import unquote, parse_qs, urlparse, urlencode
import time
import urllib.request
import requests
from fake_useragent import UserAgent
import re

from selenium import webdriver
from multiprocessing.dummy import Pool as ThreadPool
import itertools


# for terminal colors
class bcolors:
	HEADER = '\033[95m'
	OKBLUE = '\033[94m'
	OKGREEN = '\033[92m'
	WARNING = '\033[93m'
	FAIL = '\033[91m'
	ENDC = '\033[0m'
	BOLD = '\033[1m'
	UNDERLINE = '\033[4m'

# sample questions from previous games
sample_questions = {}

# list of words to clean from the question during google search
remove_words = []

# negative words
negative_words= []

driver = ""

last_question = ""
last_options = [1,1,1]

cache_html = {}

# load sample questions
def load_json():
	global remove_words, sample_questions, negative_words, driver
	remove_words = json.loads(open("Data/settings.json").read())["remove_words"]
	negative_words = json.loads(open("Data/settings.json").read())["negative_words"]

# take screenshot of question
def screen_grab(to_save):
	# 31,228 485,620 co-ords of screenshot// left side of screen
	im = Imagegrab.grab(bbox=(31,228,485,740)) 
	im.save(to_save)

# get OCR text //questions and options
def read_screen():
	screenshot_file="Screens/to_ocr.png"
	screen_grab(screenshot_file)

	#prepare argparse
	ap = argparse.ArgumentParser(description='HQ_Bot')
	ap.add_argument("-i", "--image", required=False,default=screenshot_file,help="path to input image to be OCR'd")
	ap.add_argument("-p", "--preprocess", type=str, default="thresh", help="type of preprocessing to be done")
	args = vars(ap.parse_args())

	# load the image
	image = cv2.imread(args["image"])
	gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

	if args["preprocess"] == "thresh":
		gray = cv2.threshold(gray, 0, 255,
			cv2.THRESH_BINARY | cv2.THRESH_OTSU)[1]
	elif args["preprocess"] == "blur":
		gray = cv2.medianBlur(gray, 3)

	# store grayscale image as a temp file to apply OCR
	filename = "Screens/{}.png".format(os.getpid())
	cv2.imwrite(filename, gray)

	# load the image as a PIL/Pillow image, apply OCR, and then delete the temporary file
	text = pytesseract.image_to_string(Image.open(filename))
	os.remove(filename)
	os.remove(screenshot_file)

	return text

def normalise(points):
	if points[0] != 0 or points[1] != 0 or points[2] != 0:
		sum_points = 0
		for x in range(0,3):
			sum_points += points[x]
		normal_points = []
		for x in range(0,3):
			normal_points.append((points[x] / sum_points) * 10)
		return normal_points
	return points
# get questions and options from OCR text
def parse_question():
	text = read_screen()
	lines = text.splitlines()
	question = ""
	options = list()
	flag=False

	for line in lines :
		if not flag :
			question=question+" "+line

		if '?' in line :
			flag=True
			continue

		if flag :
			if line != '' :
				options.append(line)
	return removeIV(question), options

def removeIV(question):
	try:
		if question[0] == " " and question[1] == "I" and question[2] == "v":
			question = question[3:]
		if question[0] == " ":
			question = question[1:]
		return question
	except IndexError:
		return question
# simplify question and remove which,what....etc //question is string
def get_neg(question):
	neg=False
	qwords = question.lower().split()
	if [i for i in qwords if i in negative_words]:
		neg=True
	return neg

# simplify question and remove which,what....etc //question is string
def simplify_ques(question):
	qwords = question.lower().split()
	cleanwords = [word for word in qwords if word.lower() not in remove_words]
	temp = ' '.join(cleanwords)
	clean_question=""
	#remove ?
	for ch in temp:
		if ch!="?" or ch!="\"" or ch!="\'":
			clean_question=clean_question+ch

	return clean_question.lower()

def smart_answer(content,qwords,option):
	option_printed = False
	zipped= zip(qwords,qwords[1:])
	points=0
	for el in zipped :
		if content.count(el[0]+" "+el[1])!=0 :
			if option_printed == False:
				option_printed = True
			points+=1000
	return points
# get web page
def get_page(link):
	try:
		if link.find('mailto') != -1:
			return ''
		if link in cache_html:
			return cache_html[link]
		req = urllib2.Request(link, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64)'})
		html = urllib2.urlopen(req).read()
		cache_html[link] = html
		return html
	except (urllib2.URLError, urllib2.HTTPError, ValueError) as e:
		return ''

# split the string
def split_string(source):
	splitlist = ",!-.;/?@ #"
	output = []
	atsplit = True
	for char in source:
		if char in splitlist:
			atsplit = True
		else:
			if atsplit:
				output.append(char)
				atsplit = False
			else:
				output[-1] = output[-1] + char
	return output

# use google to get wiki page
def google_ques(ques, options, neg, question_search):
	num_pages = 1
	points = list()
	content = ""
	maxo=""
	maxp=-sys.maxsize
	search_wiki = question_search[0]
	link = search_wiki
	content = question_search[1]
	soup = BeautifulSoup(content,"lxml")
	page = soup.get_text().lower()
	sig = False
	for o in options:
		try:
			o = o.lower()
			temp=0
			temp = temp + ((page.count(' ' + o + ' ')) * 1000)
			temp = temp + ((page.count('"' + o + '"')) * 1000)
			temp = temp + ((page.count(' ' + o + '"')) * 1000)
			temp = temp + ((page.count('"' + o + ' ')) * 1000)
			temp = temp + ((page.count('"' + o + '.')) * 1000)
			temp = temp + ((page.count(' ' + o + '.')) * 1000)
			temp = temp + (page.count(o))

			so = simplify_ques(o)
			words = split_string(so)
			for word in words:
				temp = temp + (page.count(' ' + word + ' '))
			if neg:
				temp*=-1
			if temp > 1000 or temp < -1000:
				sig = True
			temp = temp / len(page)

		except Exception as inst:
			temp = 0
		points.append(temp)
		if temp>maxp:
			maxp=temp
			maxo=o
	if points[0] == points[1] and points[0] == points[2] and points[1] == points[2]:
		maxo = "nope"
	return normalise(points),maxo,sig

def google_ans_wiki(ques, options, neg, option_search):
	sim_ques = simplify_ques(ques)
	num_pages = 1
	points = list()
	content = ""
	maxo=""
	maxp=-sys.maxsize
	words = split_string(sim_ques)
	sig = False
	for x in range(0,3) :
		try:
			o = options[x]
			o = o.lower()
			original=o
			# get google search results for option + 'wiki'
			content = option_search[x]
			soup = BeautifulSoup(content,"lxml")
			page = soup.get_text().lower()

			temp=0

			
			temp+=smart_answer(page, words, options[x])
			for word in words:
				temp = temp + page.count(word)
			if neg:
				temp*=-1
			if temp > 1000 or temp < -1000:
				sig = True
			temp = temp / len(page)
		except Exception as inst:
			temp = 0
		points.append(temp)
		if temp>maxp:
			maxp=temp
			maxo=original
	if points[0] == points[1] and points[0] == points[2] and points[1] == points[2]:
		maxo = "nope"
	return normalise(points),maxo,sig

def google_quesans(ques, options, neg, option_search):
	sim_ques = simplify_ques(ques)
	num_pages = 1
	points = list()
	content = ""
	maxo=""
	maxp=-sys.maxsize
	words = split_string(sim_ques)
	sig = False
	for x in range(0,3) :
		try:
			o = options[x]
			o = o.lower()
			original=o
			# get google search results for option + 'wiki'

			content = option_search[x]
			soup = BeautifulSoup(content,"lxml")
			page = soup.get_text().lower()

			temp=0

			for word in words:
				temp = temp + page.count(' ' + word + ' ')
			temp+=smart_answer(page, words, options[x])
			temp+=page.count(' ' + options[x] + ' ') * 3
			if neg:
				temp*=-1
			if temp > 1000 or temp < -1000:
				sig = True
			temp = temp / len(page)
		except Exception as inst:
			temp = 0
		points.append(temp)
		if temp>maxp:
			maxp=temp
			maxo=original
	if points[0] == points[1] and points[0] == points[2] and points[1] == points[2]:
		maxo = "nope"
	return normalise(points),maxo,sig

def google_ques_ans(ques, options, neg):
	num_pages = 1
	points = list()
	content = ""
	maxo=""
	maxp=-sys.maxsize
	for o in options:
		o = o.lower()
		original=o
		driver.get('https://www.google.com/search?q=' + ques + ' ' + o)
		content = driver.page_source
		soup = bs4.BeautifulSoup(content, "lxml")
		elems = soup.select('#resultStats')
		temp = int(elems[0].getText().replace(',','').split()[1])
		points.append(temp)
		if temp>maxp:
			maxp=temp
			maxo=original

	return normalise(points),maxo,sig

def different_valid_ocr(question,options):
	global last_options,last_question
	if(len(options) != 3):
		return False
	options_same = True
	for x in range (0,3):
		if last_options[x] != options[x]:
			options_same = False
	if options_same and last_question == question:
		return False
	return True

# return points for live game // by screenshot
def get_points_live():
	global last_options,last_question
	neg= False
	question,options=parse_question()
	if different_valid_ocr(question,options):
		last_options = options
		last_question = question
		points = []
		neg = get_neg(question)
		maxo=""
		m=1
		if neg:
			m=-1
		print("\n" + bcolors.UNDERLINE + question + bcolors.ENDC + "\n")
		#open up url in threads

		urls = [
		   question + ' wiki',
		   options[0] + 'wiki',
		   options[1] + 'wiki',
		   options[2] + 'wiki',
		   question,
		   question + ' ' + options[0],
		   question + ' ' + options[1],
		   question + ' ' + options[2]
		  ]
		pool = ThreadPool(4)
		# open the urls in their own threads
		# and return the results
		results = pool.starmap(search, zip(urls))
		# close the pool and wait for the work to finish
		pool.close()
		pool.join()
		printer(question,options,neg,results,0)
		printer(question,options,neg,results,1)
		printer(question,options,neg,results,2)
		printer(question,options,neg,results,3)


def get_html(url):
	ua = UserAgent()
	header = ua.random
	try:
		return requests.get(url).text
	except urllib.error.HTTPError as e:
		print("Error accessing:", url)
		print(e)
	except Exception as e:
		print(e)
		print("Error accessing:", url)
		return None

def _get_search_url(query):
	# note: num per page might not be supported by google anymore (because of
	# google instant)

	params = {'nl': 'en', 'q': query.encode(
		'utf8')}

	params = urlencode(params)

	https = int(time.time()) % 2 == 0
	bare_url = u"https://www.google.co.uk/search?" if https else u"http://www.google.co.uk/search?"
	url = bare_url + params
	# return u"http://www.google.com/search?hl=%s&q=%s&start=%i&num=%i" %
	# (lang, normalize_query(query), page * per_page, per_page)
	return url

def search(query):
	url = _get_search_url(query)
	html = get_html(url)
	soup = BeautifulSoup(html, "html.parser")
	divs = soup.findAll("div", attrs={"class": "g"})
	for li in divs:
		result = _get_link(li)
		if result != None:
			return result,get_page(result)

def link_good(o):
	if o.netloc and 'google' not in o.netloc and 'youtube' not in o.netloc and 'ppt' not in o.path and 'pdf' not in o.path:
			return True
	return False
	
def _filter_link(link):
	'''Filter links found in the Google result pages HTML code.
	Returns None if the link doesn't yield a valid result.
	'''
	try:
		# Valid results are absolute URLs not pointing to a Google domain
		# like images.google.com or googleusercontent.com
		o = urlparse(link, 'http')
		# link type-1
		# >>> "https://www.gitbook.com/book/ljalphabeta/python-"
		if link_good(o):
			return link
		# link type-2
		# >>> "http://www.google.com/url?url=http://python.jobbole.com/84108/&rct=j&frm=1&q=&esrc=s&sa=U&ved=0ahUKEwj3quDH-Y7UAhWG6oMKHdQ-BQMQFggUMAA&usg=AFQjCNHPws5Buru5Z71wooRLHT6mpvnZlA"
		if o.netloc and o.path.startswith('/url'):
			try:
				link = parse_qs(o.query)['url'][0]
				o = urlparse(link, 'http')
				if link_good(o):
					return link
			except KeyError:
				pass
		# Decode hidden URLs.
		if link.startswith('/url?'):
			try:
				# link type-3
				# >>> "/url?q=http://python.jobbole.com/84108/&sa=U&ved=0ahUKEwjFw6Txg4_UAhVI5IMKHfqVAykQFggUMAA&usg=AFQjCNFOTLpmpfqctpIn0sAfaj5U5gAU9A"
				link = parse_qs(o.query)['q'][0]
				# Valid results are absolute URLs not pointing to a Google domain
				# like images.google.com or googleusercontent.com
				o = urlparse(link, 'http')
				if link_good(o):
					return link
			except KeyError:
				# link type-4
				# >>> "/url?url=https://machine-learning-python.kspax.io/&rct=j&frm=1&q=&esrc=s&sa=U&ved=0ahUKEwj3quDH-Y7UAhWG6oMKHdQ-BQMQFggfMAI&usg=AFQjCNEfkUI0RP_RlwD3eI22rSfqbYM_nA"
				link = parse_qs(o.query)['url'][0]
				o = urlparse(link, 'http')
				if link_good(o):
					return link

	# Otherwise, or on error, return None.
	except Exception:
		pass
	return None

def _get_link(li):
	"""Return external link from a search."""
	a = li.find("a")
	link = a["href"]
	return _filter_link(link)


def printer(question, options, neg, results, solverID):
	m = 1
	if neg:
		m=-1
	if solverID == 0:
		print("Searching " + str(results[0][0]))
		points,maxo,sig = google_ques(question.lower(), options, neg, results[0])
		print(sig)
		for point, option in zip(points, options):
			if maxo == option.lower():
				option=bcolors.OKGREEN+option+bcolors.ENDC
			print(option + " { points: " + bcolors.BOLD + str(point*m) + bcolors.ENDC + " }")
		print('\n')
	elif solverID == 1:
		print("Searching " + str(results[4][0]))
		points,maxo,sig = google_ques(question.lower(), options, neg, results[4])
		print(sig)
		for point, option in zip(points, options):
			if maxo == option.lower():
				option=bcolors.OKGREEN+option+bcolors.ENDC
			print(option + " { points: " + bcolors.BOLD + str(point*m) + bcolors.ENDC + " }")
		print('\n')
	elif solverID == 2:
		print("Googling Answer + wiki")
		points,maxo,sig = google_ans_wiki(question.lower(), options, neg, [results[1][1],results[2][1],results[3][1]])
		print(sig)
		count = 1
		for point, option in zip(points, options):
			print("Searching " + str(results[count][0]))
			count += 1
			if maxo == option.lower():
				option=bcolors.OKGREEN+option+bcolors.ENDC
			print(option + " { points: " + bcolors.BOLD + str(point*m) + bcolors.ENDC + " }")
		print('\n')
	elif solverID == 3:
		print("Googling Question + Answer")
		count = 5
		points,maxo,sig = google_quesans(question.lower(), options, neg, [results[5][1],results[6][1],results[7][1]])
		print(sig)
		for point, option in zip(points, options):
			print("Searching " + str(results[count][0]))
			count += 1
			if maxo == option.lower():
				option=bcolors.OKGREEN+option+bcolors.ENDC
			print(option + " { points: " + bcolors.BOLD + str(point*m) + bcolors.ENDC + " }")
		print('\n')

'''
# menu// main func
if __name__ == "__main__":
	load_json()
	while(1):
		get_points_live()

'''

if __name__ == "__main__":
	load_json()
	neg= False
	question = "Which 80s song begins, 'Bass, how low can you go?'"
	question = removeIV(question)
	options = ["My Adidas","Push it","Bring the Noise"]
	neg= False
	if different_valid_ocr(question,options):
		last_options = options
		last_question = question
		points = []
		neg = get_neg(question)
		maxo=""
		m=1
		if neg:
			m=-1
		print("\n" + bcolors.UNDERLINE + question + bcolors.ENDC + "\n")
		#open up url in threads

		urls = [
		   question + ' wiki',
		   options[0] + 'wiki',
		   options[1] + 'wiki',
		   options[2] + 'wiki',
		   question,
		   question + ' ' + options[0],
		   question + ' ' + options[1],
		   question + ' ' + options[2]
		  ]
		pool = ThreadPool(8)
		# open the urls in their own threads
		# and return the results
		results = pool.starmap(search, zip(urls))
		# close the pool and wait for the work to finish
		pool.close()
		pool.join()
		printer(question,options,neg,results,0)
		printer(question,options,neg,results,1)
		printer(question,options,neg,results,2)
		printer(question,options,neg,results,3)
