import paho.mqtt.client as mqtt
import pymongo
from yeelight import Bulb, discover_bulbs
import json
from pprint import pprint

# TODO: look into start_music, it may be a way to remove the rate-limiting to 
# allow 100s of updates in a few seconds. (Sliding dimmer/live update color/etc.)

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

    def toggle(self):
        self.bulb.toggle()

    # TODO: values should be validated
    # temperature: 1700-6500
    # brightness: 1-100
    def handle_command(self, data):
        if "power" in data:
            if data['power'] == "on":
                print("Turning on")
                self.on()
            elif data['power'] == "off":
                print("Turning off")
                self.off()
            else:
                print("Invalid power value: ", data['power'])
        if "temperature" in data:
            self.bulb.set_color_temp(int(data["temperature"]))
        if "color" in data:
            red, green, blue = map(int, data['color'].split(","))
            self.bulb.set_rgb(red, green, blue, light_type=0)
        if "brightness" in data:
            self.bulb.set_brightness(int(data["brightness"]))


def send_command(data):
    try:
        bulb = YeelightBulb(data['ip_addr'])
        bulb.handle_command(data['cmd'])
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