
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
import wx
from halo import Halo
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

# GUI interface
def gui_interface():
	app = wx.App()
	frame = wx.Frame(None, -1, 'win.py')
	frame.SetDimensions(0,0,640,480)
	frame.Show()
	app.MainLoop()
	return None

# load sample questions
def load_json():
	global remove_words, sample_questions, negative_words, driver
	remove_words = json.loads(open("Data/settings.json").read())["remove_words"]
	negative_words = json.loads(open("Data/settings.json").read())["negative_words"]
	driver = webdriver.Firefox(executable_path=r'C:\Users\JakeL\Pictures\geckodriver-v0.20.1-win64\geckodriver.exe')

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

	return question, options

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

def smart_answer(content,qwords):
	zipped= zip(qwords,qwords[1:])
	points=0
	for el in zipped :
		if content.count(el[0]+" "+el[1])!=0 :
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
	link = search_wiki[0].link
	content = get_page(link)
	soup = BeautifulSoup(content,"lxml")
	page = soup.get_text().lower()

	for o in options:
		o = o.lower()
		temp=0
		temp = temp + ((page.count(' ' + o + ' ')) * 1000)
		words = split_string(o)
		for word in words:
			temp = temp + (page.count(' ' + word + ' '))
		if neg:
			temp*=-1
		temp = temp / len(page)
		points.append(temp)
		if temp>maxp:
			maxp=temp
			maxo=o
	return normalise(points),maxo

def google_ans_wiki(ques, options, neg, option_search):
	sim_ques = simplify_ques(ques)
	num_pages = 1
	points = list()
	content = ""
	maxo=""
	maxp=-sys.maxsize
	words = split_string(sim_ques)
	for x in range(0,3) :
		o = options[x]
		o = o.lower()
		original=o
		# get google search results for option + 'wiki'
		search_wiki = option_search[x]

		link = search_wiki[0].link
		content = get_page(link)
		soup = BeautifulSoup(content,"lxml")
		page = soup.get_text().lower()

		temp=0

		for word in words:
			temp = temp + page.count(' ' + word + ' ')
		temp+=smart_answer(page, words)
		if neg:
			temp*=-1
		temp = temp / len(page)
		points.append(temp)
		if temp>maxp:
			maxp=temp
			maxo=original
	return normalise(points),maxo
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
	return normalise(points),maxo

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
		   question
		  ]
		pool = ThreadPool(4)
		# open the urls in their own threads
		# and return the results
		results = pool.starmap(google.search, zip(urls,itertools.repeat(1)))
		# close the pool and wait for the work to finish
		pool.close()
		pool.join()
		try:
			print("Searching " + str(results[0][0].link))
			points,maxo = google_ques(question.lower(), options, neg, results[0])
			for point, option in zip(points, options):
				if maxo == option.lower():
					option=bcolors.OKGREEN+option+bcolors.ENDC
				print(option + " { points: " + bcolors.BOLD + str(point*m) + bcolors.ENDC + " }")
		except Exception as inst:
			print(inst)
			print("No Results Found")
		print('\n')
		try:
			print("Searching " + str(results[4][0].link))
			points,maxo = google_ques(question.lower(), options, neg, results[4])
			for point, option in zip(points, options):
				if maxo == option.lower():
					option=bcolors.OKGREEN+option+bcolors.ENDC
				print(option + " { points: " + bcolors.BOLD + str(point*m) + bcolors.ENDC + " }")
		except Exception as inst:
			print(inst)
			print("No Results Found")
		print('\n')
		try:
			print("Googling Answer + wiki")
			points,maxo = google_ans_wiki(question.lower(), options, neg, [results[1],results[2],results[3]])
			for point, option in zip(points, options):
				if maxo == option.lower():
					option=bcolors.OKGREEN+option+bcolors.ENDC
				print(option + " { points: " + bcolors.BOLD + str(point*m) + bcolors.ENDC + " }")
		except Exception as inst:
			print(inst)
			print("No Results Found")
		print('\n')
		try:
			print("Googling Question + Answer")
			points,maxo = google_ques_ans(question.lower(), options, neg)
			for point, option in zip(points, options):
				if maxo == option.lower():
					option=bcolors.OKGREEN+option+bcolors.ENDC
				print(option + " { points: " + bcolors.BOLD + str(point*m) + bcolors.ENDC + " }")
		except Exception as inst:
			print(inst)
			print("No Results Found")

# menu// main func
if __name__ == "__main__":
	load_json()
	while(1):
		try:
			get_points_live()
		except IndexError:
			print("failed")
