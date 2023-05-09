import gi
from paho.mqtt import client as mqtt_client
import random
import threading
import argparse
import sys

gi.require_version('Gtk', '3.0')
from gi.repository import GLib, Gtk, GdkPixbuf, Gio


class MqttImage(Gtk.Window):
    def __init__(self, broker, port, topic, callback):
        Gtk.Window.__init__(self)
        self.set_default_size(300, 200)
        self.broker = broker
        self.port = port
        self.topic = topic
        self.client_id = f'MQTTGO-{random.randint(0, 1000000)}'
        
        self.set_title(topic)
        self.connect("destroy", callback)

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


class AppWindow(Gtk.ApplicationWindow):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        main_vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)     
        self.add(main_vbox)

        main_vbox.set_margin_top(10)
        main_vbox.set_margin_start(10)
        main_vbox.set_margin_end(10)
        main_vbox.set_margin_bottom(10)

        hbox1 = Gtk.Box(spacing=10)   
        broker_label = Gtk.Label()
        broker_label.set_text("MQTT Broker:")
        self.broker_entry = Gtk.Entry()
        self.broker_entry.set_text("broker.MQTTGO.io")

        hbox1.pack_start(broker_label, False, False, 0)
        hbox1.pack_start(self.broker_entry, True, True, 0)
        main_vbox.pack_start(hbox1, True, False, 0)

        hbox2 = Gtk.Box(spacing=10)   
        port_label = Gtk.Label()
        port_label.set_text("MQTT Port:   ")
        self.port_entry = Gtk.Entry()
        self.port_entry.set_text("1883")

        hbox2.pack_start(port_label, False, False, 0)
        hbox2.pack_start(self.port_entry, True, True, 0)
        main_vbox.pack_start(hbox2, True, False, 0)

        hbox3 = Gtk.Box(spacing=10)   
        topic_label = Gtk.Label()
        topic_label.set_text("Image Topic: ")
        self.topic_entry = Gtk.Entry()
        
        hbox3.pack_start(topic_label, False, False, 0)
        hbox3.pack_start(self.topic_entry, True, True, 0)
        main_vbox.pack_start(hbox3, True, False, 0)

        connect_button = Gtk.Button.new_with_label("Connect")
        connect_button.connect("clicked", self.click_connect_button)
        main_vbox.pack_start(connect_button, True, False, 0)
        self.show_all()

    def click_connect_button(self, button):
        print(self.broker_entry.get_text())
        print(self.port_entry.get_text())
        print(self.topic_entry.get_text())

        win = MqttImage(self.broker_entry.get_text(), 
                        int(self.port_entry.get_text()), 
                        self.topic_entry.get_text(),
                        self.mqtt_image_close)
        win.show_all()

    def mqtt_image_close(self, win):
        print("mqtt_image_close:")
        print(win.topic)


class Application(Gtk.Application):
    def __init__(self, *args, **kwargs):
        super().__init__(
            *args,
            application_id="site.riddleling.app.mqtt-image",
            flags=Gio.ApplicationFlags.HANDLES_COMMAND_LINE,
            **kwargs
        )
        self.window = None

    def do_activate(self):
        if not self.window:
            self.window = AppWindow(application=self, title="MQTT Image")
        self.window.present()

    def do_command_line(self, command_line):
        options = command_line.get_options_dict()
        # convert GVariantDict -> GVariant -> dict
        options = options.end().unpack()

        if "test" in options:
            # This is printed on the main instance
            print("Test argument recieved: %s" % options["test"])

        self.activate()
        return 0


if __name__ == "__main__":
    app = Application()
    app.run(sys.argv)
