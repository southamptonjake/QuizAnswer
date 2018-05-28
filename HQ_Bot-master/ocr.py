
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
from urllib.parse import urlencode
import time
import urllib.request
from fake_useragent import UserAgent	

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

# load sample questions
def load_json():
	global remove_words, sample_questions, negative_words, driver
	remove_words = json.loads(open("Data/settings.json").read())["remove_words"]
	negative_words = json.loads(open("Data/settings.json").read())["negative_words"]

# take screenshot of question
def screen_grab(to_save):
	# 31,228 485,620 co-ords of screenshot// left side of screen
	im = Imagegrab.grab(bbox=(100,258,485,780))
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
				print(option)
				option_printed = True
			print(el[0] + ' ' + el[1])
			points+=1000
	return points
# get web page
def get_page(link):
	try:
		if link.find('mailto') != -1:
			return ''
		req = urllib2.Request(link, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64)'})
		html = urllib2.urlopen(req).read()
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
	search_wiki = question_search
	link = search_wiki
	content = get_page(link)
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
			
			words = split_string(o)
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
			search_wiki = option_search[x]

			link = search_wiki
			content = get_page(link)
			soup = BeautifulSoup(content,"lxml")
			page = soup.get_text().lower()

			temp=0

			for word in words:
				temp = temp + page.count(' ' + word + ' ')
			temp+=smart_answer(page, words, options[x])
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
			search_wiki = option_search[x]

			link = search_wiki
			content = get_page(link)
			soup = BeautifulSoup(content,"lxml")
			page = soup.get_text().lower()

			temp=0

			for word in words:
				temp = temp + page.count(' ' + word + ' ')
			temp+=smart_answer(page, words, options[x])
			temp+=page.count(' ' + options[x] + ' ') * 3000
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
		results = pool.starmap(google.search, zip(urls,itertools.repeat(1)))
		# close the pool and wait for the work to finish
		pool.close()
		pool.join()
		print("Searching " + str(results[0]))
		points,maxo,sig = google_ques(question.lower(), options, neg, results[0])
		print(sig)
		for point, option in zip(points, options):
			if maxo == option.lower():
				option=bcolors.OKGREEN+option+bcolors.ENDC
			print(option + " { points: " + bcolors.BOLD + str(point*m) + bcolors.ENDC + " }")
		print('\n')
		print("Searching " + str(results[4]))
		points,maxo,sig = google_ques(question.lower(), options, neg, results[4])
		print(sig)
		for point, option in zip(points, options):
			if maxo == option.lower():
				option=bcolors.OKGREEN+option+bcolors.ENDC
			print(option + " { points: " + bcolors.BOLD + str(point*m) + bcolors.ENDC + " }")
		print('\n')
		print("Googling Answer + wiki")
		points,maxo,sig = google_ans_wiki(question.lower(), options, neg, [results[1],results[2],results[3]])
		print(sig)
		count = 1
		for point, option in zip(points, options):
			print("Searching " + str(results[count]))
			count += 1
			if maxo == option.lower():
				option=bcolors.OKGREEN+option+bcolors.ENDC
			print(option + " { points: " + bcolors.BOLD + str(point*m) + bcolors.ENDC + " }")
		print('\n')
		print("Googling Question + Answer")
		count = 5
		points,maxo,sig = google_quesans(question.lower(), options, neg, [results[5],results[6],results[7]])
		print(sig)
		for point, option in zip(points, options):
			print("Searching " + str(results[count]))
			count += 1
			if maxo == option.lower():
				option=bcolors.OKGREEN+option+bcolors.ENDC
			print(option + " { points: " + bcolors.BOLD + str(point*m) + bcolors.ENDC + " }")
		print('\n')

	
def get_html(url):
    ua = UserAgent()
    header = ua.random
    try:
        request = urllib.request.Request(url)
        request.add_header("User-Agent", header)
        html = urllib.request.urlopen(request).read()
        return html
    except urllib.error.HTTPError as e:
        print("Error accessing:", url)
        print(e)
    except Exception as e:
        print(e)
        print("Error accessing:", url)
        return None	
		
def _get_search_url(query, page=0, per_page=10, lang='en', area='co.uk', ncr=False):
    # note: num per page might not be supported by google anymore (because of
    # google instant)

    params = {'nl': lang, 'q': query.encode(
        'utf8'), 'start': page * per_page, 'num': per_page }

    params = urlencode(params)

    https = int(time.time()) % 2 == 0
    bare_url = u"https://www.google.co.uk/search?" if https else u"http://www.google.co.uk/search?"
    url = bare_url + params
    # return u"http://www.google.com/search?hl=%s&q=%s&start=%i&num=%i" %
    # (lang, normalize_query(query), page * per_page, per_page)    
    return url

def search(query, pages=1, lang='en', area='com', ncr=False, void=True):
    """Returns a list of GoogleResult.
    Args:
        query: String to search in google.
        pages: Number of pages where results must be taken.
        area : Area of google homepages.
    TODO: add support to get the google results.
    Returns:
        A GoogleResult object."""
    results = []
    for i in range(pages):
        url = _get_search_url(query, i, lang=lang, area=area, ncr=ncr)
        html = get_html(url)
        soup = BeautifulSoup(html, "html.parser")
        div = soup.find("div", attrs={"class": "g"})
        return _get_google_link(div)

def _get_google_link(li):
    """Return google link from a search."""
    try:
        a = li.find("a")
        link = a["href"]
        return link
    except Exception:
        return None

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
	question = " Which of these musicals has had the most Broadway performances?"
	question = removeIV(question)
	options = ["The Lion King","The Phantom of the Opera","Cats"]
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
		pool = ThreadPool(4)
		# open the urls in their own threads
		# and return the results
		results = pool.starmap(search, zip(urls,itertools.repeat(1)))
		print(time)
		# close the pool and wait for the work to finish
		pool.close()
		pool.join()
		print("Searching " + str(results[0]))
		points,maxo,sig = google_ques(question.lower(), options, neg, results[0])
		print(sig)
		for point, option in zip(points, options):
			if maxo == option.lower():
				option=bcolors.OKGREEN+option+bcolors.ENDC
			print(option + " { points: " + bcolors.BOLD + str(point*m) + bcolors.ENDC + " }")
		print('\n')
		print("Searching " + str(results[4]))
		points,maxo,sig = google_ques(question.lower(), options, neg, results[4])
		print(sig)
		for point, option in zip(points, options):
			if maxo == option.lower():
				option=bcolors.OKGREEN+option+bcolors.ENDC
			print(option + " { points: " + bcolors.BOLD + str(point*m) + bcolors.ENDC + " }")
		print('\n')
		print("Googling Answer + wiki")
		points,maxo,sig = google_ans_wiki(question.lower(), options, neg, [results[1],results[2],results[3]])
		print(sig)
		count = 1
		for point, option in zip(points, options):
			print("Searching " + str(results[count]))
			count += 1
			if maxo == option.lower():
				option=bcolors.OKGREEN+option+bcolors.ENDC
			print(option + " { points: " + bcolors.BOLD + str(point*m) + bcolors.ENDC + " }")
		print('\n')
		print("Googling Question + Answer")
		count = 5
		points,maxo,sig = google_quesans(question.lower(), options, neg, [results[5],results[6],results[7]])
		print(sig)
		for point, option in zip(points, options):
			print("Searching " + str(results[count]))
			count += 1
			if maxo == option.lower():
				option=bcolors.OKGREEN+option+bcolors.ENDC
			print(option + " { points: " + bcolors.BOLD + str(point*m) + bcolors.ENDC + " }")
		print('\n')
	
