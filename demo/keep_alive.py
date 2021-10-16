from flask import Flask
from threading import Thread

app = Flask('Barmaid') #Flask je API pro vytváření webserveru

@app.route('/')
def home():
  return "Bot pinged!"

def run():
  app.run(host='0.0.0.0',port=8080) #host=0.0.0.0 je pro externí přístup k serveru

def keep_alive(): #Spuštění na threadu
  t = Thread(target=run)
  t.start()