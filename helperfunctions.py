from enum import Enum
from datetime import datetime,timedelta
import tkinter as tk
import json
import textwrap
import logging
import inspect
from dotenv import load_dotenv
import os
import traceback

try:
  load_dotenv()
  scaling = float(os.getenv('SCALING'))
except:
  scaling = 1
print('scalering'+str(scaling))

class Incidents:
  def __init__(self):
    self.allincidents = {}
    self.initstates = True
    self.displayclock = False
    self.clockstr = None
    self.listActiveIncidents = []
    self.logger = logging.getLogger(__name__ + '.Incidents')
    self.logger.setLevel(logging.DEBUG)
  def updateure(self):
    for incidentid,incidentObj in self.allincidents.items():
      statechanged = incidentObj.updateur()
      if statechanged:
        return True
    if self.displayclock:
      if self.clockstr is not None:
        self.clockstr.set(datetime.now().strftime('%H:%M:%S'))
        #self.logger.debug(inspect.currentframe().f_code.co_name+' - '+str(self.clockstr.get()))
    if self.initstates:
      self.initstates = False
      return True
    
    return False #statechanged
  def update_incidents(self,curWindow,newIncidents=None):
    if newIncidents is not None:
      for incident in newIncidents:
        try:
          if isinstance(incident['payload'],str):
            incidentpayload = json.loads(incident['payload'])
          else:
            incidentpayload = incident['payload']
          if isinstance(incidentpayload,dict):  
            try:  
              if 'id' in incidentpayload:
                newid = incidentpayload['id'] 
                if newid not in self.allincidents.keys():
                  self.allincidents[newid] = self.Incident(newid)
                if newid in self.allincidents.keys():
                  self.allincidents[newid].update(incidentpayload)
            except:
              print("unable to handle incident:"+str(incidentpayload))
          else:
            print("unable to type("+str(type(incident['payload']))+") handle incident:"+str(incident['payload']))
        except:
          print("incd payload invalid on incident:"+str(incident['payload'])+"   "+str(traceback.format_exc()))

          #self.logger.warn("unable to handle incident:"+str(incident))
    #check overall statuses
    stateview = {0:0,1:0,2:0,3:0,4:0,5:0,6:0}
    for incidentid,incidentObj in self.allincidents.items():
       stateview[incidentObj.state.value] += 1
    self.displayclock = False
    if stateview[1] == 0:
      if stateview[2]+stateview[3] <= 2:
        self.displayclock = True
    if self.displayclock:
       if self.clockstr is None:
         self.clockstr = tk.StringVar(curWindow)
       clocklabel = tk.Label(curWindow, textvariable = self.clockstr,font=("Arial", int(160*scaling)))
       clocklabel.pack(fill='x',expand=True)
       
    for incidentid,incidentObj in self.allincidents.items():
       if stateview[1]+stateview[2]+stateview[3] >= 3:
          incidentObj.setConstrain(True)
       else:
          incidentObj.setConstrain(False)
       if incidentObj.rawdict != '' and incidentObj.state != State.OFF:
         incidentObj.drawIncident(curWindow)
    return None

  def getStates(self):
    retstr = []
    if len(self.allincidents.keys()) >= 1:
      for incidentid,incidentObj in self.allincidents.items():
        retstr.append({'incidentid':int(incidentid),'state':incidentObj.state.value})
    return retstr

  def __str__(self):
    retstr = ""
    if len(self.allincidents.keys()) >= 1:
      for incidentid,incidentObj in self.allincidents.items():
        retstr += ","+str(incidentid)+"state:"+str(incidentObj.state.value)
    # toreturn += str(len(self.allincidents.keys()))+"stk. incidents i listen"
    else:
      retstr = "ingen incidents i listen"
    return retstr
    
  class Incident:
    
    def __init__(self, incidentid):
      self.incidentid = incidentid
      self.rawdict = ''
      self.lastupdatetime = datetime.now()
      self.state = State.OFF
      self.constrained = False
      self.drawingFrame = None
      self.stressstr = tk.StringVar()
      self.stressurCanvas = None
      self.stressurCanvasText = None
      self.stressurCanvasBg = None
      self.logger = logging.getLogger(__name__ + '.Incidents.Incident('+str(self.incidentid)+')')
      self.logger.setLevel(logging.DEBUG)
    def setConstrain(self,newvalue):
      self.constrained = bool(newvalue)
    def update(self,newdict):
      self.lastupdatetime = datetime.now()
      if newdict != self.rawdict:
        self.rawdict = newdict
        self.logger.info(inspect.currentframe().f_code.co_name+' - ny melding'+str(self.rawdict))
        return True
      return False
    def updateur(self):
      udkaldTimeWarning = 280 #280
      udkaldTimeExceeded = 300 #300
      udkaldTimeCalling = 600 #600
      udkaldTimeActive =  60*30 #60*30
      udkaldTimeExpired = 3600*2 #3600*12
      stateChanged = False
 
      if isinstance(self.rawdict,dict):
        if 'starttime' in self.rawdict:
          stresstid = datetime.now()-datetime.fromtimestamp(int(self.rawdict['starttime']))+timedelta(seconds=0)
          if self.state == State.OFF:
            if stresstid.total_seconds() <= udkaldTimeCalling:
              self.state = State.CALLING
              stateChanged = True
            elif stresstid.total_seconds() <= udkaldTimeActive:
              self.state = State.ACTIVE
              stateChanged = True
            elif stresstid.total_seconds() <= 3600*24:
              self.state = State.INACTIVE
              stateChanged = True
              
          if stresstid.total_seconds() < udkaldTimeCalling: #60*10
            if self.state != State.CALLING:
              self.logger.info(inspect.currentframe().f_code.co_name+' - incident changed to calling') 
              stateChanged = True
            self.state = State.CALLING

          else:
            if self.state == State.CALLING:
              self.logger.info(inspect.currentframe().f_code.co_name+' - incident changed to active') 
              self.state = State.ACTIVE
              stateChanged = True
            isinactive = False
            if 'endtime' in self.rawdict:
              if datetime.now() > datetime.fromtimestamp(int(self.rawdict['endtime'])):
                isinactive = True
            else:
              if stresstid.total_seconds() > udkaldTimeActive and self.lastupdatetime < datetime.now()-timedelta(minutes=15):
              # kun hvis der ikke sendes flere opdateringer/resend om denne incident:
                isinactive = True
                
            if isinactive and self.state == State.ACTIVE:
              self.state = State.INACTIVE
              stateChanged = True
              printtime = ''
              if 'endtime' in self.rawdict:
                printtime = str(self.rawdict['endtime'])
              self.logger.info(inspect.currentframe().f_code.co_name+' - incident changed to inactive'+printtime)
          if self.state == State.INACTIVE:
              if 'endtime' in self.rawdict:
                indstatstid = datetime.fromtimestamp(int(self.rawdict['endtime']))-datetime.fromtimestamp(int(self.rawdict['starttime']))
                indsatsTimer,indsatsMinut = divmod(int(indstatstid.total_seconds()/60),60)
                udkaldstid = ''
                if indsatsTimer > 0:
                  udkaldstid += str(int(indsatsTimer))
                  if int(indsatsTimer) == 1:
                    udkaldstid += ' t '
                  else:
                    udkaldstid += ' t '
                udkaldstid += str(int(indsatsMinut)).zfill(2)
                if int(indsatsMinut) == 1:
                  udkaldstid += ' min.'
                else:
                  udkaldstid += ' min.'
                  
                udkaldstid += "   udkald kl. "+datetime.fromtimestamp(int(self.rawdict['starttime'])).strftime('%H:%M:%S')+" hjem kl."+datetime.fromtimestamp(int(self.rawdict['endtime'])).strftime('%H:%M:%S')

                
                if self.stressurCanvas is not None:
                  print(udkaldstid)  
                  self.stressurCanvas.itemconfig(self.stressurCanvasText, text=udkaldstid)
              if stresstid.total_seconds() >= 3600*24:
                self.logger.info(inspect.currentframe().f_code.co_name+' - incident changed to off')
                self.state = State.OFF
                stateChanged = True
               
          streesMin,stressSek = divmod(stresstid.total_seconds(),60)
          if streesMin >= 30 or self.state == State.INACTIVE:
            streesTimtmp,streesMintmp = divmod(streesMin,60)
            streesTimStr = str(int(streesTimtmp)).zfill(2)+':'+str(int(streesMintmp)).zfill(2)+':'+str(int(stressSek)).zfill(2)
          else:
            streesTimStr =str(int(streesMin)).zfill(2)+':'+str(int(stressSek)).zfill(2)
            
          self.stressstr.set(str(int(streesMin)).zfill(2)+':'+str(int(stressSek)).zfill(2))
          try:
            if (self.state == State.CALLING or self.state == State.ACTIVE) and not stateChanged and self.stressurCanvas is not None and self.stressurCanvasText is not None:
              if isinstance(self.stressurCanvas,tk.Canvas):
                self.stressurCanvas.itemconfig(self.stressurCanvasText, text=streesTimStr)
                if self.stressurCanvasBg is not None:
                  if self.state == State.CALLING:
                    if stresstid.total_seconds() < udkaldTimeWarning:
                      self.stressurCanvas.itemconfig(self.stressurCanvasBg, fill='')
                    else:
                      self.stressurCanvas.itemconfig(self.stressurCanvasBg, fill='#f3ff4a') #gul
                      if stresstid.total_seconds() > udkaldTimeExceeded:
                        self.stressurCanvas.itemconfig(self.stressurCanvasBg, fill='#ff454e') #rød
          except:
            self.logger.error(inspect.currentframe().f_code.co_name+' - failed to change streesur: '+str(traceback.format_exc()))
          return stateChanged
      
    def drawIncident(self,window):
      vconstrain = self.constrained
      incident = self.rawdict
      meldingsplit = None
      if 'melding' in incident:
        meldingsplit = incident['melding'].splitlines()
        if len(meldingsplit) <= 2:
          meldingsplit = None
        
      if self.state == State.ACTIVE or self.state == State.INACTIVE:
        textcolor = '#000'
        if self.state == State.INACTIVE:
          textcolor = '#aaa'
        if vconstrain:
          textsize = 12*scaling
        else:
          textsize = 30*scaling
        
        self.drawingFrame = tk.LabelFrame(window,fg=textcolor,font=("Arial", int(textsize*1.2)),labelanchor='n')
        frame = self.drawingFrame
        rownum = 0
        indsatstidLabelMes = tk.Message(frame,aspect=500, fg=textcolor,text = 'Indsats tid:',font=("Arial", int(textsize)))
        self.stressurCanvas = tk.Canvas(frame,background=window["bg"], width=1000, height=50)
        self.stressurCanvasBg = round_rectangle(self.stressurCanvas,0, 0, 2, 2, radius=20, fill='#000')
        self.stressurCanvasText = self.stressurCanvas.create_text(10, 30, fill=textcolor,text='_',anchor="w", font=("Arial", int(textsize)))
        self.stressurCanvas.grid(sticky="w",column=1, row=rownum)
        indsatstidLabelMes.grid(column=0, row=rownum)
        rownum += 1
        
        meldingLabelMes = tk.Message(frame,aspect=500,fg=textcolor, text = 'melding:',font=("Arial", int(textsize)))
        melding = ' '
        if meldingsplit is not None:
          if vconstrain:
            melding = ', '.join(meldingsplit)
          else:
            frame.configure(text=str(meldingsplit[0]))
            melding = textwrap.fill('\n'.join(meldingsplit[1:]),replace_whitespace=False,width=25)
        else:
          if 'meldingdata' in incident:
            if isinstance(incident['meldingdata'],dict):
              frame.configure(text=str(incident['meldingdata']['melding']))
              melding = ""
              if 'melding_specifik' in incident['meldingdata']:
                melding += str(incident['meldingdata']['melding_specifik'])+"\n"
              if 'crew' in incident['meldingdata']:
                for vechid in incident['meldingdata']['crew'].keys():
                  if vechid in incident['vehicles'].keys():
                    melding += incident['vehicles'][str(vechid)]+","
                melding += "\n"
                if 'melding' in incident:
                  melding += textwrap.fill(str(incident['melding']),replace_whitespace=False,width=25)+"\n"
        meldingMesMes = tk.Message(frame,aspect=500, fg=textcolor,text = str(melding),anchor="w",font=("Arial", int(textsize)))
        meldingLabelMes.grid(column=0, row=rownum)
        meldingMesMes.grid(sticky="W",column=1, row=rownum)
        
        frame.pack(fill='x',expand=True)
        
        
         
      if self.state == State.CALLING:
        
        self.drawingFrame = tk.LabelFrame(window, text='_',font=("Arial", int(70*scaling)),labelanchor='n')
        self.drawingFrame.columnconfigure(0, minsize=20, weight=0)
        self.drawingFrame.columnconfigure(1, weight=1)
        self.drawingFrame.columnconfigure(2, weight=1)
        
        def drawSeats(vechid,personelavail,height): #personelavail[{'name':'','skills':['BM']}]
            def drawCircle(cx,cy):
              circleradius = int(height/15)
              #print("circle:"+str(cx))
              c.create_oval(int(cx-circleradius),int(cy-circleradius),int(cx+circleradius),int(cy+circleradius),fill='white')

            vechicleid = str(vechid)
            if incident['meldingdata'] is not None:
              if 'crew' in incident['meldingdata']:
                if vechicleid in incident['meldingdata']['crew']:
                  crewneed = len(incident['meldingdata']['crew'][vechicleid])
                  crewused = min(crewneed,len(personelavail))
                  csize = int(height/2.5)
                  c = tk.Canvas(frame, width=csize, height=csize)
                  
                  for x in range(1,int(crewneed)+1):
                    if int(crewneed) == 2:
                      if x == 1:
                        if crewused>=x:
                          drawCircle(csize/5,csize/2)
                          #c.create_oval(int(cx-cirkelradius),int(cy-cirkelradius),8,12,fill='white')
                      if x == 2:
                        if crewused>=x:
                          drawCircle(csize/5*4,csize/2)
                          #c.create_oval(13,7,18,12,fill='white')
                    else:
                      if x == 1:
                        if crewused>=x:
                          drawCircle(csize/5*1,csize/5*1)
                          #c.create_oval(2,2,7,7,fill='white')
                      if x == 2:
                        if crewused>=x:
                          drawCircle(csize/5*4,csize/5*1)
                          #c.create_oval(13,2,18,7,fill='red')
                      if x == 3:
                        if crewused>=x:
                          drawCircle(csize/5*1,csize/5*4)
                          #c.create_oval(2,13,7,18,fill='white')
                      if x == 4:
                        if crewused>=x:
                          drawCircle(csize/5*4,csize/5*4)
                          #c.create_oval(13,13,18,18,fill='white')
                  return c,crewused,(crewneed<=crewused)
            return None,0,False
            
        meldSpecifik = None
        fuldmelding =  " "
        if 'suppl_melding' in incident.keys():
          fuldmelding  = str(incident['suppl_melding'])
        
        if isinstance(incident['vehicles'],str):
          vehicles = json.loads(incident['vehicles'])
        elif isinstance(incident['vehicles'],dict):
          vehicles = incident['vehicles']
        else:
          vehicles = {}
        if 'incident_type' in incident.keys():
          if isinstance(incident['incident_type'],dict):
            melding = str(incident['incident_type']['melding'])
            if 'melding_specifik' in incident['incident_type'].keys():
              meldSpecifik = str(incident['incident_type']['melding_specifik'])
    
            if 'crew' in incident['incident_type']:
              newvehicles = {}
              for vechid in incident['incident_type']['crew'].keys(): #sorter rækkefølge
                if str(vechid) in vehicles.keys():
                  newvehicles[str(vechid)] = vehicles[str(vechid)]
              for vechid,vechname in vehicles.items():
                if vechid not in newvehicles.keys():
                  newvehicles[str(vechid)] = vechname
              vehicles = newvehicles
              if meldingsplit is not None:
                start = 0
                end = len(meldingsplit)
                if len(vehicles) > 0 and 'short_code' in incident['incident_type']:
                  start = 1
                if 'short_code' in incident['incident_type']:
                  start = 2
                fuldmelding =  "\n".join(meldingsplit[start:end])
                
          else:
            if meldingsplit is not None:
              melding = meldingsplit[0]
              meldSpecifik = str(textwrap.fill('\n'.join(meldingsplit[1:]),replace_whitespace=False,width=30))
              
          
        frame = self.drawingFrame
        frame.configure(text=str(melding)) 

      

        køretøjer = {}
        rownum = 0
        if meldSpecifik is not None:
          if len(meldSpecifik) > 1:
            print('melding: '+meldSpecifik)
            meldSpecifikLabel = tk.Message(frame,aspect=500, text = str(meldSpecifik),font=("Arial", int(50*scaling)))
            meldSpecifikLabel.grid(column=0,columnspan=3, row=0)
            rownum += 1
        self.logger.debug(inspect.currentframe().f_code.co_name+' - køretøjer:'+str(incident['vehicles']))
        if vconstrain:
          rowur = rownum+1
        else:
          rowur = rownum 
          rownum += 1
        if 'location' in incident.keys():
          lokationstr = ''
          if 'sted' in incident['location'].keys():
            if isinstance(incident['location']['sted'],str):
              lokationstr += str(incident['location']['sted'])
          if 'adresse' in incident['location'].keys():
            lokationstr += ' - '
            if isinstance(incident['location']['adresse'],list):
              if isinstance(incident['location']['adresse'][1],str):
                lokationstr += str(incident['location']['adresse'][1])
              if isinstance(incident['location']['adresse'][0],str):
                lokationstr = str(incident['location']['adresse'][0])  

          lokation = tk.Label(frame, text = str(lokationstr),font=("Arial", int(40*scaling)))
          lokation.grid(column=0,columnspan=3, row=rownum)
          rownum += 1

        personelavail = 0
        extracrew = 0
        if 'crew' in incident:
          try:
            if isinstance(incident['crew'],dict):
              crew = incident['crew']
            else:
              crew = json.loads(incident['crew'])
            if 'assigned' in crew.keys():
              if int(crew['assigned']) > 0:
                personelavail = int(crew['assigned'])
                extracrew = 0
                if 'minimum' in crew.keys():
                  extracrew = int(crew['assigned'])-int(crew['minimum'])
          except:
            self.logger.warn(inspect.currentframe().f_code.co_name+' - no crew in incident '+str(crew))

             
        for vechid,vechname in vehicles.items():
          if vechid != 'ISL':
           personel = [None]*int(personelavail)
           ktsize = {'h':int(150*scaling),'w':int(700*scaling),'xoffs':5,'yoffs':0}      
           c,personelused,filled = drawSeats(vechid,personel,ktsize['h'])
           personelavail -= personelused 
           if c is not None:
             c.grid(column=0, row=rownum,sticky=tk.W)

           if False: #simple
             køretøjer[vechid] = tk.Label(frame, text = str(vechname), bg=backgroundc) #simple
           else:
              
             køretøjer[vechid] = tk.Canvas(frame,background=window["bg"], width=ktsize['w'], height=ktsize['h'])
             if filled:
               round_rectangle(køretøjer[vechid],ktsize['xoffs'], ktsize['yoffs'], ktsize['w']-ktsize['xoffs']-1, ktsize['h']-ktsize['yoffs']-1, radius=ktsize['h']*0.15, fill='#6eff7c')
             else:
               pass
             køretøjer[vechid].create_text(ktsize['xoffs']+5, int(ktsize['h']/2), text=str(vechname),anchor="w", font=('Helvetica', int(80*scaling)))

           køretøjer[vechid].grid(column=1, row=rownum,sticky=tk.W)
           self.logger.debug(inspect.currentframe().f_code.co_name+' - drawing '+str(vechid)+' at row '+str(rownum))
           #køretøjer[vechid].pack(fill='x',expand=True)
           rownum += 1
        if extracrew > 0:
          ekstracrewLabel = tk.Label(frame, text = '+'+str(int(extracrew)),font=('Helvetica',int(100*scaling)))
          ekstracrewLabel.grid(column=0,columnspan=2, row=rownum,sticky=tk.W)
          rownum += 1
        if 'starttime' in incident:
          #self.updateur()
          if vconstrain:
            ursize = {'h':int(60*scaling),'w':int(230*scaling)} 
            self.stressurCanvas = tk.Canvas(frame,background=window["bg"], width=ursize['w'], height=ursize['h'])
            self.stressurCanvasBg = round_rectangle(self.stressurCanvas,1, 1, ursize['w']-1, ursize['w']-1, radius=int(ursize['h']*0.15), fill='')
            self.stressurCanvasText = self.stressurCanvas.create_text(int(ursize['w']*0.05), int(ursize['h']/2), text='_',anchor="w", font=("Arial", int(48*scaling)))
            self.stressurCanvas.grid(column=2,rowspan=rownum, row=rowur)
          else:
            ursize = {'h':int(140*scaling),'w':int(430*scaling)} 
            self.stressurCanvas = tk.Canvas(frame,background=window["bg"], width=ursize['w'], height=ursize['h'])
            self.stressurCanvasBg = round_rectangle(self.stressurCanvas,1, 1, ursize['w']-1, ursize['h']-1, radius=int(ursize['h']*0.15), fill='') 
            self.stressurCanvasText = self.stressurCanvas.create_text(int(ursize['w']*0.05), int(ursize['h']/2), text='_',anchor="w", font=("Arial", int(120*scaling)))  #120
            self.stressurCanvas.grid(column=0,columnspan=3, row=rowur)
          self.updateur()
        if not vconstrain:
          
          meldfullLabel = tk.Message(frame,aspect=500, text = str(fuldmelding),font=("Arial", int(20*scaling)))
          meldfullLabel.grid(column=0,columnspan=3, row=rownum)

        frame.pack(fill='x',expand=True)  
        
def strfdelta(tdelta, fmt):
    d = {"days": tdelta.days}
    d["hours"], rem = divmod(tdelta.seconds, 3600)
    d["minutes"], d["seconds"] = divmod(rem, 60)
    return fmt.format(**d)
    
def round_rectangle(canvas,x1, y1, x2, y2, radius=25, **kwargs):
        
    points = [x1+radius, y1,
              x1+radius, y1,
              x2-radius, y1,
              x2-radius, y1,
              x2, y1,
              x2, y1+radius,
              x2, y1+radius,
              x2, y2-radius,
              x2, y2-radius,
              x2, y2,
              x2-radius, y2,
              x2-radius, y2,
              x1+radius, y2,
              x1+radius, y2,
              x1, y2,
              x1, y2-radius,
              x1, y2-radius,
              x1, y1+radius,
              x1, y1+radius,
              x1, y1]
        
    return canvas.create_polygon(points, **kwargs, smooth=True)
class State(Enum):
       CALLING = 1
       ACTIVE = 2
       INACTIVE = 3
       OFF = 4        
class ThreadState(Enum):
    INIT = 0 #just create no update yet
    CONNECTING = 1 #commanded to connect no update yet
    CONNECTED = 2 #connected
    INCONCLUSIVE = 3 # all not determined
    DISCONNECTED = 4 #disconnected     
    def __lt__(self, other):
      if self.__class__ is other.__class__:
        return self.value < other.value
      return NotImplemented
"""
t1 = Incidents()
print(t1.updateure())   
"""     
