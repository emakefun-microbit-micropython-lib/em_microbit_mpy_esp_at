from microbit import *
import time
from micropython import const
from esp_at_device import EspAtDevice

WIFI_SSID: str = "emakefun"
WIFI_PASSWORD: str = "501416wf"

MQTT_SCHEME: int = const(1)
MQTT_CLIENT_ID: str = "my_client_id"
MQTT_USER_NAME: str = "my_user_name"
MQTT_PASSWORD: str = "my_password"
MQTT_PATH: str = ""

MQTT_BROKER: str = "broker.emqx.io"
MQTT_PORT: int = const(1883)
MQTT_TOPIC: str = "emakefun/sensor/testtopic"


def show_error():
    while True:
        display.show(Image.NO)
        sleep(1000)


uart.init(baudrate=9600, bits=8, parity=None, stop=1, tx=pin1, rx=pin0)
esp_at_device = EspAtDevice(uart)

last_publish_time = 0

if not esp_at_device.wifi_connect(WIFI_SSID, WIFI_PASSWORD):
    show_error()

if not esp_at_device.mqtt_user_config(
    MQTT_SCHEME, MQTT_CLIENT_ID, MQTT_USER_NAME, MQTT_PASSWORD, MQTT_PATH
):
    show_error()

if not esp_at_device.mqtt_connect(MQTT_BROKER, MQTT_PORT, True):
    show_error()

if not esp_at_device.mqtt_subscribe(MQTT_TOPIC, 0):
    show_error()

while True:
    received_result = esp_at_device.mqtt_receive()
    if received_result.success and received_result.length > 0:
        display.show(Image.SKULL)
        while esp_at_device.stream.any():
            read_char = esp_at_device.stream.read()

    current_time = time.ticks_ms()
    if current_time - last_publish_time > 3000:
        display.show(Image.TARGET)
        content = "test message with timestamp:" + str(current_time)
        if esp_at_device.mqtt_publish(MQTT_TOPIC, content, 0, False):
            display.show(Image.YES)
        else:
            show_error()
        last_publish_time = time.ticks_ms()
