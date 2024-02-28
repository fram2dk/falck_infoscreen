#!/usr/bin/python3
import json
import os
from dotenv import load_dotenv
from queue import Queue
import threading

from helperfunctions import *
from gui import threadGui
from mqtt import threadMqtt

load_dotenv()
mqttdata = json.loads(os.getenv('MQTTDATA'))
version = '240223a'
# begin code
#987
que = Queue(maxsize = 3)

if __name__ == "__main__":
    guit = threading.Thread(target=threadGui, args=('gui',que), kwargs={'incidenttopic':str(mqttdata['topic']),'swversion':version})
    guit.start()
    mqttc = threading.Thread(target=threadMqtt, args=('mqttserver',que))
    mqttc.start()


