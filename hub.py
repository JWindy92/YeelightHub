import paho.mqtt.client as mqtt
import pymongo
from yeelight import Bulb, discover_bulbs
import json
from pprint import pprint

bulbs = []

class YeelightBulb:

    def __init__(self, ip):
        self.ip = ip
        self.bulb = Bulb(ip)

    def get_status(self):
        re_map = {
            "on": True,
            "off": False
        }
        props = self.bulb.get_properties()
        props['power'] = re_map[props['power']]
        return props

    def off(self):
        self.bulb.turn_off()
    
    def on(self):
        self.bulb.turn_on()

    def handle_command(self, data):
        if self.get_status()['power'] != data['state']['power']:
            self.bulb.toggle()
        

# TODO: May be able to use built in discovery service rather than pulling from mongo, but this may be more reliable/faster
mongoClient = pymongo.MongoClient("mongodb://10.0.0.52:27018/")
db = mongoClient["SmartHomeDB"]
devices = db["DEVICES"]

yeelights = devices.find({"type": "Yeelight"})
for doc in yeelights:
    print("Found a bulb")
    bulb = YeelightBulb(doc['addr'])
    bulbs.append(bulb)

def get_bulb_by_ip(addr):
    for bulb in bulbs:
        if addr == bulb.ip:
            return bulb

def discover():
    print("Looking for bulbs")
    bulbs = discover_bulbs(timeout=30)
    return bulbs

def send_command(data):
    try:
        bulb = get_bulb_by_ip(data['addr'])
        bulb.handle_command(data)
    except:
        print("Something went wrong")

# The callback for when the client receives a CONNACK response from the server.
def on_connect(client, userdata, flags, rc):
    print("Connected with result code "+str(rc))

    # Subscribing in on_connect() means that if we lose the connection and
    # reconnect then subscriptions will be renewed.
    client.subscribe("yeelight/cmnd")

# The callback for when a PUBLISH message is received from the server.
def on_message(client, userdata, msg):
    data = json.loads(msg.payload)
    print(msg.topic)
    if msg.topic == "yeelight/cmnd":
        print("sending")
        send_command(data)

client = mqtt.Client()
client.on_connect = on_connect
client.on_message = on_message

client.connect("10.0.0.228", 1883, 60)

# Blocking call that processes network traffic, dispatches callbacks and
# handles reconnecting.
# Other loop*() functions are available that give a threaded interface and a
# manual interface.
client.loop_forever()