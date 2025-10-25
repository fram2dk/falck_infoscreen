from queue import Queue
import paho.mqtt.client as mqtt
import ssl
import time
import base64
import os
import sys
import json
import logging
import random
import uuid
from datetime import datetime,timedelta,timezone
from dotenv import load_dotenv

mqtt_logger = logging.getLogger(__name__)
mqtt_logger.setLevel(logging.DEBUG)

load_dotenv()
mqttdata = json.loads(os.getenv('MQTTDATA'))


def threadMqtt(name,respQueue: Queue,statusQueue: Queue,monitorque: Queue,incidenttopic='',swversion='.,.',instanceid='ABC'):
    conntimeout = datetime.now()+timedelta(minutes = 5)
    mqttstate = 'init'
    lastheartbeatupmqtt = datetime.now()
    mqttbasetopic = str(mqttdata['topic'].split('/')[0])
    ## mqtt
    # The callback for when the client receives a CONNACK response from the server.
    def on_connect(client, userdata, flags, rc):
         nonlocal conntimeout
         mqtt_logger.info("Connected with result code "+str(rc))
         client.publish(str(mqttbasetopic)+"/fromScreen/instance/"+str(instanceid), json.dumps({'timestamp':datetime.now(timezone.utc).timestamp(),'instance':str(instanceid),'message':'screen logged on','swversion':str(swversion),'listening':[str(mqttdata['topic'])]}))
         client.subscribe(mqttdata['topic'])
         conntimeout = datetime.now()+timedelta(days = 1)
         monitorque.put({'name':name,'state':'connected'})
    # The callback for when a PUBLISH message is received from the server.
    def on_disconnect(client, userdata, rc):
      nonlocal conntimeout
      mqtt_logger.warn("Device disconnected with result code: " + str(rc))
      conntimeout = datetime.now()+timedelta(minutes = 10)
      monitorque.put({'name':name,'state':'disconnected'})
      if rc != 0:
        recondelay = random.randrange(8, 89)
        mqtt_logger.info("Unexpected MQTT disconnection. Attempting to reconnect. in "+str(recondelay)+" seconds")
        time.sleep(recondelay)
        try:
          client.reconnect()
        except:
          recondelay = random.randrange(60, 289)
          mqtt_logger.info("Unexpected MQTT disconnection. Attempting to reconnect. in "+str(recondelay)+" seconds")
      
      
    def on_message(client, userdata, msg):
         nonlocal conntimeout
         nonlocal mqttid
         nonlocal lastheartbeatupmqtt
         conntimeout = datetime.now()+timedelta(minutes = 1)
         mqtt_logger.debug('recieved message: '+str(len(msg.payload)))
         respQueue.put({'mqtt':{'message':msg.payload,'topic':msg.topic}})
         if lastheartbeatupmqtt+timedelta(minutes=30)<datetime.now():
           client.publish(str(mqttbasetopic)+"/fromScreen/instance/"+str(instanceid),json.dumps({'timestamp':datetime.now(timezone.utc).timestamp(),'instance':str(instanceid),'message':'alive and well','swversion':str(swversion),'listening':[str(mqttdata['topic'])]}))
           lastheartbeatupmqtt = datetime.now()
    
    def on_queueReq(item):
         client.publish("brandtelegram/test",item)
    def on_log(client, userdata, level, buf):
       mqtt_logger.debug(f"SYSTEM: {buf}")
       if str(buf) == 'Received PINGRESP':
         monitorque.put({'name':name,'state':'connected'})
  
    def connCert():
       cafile = './rootCA.crt'
       certfile = './brandtelegram.crt'
       keyfile = './brandtelegram.key'
       
       client.tls_set(ca_certs=cafile, certfile=certfile, keyfile=keyfile, tls_version=ssl.PROTOCOL_TLS, cert_reqs=ssl.CERT_REQUIRED)
       client.tls_insecure_set(True)
       client.connect(mqttdata['server']['hostname'], mqttdata['server']['port'], 53)
    try:
      mqttid = str(os.getenv('STATIONNAME'))+'-'
    except:
      mqtt_logger.warn('station name not set')
    mqttid +=  str(base64.b64encode(uuid.getnode().to_bytes(6,'big')).decode("ascii"))
    print(mqttid)
    client = mqtt.Client(mqttid)
    while mqttstate == 'init':
      client.reinitialise()
      client.on_connect = on_connect
      client.on_disconnect = on_disconnect
      client.on_message = on_message
      client.on_log = on_log
      client.username_pw_set(mqttdata['user']['name'], mqttdata['user']['password'])

      mqtt_logger.debug("connecting to broker")
      monitorque.put({'name':name,'state':'connecting'})
    
      try:
        connCert()
        mqttstate = 'connected'
      except OSError as e:
        mqtt_logger.info("MQTT not able to connect. due to "+str(e))
        time.sleep(10)
        
    mqtt_logger.debug('connected?')
    #client.loop_forever()
    while True: #datetime.now() < conntimeout:
       client.loop_start()
       while not statusQueue.empty():
         client.publish(str(mqttbasetopic)+"/fromScreen/instance/"+str(instanceid)+"/incidentupdate",json.dumps({'timestamp':datetime.now(timezone.utc).timestamp(),'instance':str(instanceid),'message':json.dumps(statusQueue.get())}))
       time.sleep(0.5)
       client.loop_stop()
    raise "MQTT ended due to timeout reached"
       
       
