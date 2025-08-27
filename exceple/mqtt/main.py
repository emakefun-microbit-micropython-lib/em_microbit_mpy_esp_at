from microbit import *
import time
from micropython import const
from esp_at_manager import EspAtManager
from esp_at_mqtt import *
import machine

WIFI_SSID: str = "emakefun"
WIFI_PASSWORD: str = "501416wf"

MQTT_CLIENT_ID: str = "my_client_id"
MQTT_USER_NAME: str = "my_user_name"
MQTT_PASSWORD: str = "my_password"
MQTT_PATH: str = ""

MQTT_BROKER: str = "broker.emqx.io"
MQTT_PORT: int = const(1883)

device_id = "".join("{:02x}".format(b) for b in machine.unique_id())
MQTT_TOPIC = "emakefun/sensor/{}/testtopic".format(device_id)

uart.init(baudrate=9600, bits=8, parity=None, stop=1, tx=pin1, rx=pin0)
esp_at_manager = EspAtManager(uart)

last_publish_time = 0
last_sent_message = ""

if not esp_at_manager.wifi.connect_wifi(WIFI_SSID, WIFI_PASSWORD, 10000):
    raise Exception("WiFi connection failed")

mqtt = esp_at_manager.mqtt

if not mqtt.user_config(
    MQTT_OVER_TCP, MQTT_CLIENT_ID, MQTT_USER_NAME, MQTT_PASSWORD, MQTT_PATH
):
    raise Exception("MQTT configuration failed")

if not mqtt.connect_mqtt(MQTT_BROKER, MQTT_PORT, True, 10000):
    raise Exception("MQTT connection failed")

if not mqtt.subscribe(MQTT_TOPIC, 0):
    raise Exception("MQTT subscription failed")

while True:
    topic, length = mqtt.receive(5000)
    if length > 0:
        display.show(Image.SKULL)
        remaining_length = length
        data = bytearray()
        while remaining_length > 0:
            if mqtt.stream.any():
                data.extend(mqtt.stream.read(1))
                remaining_length -= 1

        if data.decode("utf-8") == last_sent_message:
            display.show(Image.HAPPY)
        else:
            display.show(Image.SAD)

    current_time = time.ticks_ms()
    if current_time - last_publish_time > 3000:
        display.show(Image.TARGET)
        send_content = "test message with timestamp:" + str(current_time)
        if mqtt.publish(MQTT_TOPIC, send_content, 0, False, 10000):
            display.show(Image.YES)
            last_sent_message = send_content
        else:
            display.show(Image.NO)
        last_publish_time = time.ticks_ms()
