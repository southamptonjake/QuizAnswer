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
from google.cloud import language
from google.cloud.language import enums
from google.cloud.language import types

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
	global remove_words, negative_words
	remove_words = json.loads(open("Data/settings.json").read())["remove_words"]
	negative_words = json.loads(open("Data/settings.json").read())["negative_words"]
	
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
	
def entities_text(text):
    """Detects entities in the text."""
    client = language.LanguageServiceClient()		
    # Instantiates a plain text document.
    document = types.Document(content=text,type=enums.Document.Type.PLAIN_TEXT)
    # Detects entities in the document
    entities = client.analyze_entities(document).entities
    # entity types from enums.Entity.Type
    entity_type=('UNKNOWN', 'PERSON', 'LOCATION', 'ORGANIZATION','EVENT', 'WORK_OF_ART', 'CONSUMER_GOOD', 'OTHER')
    name_salience = {}
    for entity in entities:
        name_salience[entity.name] = entity.salience
    return name_salience
	
# use google to get wiki page
def google_wiki(ques, options, neg, sal):
	spinner = Halo(text='Googling and searching Wikipedia', spinner='dots2')
	spinner.start()
	num_pages = 1
	points = list()
	content = ""
	maxo=""
	maxp=-sys.maxsize
	words = split_string(ques)
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
			try:
				sal[word]
				temp = temp + page.count(word)
			except:
				temp = temp
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
	
# use google to get wiki page
def google_wiki2(ques, options, neg):
	spinner = Halo(text='Googling and searching Wikipedia', spinner='dots2')
	spinner.start()
	num_pages = 1
	points = list()
	content = ""
	maxo=""
	maxp=-sys.maxsize
	print(ques)
	search_wiki = google.search(ques + ' wiki', num_pages)
	link = search_wiki[0].link
	print(link)
	content = get_page(link)
	soup = BeautifulSoup(content,"lxml")
	page = soup.get_text().lower()
	
	for o in options:
		o = o.lower()
		temp=0
		temp = temp + ((page.count(o)) * 1000)
		words = split_string(o)
		for word in words:
			temp = temp + (page.count(word))
		if neg:
			temp*=-1
		points.append(temp)
		if temp>maxp:
			maxp=temp
			maxo=o
	spinner.succeed()
	spinner.stop()
	return points,maxo

def get_points_question(questionNumber):
	hq_question_json = json.loads(open("Data/question" + str(questionNumber) + ".json", encoding="utf8").read())
	hq_question = hq_question_json['question']
	simq, neg = simplify_ques(hq_question)
	options = []
	for x in range(0, 3):
		options.append(hq_question_json['answers'][x]['text'])
	simq = simq.lower()
	maxo=""
	#points, maxo = google_wiki(simq, options,neg,entities_text(hq_question))
	points, maxo = google_wiki2(hq_question, options,neg)
	for x in range(0, 3):
		if maxo == options[x].lower():
			option=bcolors.OKGREEN+options[x]+bcolors.ENDC
		print(options[x] + " { points: " + bcolors.BOLD + str(points[x]) + bcolors.ENDC + " }\n")

def get_question_id():
	hq_question_json = json.loads(open("Data/question.json", encoding="utf8").read())
	return hq_question_json['questionId']
	
# menu// main func
if __name__ == "__main__":
	load_json()
	lastq = ""
	while(1):
		if lastq !=  get_question_id():
			bots_per_answer  = get_points_question(10,"bot")			
			lastq = get_question_id()
	

