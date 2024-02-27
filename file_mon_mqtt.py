# This is a companion script to GoveeBTTempLogger (https://github.com/wcbonner/GoveeBTTempLogger). to provide an integration to homeassistant
#
#
# Filemonitor watching a directory and on changes to a (log-)file gets the last line, reformats it as json, then publishes that json as payload to an MQTT Topic
#
# When a device is encountered for the first time, a Homeassitant MQQT Sensor configuration topic is sent to HA. 
# The Sensor is configred based on a template stored in the config_template.json file
#
# All parameters are stored in the config.json file
#
# This script uses the Eclipse paho mqtt client library to communicate with the MQTT Broker, as well as the watchdog library to monitor file system changes.
# Both need to be installed using pip:
#    >pip install watchdog paho-mqtt
#
# For more detals see.
#   https://www.home-assistant.io/integrations/sensor.mqtt/
#   https://www.home-assistant.io/integrations/mqtt/#sensors
#
#
import json
import os
import subprocess
import datetime
import time
import re
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import paho.mqtt.client as mqtt

#
#
# Load configuration from JSON file
def load_config():
    with open('config.json', 'r') as config_file:
        return json.load(config_file)

#
# Load the configuation paramters from config.json
config = load_config()
mqtt_broker = config['mqtt_broker']
mqtt_port = config['mqtt_port']
monitoring_dir = config['monitoring_dir']
mqtt_username = config['mqtt_username']
mqtt_topic = config['mqtt_topic']
mqtt_password = config['mqtt_password']
# Would be a bit ore secure if he password where read from an ENV variable 
#    mqtt_password = os.getenv("MQTT_PASSWORD", "default_password")

# Get he list of already configured devices
tracked_devices = set(config['tracked_devices'])

# Regular Expression Pattern. Only interested in files matching this pattern. This pattern also defines the device_id used (Mac addr. of device)
# e.g. "gvh-(.+)-.+-.+.txt", will match on "gvh-A4C13876CC05-2024-02.txt" and return "A4C13876CC05" as the device_id
pattern = config['filename_regex']

# MQTT Client Setup and connect to the broker
client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
client.username_pw_set(mqtt_username, mqtt_password)
client.connect(mqtt_broker, mqtt_port, 60)


# Update config file with new device
def update_config(new_device):
    #
    # After a new device is discovered, keep track of it in the config.json file
    #
    global tracked_devices
    tracked_devices.add(new_device)
    config['tracked_devices'] = list(tracked_devices)
    with open('config.json', 'w') as config_file:
        json.dump(config, config_file, indent=4)
# end def()

def new_device_config(new_device):
    #
    # For details on the mqtt discovery see: https://www.home-assistant.io/integrations/mqtt/#sensors
    # Sensor template is defined in the config_template.json file

    # Prefix the DeviceID with "dl_" (for Datalogger)
    new_device_id = f"dl_{new_device}"


    # Load config templates
    with open('config_template.json', 'r') as template_file:
        templates = json.load(template_file)

    # homeassistant MQTT Integration needs one configuration topic for each "state attribute". A Template for is defined in config_template.json

    # See: https://www.home-assistant.io/integrations/mqtt/#discovery-payload
    # Discovery Topic:
    #       https://www.home-assistant.io/integrations/mqtt#discovery-topic        
    #       Here the Node is set to DeviceId, and the ObjectId is set to the key (e.g. temperatur) from the config_template.json file   

    # Make sure any old definition is deleted by putting an empty config payload on the queue
    for key, payload in reversed(templates.items()):
        # Create MQTT topic
        config_topic = f"{mqtt_topic}/{new_device_id}/{key}/config"
        client.publish(config_topic, payload=None, retain=True)
        print(f"Published: '<<None>>' to topic: {config_topic}")
        time.sleep(3) # sleep for 3 seconds to allow homeassitant to react, before sending next message
    #end for
        
    for key, payload in templates.items():
        # Replace ##DeviceId## with actual device ID

        payload_str = json.dumps(payload).replace("##DeviceId##", new_device_id)
        payload = json.loads(payload_str)

        # If you need to use the "json_attributes_template" please see examples in the "config_template_attr.json file
        # In the config file, define the json_attributes as normal json, it will be converted here to the string required by MQTT.sensor 
        # Special Case: json_attribute_template needs to be a string:
        # Handle json_attributes_template
        if 'json_attributes_template' in payload:
            json_attributes_template = payload['json_attributes_template']
            # Convert the dictionary to a JSON formatted string
            json_attributes_template_str = json.dumps(json_attributes_template)
            # Replace the dictionary with its string representation
            payload['json_attributes_template'] = json_attributes_template_str


        # Create MQTT topic
        config_topic = f"{mqtt_topic}/{new_device_id}/{key}/config"

        # Publish config message with retain flag to ensure configuration will survive HA restart
        payload_str = json.dumps(payload)
        client.publish(config_topic, payload=payload_str, retain=True)
        print(f"Published: {json.dumps(payload)} to topic: {config_topic}")
        time.sleep(5) # sleep for 5 seconds to allow homeassitant to react, before sending next message
    #end for
    update_config(new_device)
# end def()


last_timestamp = ""

# Handler for Watchdog
class FileChangeHandler(FileSystemEventHandler):
    def on_modified(self, event):
        global last_timestamp

        if not event.is_directory:
            file_path = event.src_path
            file_name = os.path.basename(file_path)

            # Check if the file name matches the pattern
            match = re.match(pattern, file_name)
            if match:
                device_id = match.group(1)  # Extract the device id

                # Check if the device is new and send config if necessary
                if device_id not in tracked_devices:
                    # Send config message for new device and update config.json
                    new_device_config(device_id)

                # Running 'tail -1' on the file
                last_line = subprocess.check_output(['tail', '-1', file_path]).decode().strip()

                # Parsing the line into a JSON object
                timestamp_str, temperature, humidity, battery = last_line.split('\t')

                # Convert timestamp to UNIX epoch time
                timestamp = datetime.datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S')
                epoch_timestamp = int(timestamp.replace(tzinfo=datetime.timezone.utc).timestamp())
                if not (epoch_timestamp == last_timestamp): # Check for duplicates (File observer could kick in twice)
                    last_timestamp = epoch_timestamp
                    data = {
                        "timestamp": epoch_timestamp,
                        "timestamp_str": str(timestamp_str),
                        "temperature": float(temperature),
                        "humidity": float(humidity),
                        "battery": int(battery)
                    }
                    json_payload_str = json.dumps(data)

                    # Publishing the JSON payload to MQTT. 
                    topic = f"{mqtt_topic}/dl_{device_id}/state"
                    client.publish(topic, payload=json_payload_str)

                    print(f"Published: {json_payload_str} to topic: {topic}")
    # end def()
# end class()

# Setting up Watchdog to monitor the given directory
observer = Observer()
observer.schedule(FileChangeHandler(), path=monitoring_dir, recursive=False)
observer.start()

# Infinite loop, until a keybaord interrupt (ctrl-c) is issues to stop the script
try:
    while True:
        pass
except KeyboardInterrupt:
    observer.stop()

# Gracefully close the mqtt client connection
observer.join()
client.disconnect()
