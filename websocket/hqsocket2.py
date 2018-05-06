from websocket import create_connection
conn = create_connection('wss://ws-quiz.hype.space')
result = conn.recv()
print(result)
