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
from datetime import datetime,timedelta
from dotenv import load_dotenv

mqtt_logger = logging.getLogger(__name__)
mqtt_logger.setLevel(logging.DEBUG)

load_dotenv()
mqttdata = json.loads(os.getenv('MQTTDATA'))


def threadMqtt(name,respQueue: Queue):
    conntimeout = datetime.now()+timedelta(minutes = 5)
    ## mqtt
    # The callback for when the client receives a CONNACK response from the server.
    def on_connect(client, userdata, flags, rc):
         nonlocal conntimeout
         mqtt_logger.info("Connected with result code "+str(rc))
         client.publish("struerbrand/status",'screen logged on')
         client.subscribe(mqttdata['topic'])
         conntimeout = datetime.now()+timedelta(days = 1)
    # The callback for when a PUBLISH message is received from the server.
    def on_disconnect(client, userdata, rc):
      nonlocal conntimeout
      mqtt_logger.warn("Device disconnected with result code: " + str(rc))
      conntimeout = datetime.now()+timedelta(minutes = 10)
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
         conntimeout = datetime.now()+timedelta(minutes = 120)
         mqtt_logger.debug('recieved message: '+str(len(msg.payload)))
         respQueue.put({'message':msg.payload,'topic':msg.topic})

    def on_queueReq(item):
         client.publish("brandtelegram/test",item)
    def on_log(client, userdata, level, buf):
       mqtt_logger.debug(f"SYSTEM: {buf}")
  
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
    client.on_connect = on_connect
    client.on_disconnect = on_disconnect
    client.on_message = on_message
    client.on_log = on_log
    client.username_pw_set(mqttdata['user']['name'], mqttdata['user']['password'])
    
    
    
    #tell others that we hadled the incident
    mqtt_logger.debug("connecting to broker")
    connCert()
    mqtt_logger.debug('connected?')
    client.loop_forever()
    #while datetime.now() < conntimeout:
    #   client.loop_start()
    #   time.sleep(0.5)
    #   client.loop_stop()
    raise "MQTT ended due to timeout reached"
       
       
