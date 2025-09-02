from microbit import *
import time
from micropython import const
import esp_at_manager
import esp_at_mqtt
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
esp_at_manager = esp_at_manager.EspAtManager(uart)

last_publish_time = 0

if not esp_at_manager.wifi.connect_wifi(WIFI_SSID, WIFI_PASSWORD):
    raise Exception("Error: WiFi connection failed.")

mqtt = esp_at_manager.mqtt
if not mqtt.user_config(
    esp_at_mqtt.OVER_TCP, MQTT_CLIENT_ID, MQTT_USER_NAME, MQTT_PASSWORD, MQTT_PATH
):
    raise Exception("Error: MQTT configuration failed.")

if not mqtt.connect_mqtt(MQTT_BROKER, MQTT_PORT, True):
    raise Exception("Error: MQTT connection failed.")

if not mqtt.subscribe(MQTT_TOPIC, 0):
    raise Exception("Error: MQTT subscription failed.")

display.show(Image.HAPPY)
while True:
    topic, length = mqtt.receive(100)
    if topic != "":
        end_time = time.ticks_add(time.ticks_ms(), 200)
        received_data = bytearray()
        while True:
            remaining = length - len(received_data)
            if remaining <= 0:
                break
            data = mqtt.stream.read(remaining)
            if data is not None:
                received_data.extend(data)
            if time.ticks_diff(time.ticks_ms(), end_time) >= 0:
                break
        if topic == MQTT_TOPIC and len(received_data) == length:
            if received_data.decode("utf-8") == "display on":
                display.on()
            else:
                display.off()

    if time.ticks_ms() - last_publish_time > 1000:
        send_content = "display off" if display.is_on() else "display on"
        if not mqtt.publish(MQTT_TOPIC, send_content, 0, False, 1000):
            raise Exception("Error: MQTT publish content failed.")
        last_publish_time = time.ticks_ms()
