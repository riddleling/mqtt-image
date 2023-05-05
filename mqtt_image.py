import gi
from paho.mqtt import client as mqtt_client
import random
import threading
import base64
import argparse

gi.require_version('Gtk', '3.0')
from gi.repository import GLib, Gtk, GObject, GdkPixbuf, Gio


class MqttImage(Gtk.Window):
    def __init__(self, broker, port, topic):
        Gtk.Window.__init__(self)
        
        self.broker = broker
        self.port = port
        self.topic = topic
        self.client_id = f'MQTTGO-{random.randint(0, 1000000)}'
        
        self.set_title("MQTT Image")
        self.connect("destroy", Gtk.main_quit)

        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)     
        self.add(vbox)

        self.image = Gtk.Image()       
        vbox.pack_start(self.image, True, True, 0)

        thread = threading.Thread(target=self.connect_mqtt)
        thread.daemon = True
        thread.start()

    def connect_mqtt(self):
        def mqtt_on_connect(client, userdata, flags, rc):
            if rc == 0:
                print("Connected to MQTT Broker!")
            else:
                print("Failed to connect, return code %d\n", rc)

        self.client = mqtt_client.Client(self.client_id)
        self.client.on_connect = mqtt_on_connect
        self.client.connect(self.broker, self.port)
        self.subscribe()
        self.client.loop_forever()
    
    def subscribe(self):
        def on_message(client, userdata, msg):
            #print(f"Received `{msg.payload}` from `{msg.topic}` topic")
            GLib.idle_add(self.update_image, msg.payload)

        self.client.subscribe(self.topic)
        self.client.on_message = on_message

    def update_image(self, image_data):
        loader = GdkPixbuf.PixbufLoader.new()
        loader.write(image_data)
        pixbuf = loader.get_pixbuf()
        self.image.set_from_pixbuf(pixbuf)
        loader.close()



parser = argparse.ArgumentParser()
parser.add_argument("-b", "--broker", help="MQTT Broker")
parser.add_argument("-p", "--port", help="MQTT Port", type=int)
parser.add_argument("-t", "--topic", help="MQTT Image topic")
args = parser.parse_args()

window = MqttImage(args.broker, args.port, args.topic)
window.show_all()

Gtk.main()