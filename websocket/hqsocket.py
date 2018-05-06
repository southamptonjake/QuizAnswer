import websocket
import time
import requests
import urllib
import threading
###########################################################################
# configuration
###########################################################################
url      = 'ws://ws-quiz.hype.space'
token = 'Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VySWQiOjE2OTA0Mzk2LCJ1c2VybmFtZSI6IkdyZWVkTGFiZWxsZSIsImF2YXRhclVybCI6InMzOi8vaHlwZXNwYWNlLXF1aXovZGVmYXVsdF9hdmF0YXJzL1VudGl0bGVkLTFfMDAwM19yZWQucG5nIiwidG9rZW4iOiJhWWhSeXgiLCJyb2xlcyI6W10sImNsaWVudCI6IiIsImd1ZXN0SWQiOm51bGwsInYiOjEsImlhdCI6MTUyNTQ0OTczOSwiZXhwIjoxNTMzMjI1NzM5LCJpc3MiOiJoeXBlcXVpei8xIn0.m4mLovGgkeRi5-O8_YaHHwd5rAqNnpN2vgRfoESkHpE'

# Websocket connection
######################
def on_message(ws, message):
    print (message)

def on_error(ws, error):
    print (error)

def on_close(ws):
    print ("### closed ###")

def on_open(ws):
    def run(*args):
        while True:
            time.sleep(1)
        ws.close()
        print ("thread terminating...")	
    thread.start_new_thread(run, ())

if __name__ == "__main__":
    websocket.enableTrace(True)
    ws = websocket.WebSocketApp(url,
                              on_message = on_message,
                              on_error   = on_error,
                              on_close   = on_close,
                              header     = {"token: aYhRyx"}
                              )
    ws.on_open = on_open
    ws.run_forever()
