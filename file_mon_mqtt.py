import os
import subprocess
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import paho.mqtt.client as mqtt

# pip install watchdog paho-mqtt


# MQTT Broker settings
mqtt_broker = "localhost"  # Change to your MQTT broker address
mqtt_port = 1883  # Change if your MQTT broker uses a different port
mqtt_topic = "datalogger/{}"  # Topic format

# Directory to monitor
monitoring_dir = "/path/to/your/directory"  # Change to your directory path

# MQTT Client Setup
client = mqtt.Client()
client.connect(mqtt_broker, mqtt_port, 60)

# Handler for Watchdog
class FileChangeHandler(FileSystemEventHandler):
    def on_modified(self, event):
        if not event.is_directory:
            file_path = event.src_path
            file_name = os.path.basename(file_path)
            topic = mqtt_topic.format(file_name)

            # Running 'tail -1' on the file
            last_line = subprocess.check_output(['tail', '-1', file_path]).decode().strip()

            # Publishing the last line to MQTT
            client.publish(topic, last_line)
            print(f"Published: {last_line} to topic: {topic}")

# Setting up Watchdog
observer = Observer()
observer.schedule(FileChangeHandler(), path=monitoring_dir, recursive=False)
observer.start()

try:
    while True:
        pass
except KeyboardInterrupt:
    observer.stop()
observer.join()
client.disconnect()
