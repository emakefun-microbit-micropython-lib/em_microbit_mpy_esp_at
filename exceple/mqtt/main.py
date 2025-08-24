from microbit import *
import time
import urandom
from micropython import const
from esp_at_manager import EspAtManager
from esp_at_result_code import ResultCode

WIFI_SSID: str = "emakefun"
WIFI_PASSWORD: str = "501416wf"

MQTT_CLIENT_ID: str = "my_client_id"
MQTT_USER_NAME: str = "my_user_name"
MQTT_PASSWORD: str = "my_password"
MQTT_PATH: str = ""

MQTT_BROKER: str = "broker.emqx.io"
MQTT_PORT: int = const(1883)

urandom.seed(time.ticks_ms())
test_topic = "emakefun/sensor/" + str(urandom.getrandbits(16)) + "/timestamp"

uart.init(baudrate=9600, bits=8, parity=None, stop=1, tx=pin1, rx=pin0)
esp_at_manager = EspAtManager(uart)

last_publish_time = 0

while uart.any():
    uart.read()

wifi_result = esp_at_manager.wifi.connect_wifi(WIFI_SSID, WIFI_PASSWORD)
if wifi_result != ResultCode.OK:
    print("wifi connect failed: " + ResultCode.to_string(wifi_result))
    while True:
        display.show(Image.NO)
        sleep(1000)


mqtt = esp_at_manager.mqtt

config_result = mqtt.user_config(
    mqtt.MQTT_OVER_TCP, MQTT_CLIENT_ID, MQTT_USER_NAME, MQTT_PASSWORD, MQTT_PATH
)
if config_result != ResultCode.OK:
    print("mqtt config failed: " + ResultCode.to_string(config_result))
    while True:
        display.show(Image.NO)
        sleep(1000)

connect_result = mqtt.connect(MQTT_BROKER, MQTT_PORT, True)
if connect_result != ResultCode.OK:
    print("mqtt connect failed: " + ResultCode.to_string(connect_result))
    while True:
        display.show(Image.NO)
        sleep(1000)


subscribe_result = mqtt.subscribe(test_topic, 0)
if subscribe_result != ResultCode.OK:
    print("mqtt subscribe failed: " + ResultCode.to_string(subscribe_result))
    while True:
        display.show(Image.NO)
        sleep(1000)

while True:
    received_result = mqtt.receive()
    if received_result.is_ok and received_result.length > 0:
        display.scroll("1")
        remaining_length = received_result.length
        while remaining_length > 0:
            if mqtt.get_stream().any():
                read_char = mqtt.get_stream().read(1)
                remaining_length -= 1

    current_time = time.ticks_ms()
    if current_time - last_publish_time > 3000:
        display.scroll("2")
        content = "test message with timestamp:" + str(current_time)
        publish_result = mqtt.publish(test_topic, content, 0, False)
        if publish_result == ResultCode.OK:
            display.show(Image.YES)
        else:
            display.show(Image.NO)
        last_publish_time = time.ticks_ms()
