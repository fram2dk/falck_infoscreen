#!/usr/bin/python3
import json
import os
from dotenv import load_dotenv
from queue import Queue
import threading
import logging
import sys
import time

from helperfunctions import *
from gui import threadGui
from mqtt import threadMqtt

# create formatter and add it to the handler
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')


# create and configure main logger
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)
# create console handler with a higher log level
handler = logging.StreamHandler()
handler.setLevel(logging.DEBUG)
handler.setFormatter(formatter)
logger.addHandler(handler)

# add the file handler to the logger
filehandler = logging.FileHandler("errors.log", mode='a')
filehandler.setLevel(logging.WARN)
filehandler.setFormatter(formatter)
logger.addHandler(filehandler)

version = '050324a'
allok = True

def handle_exception(exc_type, exc_value, exc_traceback):
   global allok
   # if issubclass(exc_type, KeyboardInterrupt):
   #     sys.__excepthook__(exc_type, exc_value, exc_traceback)
   #     return
   logger.error("Uncaught exception", exc_info=(exc_type, exc_value, exc_traceback))
   allok = False

def treads_exception(args):
    global allok
    # report the failure
    logger.error("Uncaught exception from thread: ", exc_info=(args.exc_type, args.exc_value, args.exc_traceback))
    #print(f'Thread failed: {args.exc_value}')
    allok = False
    
sys.excepthook = handle_exception
threading.excepthook = treads_exception

load_dotenv()
mqttdata = json.loads(os.getenv('MQTTDATA'))
que = Queue(maxsize = 3)

if __name__ == "__main__":
    guit = threading.Thread(target=threadGui,daemon=True, args=('gui',que), kwargs={'incidenttopic':str(mqttdata['topic']),'swversion':version})
    guit.start()
    mqttc = threading.Thread(target=threadMqtt,daemon=True, args=('mqttserver',que))
    mqttc.start()
while allok:
  time.sleep(10)

