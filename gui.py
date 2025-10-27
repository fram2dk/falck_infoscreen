#!/usr/bin/python3
import tkinter as tk
import screeninfo
import os
#import tksvg
import json
#from PIL import Image, ImageTk
#from PIL import ImageGrab
import pyscreenshot as ImageGrab
from datetime import datetime,timedelta
import time
import logging
from queue import Queue

from helperfunctions import Incidents,ThreadState

gui_logger = logging.getLogger(__name__)
gui_logger.setLevel(logging.INFO)

def threadGui(name,que: Queue,statusque: Queue,monitorque: Queue, incidenttopic='',swversion='.,.',instanceid='ABC'):
    ## gui
    incidentsObj = Incidents()
    window = tk.Tk()
    monitors = screeninfo.get_monitors()
    if len(monitors) > 1:
      gui_logger.debug(str(monitors[1]))
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
    if ws>hs:
      w = h*2
    window.geometry('%dx%d+%d+%d' % (w, h, x, y))
    gui_logger.debug("screen:"+str(w)+"x"+str(h)+" x="+str(x)+",y="+str(y))
    #Set the Title of Tkinter window
    window.title(str(os.getenv('STATIONNAME'))+' (v'+str(swversion)+')')
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
    def drawStates(states):
      #stressurCanvasText = window.create_text(10, 20, fill=textcolor,text='test234',anchor="w", font=("Arial", int(30)))
      #statelabel = tk.Label(window, textvariable = "test123",font=("Arial", int(60)))
      appStateCanvas = tk.Frame(window)
      #print(datetime.now().timestamp() )
      if (int(str(datetime.now().timestamp()).replace('.','0')[-4]) % 2) == 0:
        ticktxt = tk.Label(appStateCanvas, text = str('|')[0].upper(),fg='#AAA',font=("Arial", int(8)))
       
      else:
        ticktxt = tk.Label(appStateCanvas, text = str(':'),fg='#FFF',font=("Arial", int(8)))
      ticktxt.pack(side = tk.LEFT)
      for appname,appstate in states.items():
 
        if appstate == ThreadState.CONNECTING:
          textcolor = '#000'
        elif appstate == ThreadState.CONNECTED:
          textcolor = '#0F0'
        elif appstate == ThreadState.INCONCLUSIVE:
          textcolor = '#00F'  
        elif appstate == ThreadState.DISCONNECTED:
          textcolor = '#F00'
        else:
          textcolor = '#DDD'
        tmptxt = tk.Label(appStateCanvas, text = str(appname)[0].upper(),fg=textcolor,font=("Arial", int(14)))
        tmptxt.pack(side = tk.LEFT)
     #   appStateCanvas.create_text(10, 20, fill=textcolor,text=str(appname)[0].upper(),anchor="w", font=("Arial", int(textsize)))
     # stressurCanvasText = self.stressurCanvas.create_text(10, 20, fill=textcolor,text='_',anchor="w", font=("Arial", int(textsize)))
      appStateCanvas.place(x=1,y=1)
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
    def timerInterrupt():
       #global window
       statechanged = incidentsObj.updateure()
       if statechanged:
          clearFrame()
          incidentsObj.update_incidents(window)
          statusque.put({"Incident states":incidentsObj.getStates()})
          print('statusque apppended')

       if int(datetime.now().timestamp()) % 60 == 0:
         print('will make screenshot')
         #widgetsize = (window.winfo_rootx(),window.winfo_rooty(),window.winfo_rootx()+window.winfo_width(),window.winfo_rooty()+window.winfo_height())
         #im = ImageGrab.grab()
         #im.save('screen'+str(int(datetime.now().timestamp()))[:5]+'.png')
         #time.sleep(1)
       window.after(200, timerInterrupt)
       window.update()        
         
    def checkque():
        nonlocal lastMesTime
        nonlocal lastMes
        while not que.empty():
           messageRaw = que.get()
           if 'mqtt' in messageRaw.keys():
             message = messageRaw['mqtt']['message']
             topic = messageRaw['mqtt']['topic']
             if len(message) < 10:
                gui_logger.debug('no more to display')
                window.withdraw()
             elif isinstance(message,bytes) and message != lastMes:
                pngheader = b"\x89\x50\x4E\x47\x0D\x0A"
                if message[:6] == pngheader:
                  gui_logger.debug('valid png image')
                  drawImage(pngdata=message)
                else:
                  gui_logger.info('recieved incident:'+str(message.decode('utf-8'))+' '+str(topic))
                  if topic == incidenttopic:
                    incidents = None
                    try:
                      incidents = json.loads(message.decode('utf-8'))
                      gui_logger.info("there were "+str(len(incidents))+" incidents in the message")
                    except:
                      gui_logger.warn('activeincident was invalid json')
                    
                    if incidents is not None:
                      clearFrame()
                      incidentsObj.update_incidents(window,newIncidents=incidents)
                      #gui_logger.debug("Incident states: "+str(incidentsObj))
                      statusque.put({"reason":"received some incidents","incidentstates":incidentsObj.getStates()})
                    else:
                      gui_logger.debug("Incidents was not update")
             lastMesTime = datetime.now()
             lastMes = message
           if 'states' in messageRaw.keys():
             if isinstance(messageRaw['states'],dict):
               drawStates(messageRaw['states'])
               #print('from gui: '+str(messageRaw['states'])) 
             else:
               print(type(messageRaw['states']))
           if 'init' in messageRaw.keys():
             if messageRaw['init']:  
               incidentsObj.__init__() #reset all incidents
               pass
        window.update()                
           
        if lastMesTime+timedelta(minutes=30)<datetime.now():
           gui_logger.info('no update received for a long time')
           clearFrame()
           incidentsObj.update_incidents(window)
           statusque.put({"reason":"no update received for a long time","incidentstates":incidentsObj.getStates()})
           window.update()
           lastMesTime = datetime.now()
        monitorque.put({'name':name,'state':'connected'})
        window.after(2000, checkque)
    timerInterrupt()
    checkque()
    
    window.mainloop()

    
    #while True:
        
        #statechanged = incidentsObj.updateure()
        #window.after(200, incidentsObj.updateure())
        #if statechanged:
        #  clearFrame()
        #  incidentsObj.update_incidents(window)
        #window.update()
        ##time.sleep(1.5)
        #window.mainloop()


      
"""
t1 = Queue()      
t2 = threadGui("test",t1)
print(t2)
"""


