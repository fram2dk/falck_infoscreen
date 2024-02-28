from queue import Queue
import paho.mqtt.client as mqtt
import ssl
import time
import os
import json
from dotenv import load_dotenv

load_dotenv()
mqttdata = json.loads(os.getenv('MQTTDATA'))


def threadMqtt(name,respQueue: Queue):
    ## mqtt
    # The callback for when the client receives a CONNACK response from the server.
    def on_connect(client, userdata, flags, rc):
         print("Connected with result code "+str(rc))

         client.publish("struerbrand/status",'screen logged on')
         client.subscribe(mqttdata['topic'])
    # The callback for when a PUBLISH message is received from the server.
    def on_message(client, userdata, msg):
         print('recieved message: '+str(len(msg.payload)))
         respQueue.put({'message':msg.payload,'topic':msg.topic})

    def on_queueReq(item):
         client.publish("brandtelegram/test",item)

    def connCert():
       cafile = './rootCA.crt'
       certfile = './brandtelegram.crt'
       keyfile = './brandtelegram.key'
       client.tls_set(ca_certs=cafile, certfile=certfile, keyfile=keyfile, tls_version=ssl.PROTOCOL_TLS, cert_reqs=ssl.CERT_REQUIRED)
       client.tls_insecure_set(True)
       client.connect(mqttdata['server']['hostname'], mqttdata['server']['port'], 60)

    client = mqtt.Client("station1")
    client.on_connect = on_connect
    client.on_message = on_message
    client.username_pw_set(mqttdata['user']['name'], mqttdata['user']['password'])
    #tell others that we hadled the incident
    print("connecting to broker")
    connCert()
    print('connected?')
    while True:
       client.loop_start()
       time.sleep(0.5)
       client.loop_stop()
