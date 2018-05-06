import csv
import json
with open('question_answers.csv', 'r') as csvfile:
	csvreader = csv.reader(csvfile, delimiter=',', quotechar='\"')
	csvtext = []
	next(csvreader)
	for row in csvreader:
		coltext = []
		for col in row:
			coltext.append(col)
		csvtext.append(coltext)
	for x in range(0, len(csvtext),3):
		question = csvtext[x][0]
		answer1 = csvtext[x][1]
		answer2 = csvtext[x+1][1]
		answer3 = csvtext[x+2][1]
		print(question)
		print(answer1)
		print(answer2)
		print(answer3)
		d = {"type": "question", "ts": "2017-12-28T20:09:42.040Z", "totalTimeMs": 10000, "timeLeftMs": 10000, "questionId": 20005, "question": question, "category": "Literature", "answers": [ { "answerId": 52360, "text": answer1 }, { "answerId": 52361, "text": answer2 }, { "answerId": 52362, "text": answer3 } ], "questionNumber": 7, "questionCount": 12, "sent": "2017-12-28T20:09:42.073Z"}
		with open('question' + str(int((x + 3)/3)	) + '.json', 'w') as fp:
			json.dump(d, fp)
  
