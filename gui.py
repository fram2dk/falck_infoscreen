#!/usr/bin/python3
import tkinter as tk
import screeninfo
import os
import tksvg
import json
from PIL import Image, ImageTk
from datetime import datetime,timedelta
import time
from queue import Queue

from helperfunctions import Incidents

def threadGui(name,que: Queue, incidenttopic=''):
    ## gui
    incidentsObj = Incidents()
    window = tk.Tk()
    monitors = screeninfo.get_monitors()
    if len(monitors) > 1:
      print(monitors[1])
      ws = monitors[1].width
      hs = monitors[1].height
      w = ws-7
      h = hs
      x = monitors[1].x+1
      y = monitors[1].y
    else:
      ws = window.winfo_screenwidth() # width of the screen
      hs = window.winfo_screenheight() # height of the screen
      w = ws/3 # width for the Tk root
      h = hs # height for the Tk root
      # calculate x and y coordinates for the Tk root window
      x = (ws) - (w)
      y = (hs/2) - (h/2)
    window.geometry('%dx%d+%d+%d' % (w, h, x, y))
    print("screen:"+str(w)+"x"+str(h)+" x="+str(x)+",y="+str(y))
    #Set the Title of Tkinter window
    window.title(str(os.getenv('STATIONNAME')))
    def drawImage(pngdata=None):
        clearFrame()
        if pngdata is not None:
            png_image = ImageTk.PhotoImage(data=pngdata,format='png')
            #png_image = ImageTk.PhotoImage(file='cbimage.png')
            label = tk.Label(image=png_image)
        else:
            svg_image = tksvg.SvgImage(file="drawing.svg")
            label = tk.Label(image=svg_image)
        label.pack()
        window.update()
      
      
    def clearFrame():
        # destroy all widgets from frame
        window.deiconify()
        try:
           for widget in window.winfo_children():
                widget.destroy()
        except:
           pass
    lastMesTime = datetime.now()-timedelta(days=1)
    lastMes = b""
    while True:
        if not que.empty():
           messageRaw = que.get()
           message = messageRaw['message']
           topic = messageRaw['topic']
           if len(message) < 10:
              print('no more to display')
              window.withdraw()
           elif isinstance(message,bytes) and message != lastMes:
              pngheader = b"\x89\x50\x4E\x47\x0D\x0A"
              if message[:6] == pngheader:
                print('valid png image')
                drawImage(pngdata=message)
              else:
                print('recieved incident:'+str(message.decode('utf-8'))+' '+str(topic))
                if topic == incidenttopic:
                  incidents = None
                  try:
                    incidents = json.loads(message.decode('utf-8'))

                  except:
                    print('activeincident was invalid json')
                  
                  if incidents is not None:
                    clearFrame()
                    incidentsObj.update_incidents(window,newIncidents=incidents)
                    
                   # print('incidents: '+str(incidents))
                    
                 #   for incident in incidents:
                 #     if len(incidents) <= 1:
                 #       drawIncident(incident)
                 #     else:
                 #       drawIncident(incident,vconstrain=True)
                    window.update()
                
           lastMesTime = datetime.now()
           lastMes = message
        if lastMesTime+timedelta(minutes=30)<datetime.now():
           print('no update recieved for a long time')
           if True: #show clock
             clearFrame()
             incidentsObj.update_incidents(window)
             window.update()
           else:
             window.withdraw()
           lastMesTime = datetime.now()
        statechanged = incidentsObj.updateure()
        if statechanged:
          clearFrame()
          incidentsObj.update_incidents(window)
        window.update()
        time.sleep(0.5)
      # window.mainloop()
      
"""
t1 = Queue()      
t2 = threadGui("test",t1)
print(t2)
"""


