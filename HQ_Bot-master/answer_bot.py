'''

	TODO:
	* Implement normalize func
	* Attempt to google wiki \"...\" part of question
	* Rid of common appearances in 3 options
	* Automate screenshot process
	* Implement Asynchio for concurrency

	//Script is in working condition at all times
	//TODO is for improving accuracy

'''

# answering bot for trivia HQ and Cash Show
import json
import urllib.request as urllib2
from bs4 import BeautifulSoup
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
import math

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

# GUI interface 
def gui_interface():
	app = wx.App()
	frame = wx.Frame(None, -1, 'win.py')
	frame.SetDimensions(0,0,640,480)
	frame.Show()
	app.MainLoop()
	return None

def load_json():
	global remove_words, sample_questions, negative_words
	remove_words = json.loads(open("Data/settings.json",encoding="utf8").read())["remove_words"]
	negative_words = json.loads(open("Data/settings.json",encoding="utf8").read())["negative_words"]
# simplify question and remove which,what....etc //question is string
def simplify_ques(question):
	neg=False
	qwords = question.lower().split()
	if [i for i in qwords if i in negative_words]:
		neg=True
	cleanwords = [word for word in qwords if word.lower() not in remove_words]
	temp = ' '.join(cleanwords)
	clean_question=""
	#remove ?
	for ch in temp: 
		if ch!="?" or ch!="\"" or ch!="\'":
			clean_question=clean_question+ch

	return clean_question.lower(),neg


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

# normalize points // get rid of common appearances // "quote" wiki option + ques
def normalize():
	return None	

# wait for certain milli seconds 
def wait(msec):
	return None

# answer by combining two words
def smart_answer(content,qwords):
	zipped= zip(qwords,qwords[1:])
	points=0
	for el in zipped :
		if content.count(el[0]+" "+el[1])!=0 :
			points+=1000
	return points

# use google to get wiki page
def google_wiki(sim_ques, options, neg):
	spinner = Halo(text='Googling and searching Wikipedia', spinner='dots2')
	spinner.start()
	num_pages = 1
	points = list()
	content = ""
	maxo=""
	maxp=-sys.maxsize
	words = split_string(sim_ques)
	for o in options:
		
		o = o.lower()
		original=o
		o += ' wiki'

		# get google search results for option + 'wiki'
		search_wiki = google.search(o, num_pages)

		link = search_wiki[0].link
		content = get_page(link)
		soup = BeautifulSoup(content,"lxml")
		page = soup.get_text().lower()

		temp=0

		for word in words:
			temp = temp + page.count(word)
		temp+=smart_answer(page, words)
		if neg:
			temp*=-1
		points.append(temp)
		if temp>maxp:
			maxp=temp
			maxo=original
	spinner.succeed()
	spinner.stop()
	return points,maxo

def get_points_question(number_of_bots,bot_or_user):
	hq_question_json = json.loads(open("Data/question.json", encoding="utf8").read())
	hq_question = hq_question_json['question']
	simq, neg = simplify_ques(hq_question)
	options = []
	for x in range(0, 3):
		options.append(hq_question_json['answers'][x]['text'])
	simq = simq.lower()
	print(options)
	print(simq)
	print(neg)
	maxo=""
	points, maxo = google_wiki(simq, options,neg)
	if bot_or_user == "user":
		for x in range(0, 3):
			if maxo == options[x].lower():
				option=bcolors.OKGREEN+options[x]+bcolors.ENDC
			print(options[x] + " { points: " + bcolors.BOLD + str(points[x]) + bcolors.ENDC + " }\n")
	else:
		total_points = 0
		for x in range(0, 3):
			total_points += points[x]
		bots_per_answer = []
		total_bots_allocated = 0
		for x in range(0, 3):
			bots_per_answer.append(math.floor(points[x] / total_points * number_of_bots))
			total_bots_allocated += math.floor(points[x] / total_points * number_of_bots)
		if total_bots_allocated < number_of_bots:
			for x in range(0, 3):
				if maxo == options[x].lower():
					bots_per_answer[x] += number_of_bots - total_bots_allocated
		return bots_per_answer

def get_question_id():
	hq_question_json = json.loads(open("Data/question.json", encoding="utf8").read())
	return hq_question_json['questionId']
	
# menu// main func
if __name__ == "__main__":
	load_json()
	lastq = ""
	while(1):
		if lastq !=  get_question_id():
			bots_per_answer  = get_points_question(10,"user")			
			lastq = get_question_id()
	

