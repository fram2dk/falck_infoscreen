#!/usr/bin/python3
import requests
from enum import Enum
from datetime import datetime,timedelta
from queue import Queue
import logging
import time
from helperfunctions import *

class ThreadMonitor:
  def __init__(self):
    self.threads = {}
    self.logger = logging.getLogger(__name__ + '.TreadMonitor')
    self.logger.setLevel(logging.DEBUG)
    self.newThread('inet',timeout=112)
    self.updateState('inet',ThreadState.CONNECTING)
    self.updateInet()
    
  def updateInet(self):
    if not 'inet' in self.threads.keys():
      self.newThread('inet')
    try:
        response = requests.get("https://dns.google.com", timeout=5)
        self.updateState('inet',ThreadState.CONNECTED)
    except requests.ConnectionError:
        self.updateState('inet',ThreadState.DISCONNECTED)
    
  def newThread(self,name,icon=None,timeout=60):
    self.threads[str(name)] = {'state':ThreadState.INIT, 'timestamp':datetime.now(),'timeout':int(timeout)}
    if icon is not None:
      self.threads[str(name)]['icon'] = str(icon)
  def updateState(self,name,newState):
    if str(name) in self.threads.keys():
      self.threads[str(name)]['timestamp'] = datetime.now()
      self.threads[str(name)]['state'] = newState
      print('State update: '+str(name)+' -> '+str(newState)) 
      return True
    else:
      return False  
      
  def checkStates(self):
    for thname,th in self.threads.items():
      if th['state'] > ThreadState.INIT:
        if th['timestamp']+timedelta(seconds=th['timeout']) < datetime.now():
          if thname == 'inet':
            self.updateInet()
          else:
            self.updateState(thname,ThreadState.DISCONNECTED)
           
  def getStates(self):
    self.checkStates()
    outDict = {}
    for thname,th in self.threads.items():
      outDict[thname] = th['state']
    return outDict





