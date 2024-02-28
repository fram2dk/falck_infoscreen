from enum import Enum
from datetime import datetime,timedelta
import tkinter as tk
import json
import textwrap

class Incidents:
  def __init__(self):
    self.allincidents = {}
    self.displayclock = False
    self.clockstr = None
    self.listActiveIncidents = []
  def updateure(self):
    for incidentid,incidentObj in self.allincidents.items():
      statechanged = incidentObj.updateur()
      if statechanged:
        return True
    if self.displayclock:
      if self.clockstr is not None:
        self.clockstr.set(datetime.now().strftime('%H:%M:%S'))
        print(self.clockstr.get())
    return False #statechanged
  def update_incidents(self,curWindow,newIncidents=None):
    if newIncidents is not None:
      for incident in newIncidents:
        if 'id' in incident:
          newid = incident['id']
          if newid not in self.allincidents.keys():
            self.allincidents[newid] = self.Incident(newid)
          if newid in self.allincidents.keys():
            self.allincidents[newid].update(incident)
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
       clocklabel = tk.Label(curWindow, textvariable = self.clockstr,font=("Arial", 160))
       clocklabel.pack(fill='x',expand=True)
    for incidentid,incidentObj in self.allincidents.items():
       if stateview[1]+stateview[2]+stateview[3] >= 3:
          incidentObj.setConstrain(True)
       else:
          incidentObj.setConstrain(False)
       if incidentObj.rawdict != '' and incidentObj.state != State.OFF:
         incidentObj.drawIncident(curWindow)
    
    
  class Incident:
    
    def __init__(self, incidentid):
      incidentid = incidentid
      self.rawdict = ''
      self.state = State.OFF
      self.constrained = False
      self.drawingFrame = None
      self.stressstr = tk.StringVar()
      self.stressurCanvas = None
      self.stressurCanvasText = None
      self.stressurCanvasBg = None
    def setConstrain(self,newvalue):
      self.constrained = bool(newvalue)
    def update(self,newdict):
      if newdict != self.rawdict:
        self.rawdict = newdict
        print('ny melding'+str(self.rawdict))
    def updateur(self):
      udkaldTimeWarning = 280 #280
      udkaldTimeExceeded = 300 #300
      udkaldTimeCalling = 600 #600
      udkaldTimeActive =  60*30 #60*30
      udkaldTimeExpired = 3600*12 #3600*12
      stateChanged = False
 
      if isinstance(self.rawdict,dict):
        if 'starttime' in self.rawdict:
          stresstid = datetime.now()-datetime.fromtimestamp(int(self.rawdict['starttime']))+timedelta(seconds=20)
          if stresstid.total_seconds() < udkaldTimeCalling: #60*10
            if self.state != State.CALLING:
              print('incident changed to calling') 
              stateChanged = True
            self.state = State.CALLING

          else:
            if self.state == State.CALLING:
              print('incident changed to active') 
              self.state = State.ACTIVE
              stateChanged = True
            if stresstid.total_seconds() > udkaldTimeActive and self.state == State.ACTIVE: #('endtime' in self.rawdict)
              self.state = State.INACTIVE
              stateChanged = True
              print('incident changed to inactive'+str(self.rawdict['endtime']))
          if self.state == State.INACTIVE:
            if 'endtime' in self.rawdict:
              #stresstid = datetime.fromtimestamp(int(self.rawdict['endtime']))-datetime.fromtimestamp(int(self.rawdict['starttime']))
              if stresstid.total_seconds() >= udkaldTimeExpired:
                print('incident changed to off')
                self.state = State.OFF
                stateChanged = True
               
          streesMin,stressSek = divmod(stresstid.total_seconds(),60)
          if streesMin >= 30 or self.state == State.INACTIVE:
            streesTimtmp,streesMintmp = divmod(streesMin,60)
            streesTimStr = str(int(streesTimtmp)).zfill(2)+':'+str(int(streesMintmp)).zfill(2)+':'+str(int(stressSek)).zfill(2)
          else:
            streesTimStr =str(int(streesMin)).zfill(2)+':'+str(int(stressSek)).zfill(2)
            
          self.stressstr.set(str(int(streesMin)).zfill(2)+':'+str(int(stressSek)).zfill(2))
          if (self.state == State.CALLING or self.state == State.ACTIVE) and self.stressurCanvas is not None and self.stressurCanvasText is not None:
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
          return stateChanged
      
    def drawIncident(self,window):
      vconstrain = self.constrained
      incident = self.rawdict
      meldingsplit = None
      if 'melding' in incident:
        meldingsplit = incident['melding'].splitlines()
      if self.state == State.ACTIVE or self.state == State.INACTIVE:
        textcolor = '#000'
        if self.state == State.INACTIVE:
          textcolor = '#aaa'
        if vconstrain:
          textsize = 12
        else:
          textsize = 30
        
        self.drawingFrame = tk.LabelFrame(window,fg=textcolor,font=("Arial", int(textsize*1.2)),labelanchor='n')
        frame = self.drawingFrame
        rownum = 0
        indsatstidLabelMes = tk.Message(frame,aspect=500, fg=textcolor,text = 'Indsats tid:',font=("Arial", textsize))
        self.stressurCanvas = tk.Canvas(frame,background=window["bg"], width=200, height=50)
        self.stressurCanvasBg = round_rectangle(self.stressurCanvas,0, 0, 410, 120, radius=20, fill='')
        self.stressurCanvasText = self.stressurCanvas.create_text(10, 20, fill=textcolor,text='_',anchor="w", font=("Arial", textsize))
        self.stressurCanvas.grid(column=1, row=rownum)
        indsatstidLabelMes.grid(column=0, row=rownum)
        rownum += 1
        
        meldingLabelMes = tk.Message(frame,aspect=500,fg=textcolor, text = 'melding:',font=("Arial", textsize))
        melding = ' '
        if meldingsplit is not None:
          if vconstrain:
            melding = ', '.join(meldingsplit)
          else:
            frame.configure(text=str(meldingsplit[0]))
            melding = textwrap.fill('\n'.join(meldingsplit[1:]),replace_whitespace=False,width=25)
        meldingMesMes = tk.Message(frame,aspect=500, fg=textcolor,text = str(melding),font=("Arial", textsize))
        meldingLabelMes.grid(column=0, row=rownum)
        meldingMesMes.grid(column=1, row=rownum)
        
        frame.pack(fill='x',expand=True)
        
        
         
      if self.state == State.CALLING:
        
        self.drawingFrame = tk.LabelFrame(window, text='_',font=("Arial", 70),labelanchor='n')
        self.drawingFrame.columnconfigure(0, minsize=20, weight=0)
        self.drawingFrame.columnconfigure(1, weight=1)
        self.drawingFrame.columnconfigure(2, weight=1)
        
        def drawSeats(vechid,personelavail): #personelavail[{'name':'','skills':['BM']}]
            def drawCircle(cx,cy):
              circleradius = 10
              print("circle:"+str(cx))
              c.create_oval(int(cx-circleradius),int(cy-circleradius),int(cx+circleradius),int(cy+circleradius),fill='white')

            vechicleid = str(vechid)
            if incident['meldingdata'] is not None:
              if 'crew' in incident['meldingdata']:
                if vechicleid in incident['meldingdata']['crew']:
                  crewneed = len(incident['meldingdata']['crew'][vechicleid])
                  crewused = min(crewneed,len(personelavail))
                  csize = 60
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
        vehicles = json.loads(incident['vehicles'])
        if 'meldingdata' in incident:
          if isinstance(incident['meldingdata'],dict):
            melding = str(incident['meldingdata']['melding'])
            if 'melding_specifik' in incident['meldingdata']:
              meldSpecifik = str(incident['meldingdata']['melding_specifik'])
    
            if 'crew' in incident['meldingdata']:
              newvehicles = {}
              for vechid in incident['meldingdata']['crew'].keys(): #sorter rækkefølge
                if str(vechid) in vehicles.keys():
                  newvehicles[str(vechid)] = vehicles[str(vechid)]
              for vechid,vechname in vehicles.items():
                if vechid not in newvehicles.keys():
                  newvehicles[str(vechid)] = vechname
              vehicles = newvehicles
              if meldingsplit is not None:
                start = 0
                end = len(meldingsplit)
                if len(vehicles) > 0 and 'meldKode' in incident['meldingdata']:
                  start = 1
                if 'meldingsKode' in incident['meldingdata']:
                  start = 2
                fuldmelding =  "\n".join(meldingsplit[start:end])
          else:
            if meldingsplit is not None:
              melding = meldingsplit[0]
              meldSpecifik = str('\n'.join(meldingsplit[1:]))          
          
        frame = self.drawingFrame
        frame.configure(text=str(melding)) 

      

        køretøjer = {}
        rownum = 0
        if meldSpecifik is not None:
          if len(meldSpecifik) > 1:
            #print('meldoing: '+meldSpecifik)
            meldSpecifikLabel = tk.Message(frame,aspect=500, text = str(meldSpecifik),font=("Arial", 50))
            meldSpecifikLabel.grid(column=0,columnspan=3, row=0)
            rownum += 1
        print(incident['vehicles'])
        if vconstrain:
          rowur = rownum+1
        else:
          rowur = rownum 
          rownum += 1
        if 'lokation' in incident:
          if incident['lokation'] is not None:
            lokation = tk.Label(frame, text = str(incident['lokation']),font=("Arial", 40))
            lokation.grid(column=0,columnspan=3, row=rownum)
            rownum += 1

        personelavail = 0
        extracrew = 0
        if 'crew' in incident:
          try:
            crew = json.loads(incident['crew'])
            if 'assigned' in crew:
              if int(crew['assigned']) > 0:
                personelavail = int(crew['assigned']) 
                extracrew = int(crew['assigned'])-int(crew['minimum'])
          except:
            pass

             
        for vechid,vechname in vehicles.items():
          if vechid != 'ISL':
           personel = [None]*int(personelavail)      
           c,personelused,filled = drawSeats(vechid,personel)
           personelavail -= personelused 
           if c is not None:
             c.grid(column=0, row=rownum,sticky=tk.W)

           if False: #simple
             køretøjer[vechid] = tk.Label(frame, text = str(vechname), bg=backgroundc) #simple
           else:
             køretøjer[vechid] = tk.Canvas(frame,background=window["bg"], width=550, height=150)
             if filled:
               round_rectangle(køretøjer[vechid],5, 15, 545, 135, radius=10, fill='#6eff7c')
             else:
               pass
             køretøjer[vechid].create_text(10, 70, text=str(vechname),anchor="w", font=('Helvetica 80'))

           køretøjer[vechid].grid(column=1, row=rownum,sticky=tk.W)
           print('drawing '+str(vechid)+' at row '+str(rownum))
           #køretøjer[vechid].pack(fill='x',expand=True)
           rownum += 1
        if extracrew > 0:
          ekstracrewLabel = tk.Label(frame, text = '+'+str(int(extracrew)),font=('Helvetica 100'))
          ekstracrewLabel.grid(column=0,columnspan=2, row=rownum,sticky=tk.W)
          rownum += 1
        if 'starttime' in incident:
          #self.updateur()
          if vconstrain:
            self.stressurCanvas = tk.Canvas(frame,background=window["bg"], width=230, height=60)
            self.stressurCanvasBg = round_rectangle(self.stressurCanvas,1, 1, 229, 59, radius=10, fill='')
            self.stressurCanvasText = self.stressurCanvas.create_text(10, 30, text='_',anchor="w", font=("Arial", 48))
            self.stressurCanvas.grid(column=2,rowspan=rownum, row=rowur)
          else:
            self.stressurCanvas = tk.Canvas(frame,background=window["bg"], width=430, height=140)
            self.stressurCanvasBg = round_rectangle(self.stressurCanvas,0, 0, 410, 120, radius=20, fill='')
            self.stressurCanvasText = self.stressurCanvas.create_text(10, 60, text='_',anchor="w", font=("Arial", 120))
            self.stressurCanvas.grid(column=0,columnspan=3, row=rowur)
          self.updateur()
        if not vconstrain:
          
          meldfullLabel = tk.Message(frame,aspect=500, text = str(fuldmelding),font=("Arial", 20))
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
        

t1 = Incidents()
print(t1.updateure())   
        