from esp_at_stream_util import *
from micropython import const


__version__ = "1.0.0"

# <scheme>：
MQTT_OVER_TCP: int = const(1)
MQTT_OVER_TLS_NO_VERIFY: int = const(2)
MQTT_OVER_TLS_VERIFY_SERVER_CERT: int = const(3)
MQTT_OVER_TLS_PROVIDE_CLIENT_CERT: int = const(4)
MQTT_OVER_TLS_MUTUAL_VERIFY: int = const(5)
MQTT_OVER_WEB_SOCKET: int = const(6)
MQTT_OVER_WS_SECURE_NO_VERIFY: int = const(7)
MQTT_OVER_WS_SECURE_VERIFY_SERVER_CERT: int = const(8)
MQTT_OVER_WS_SECURE_PROVIDE_CLIENT_CERT: int = const(9)
MQTT_OVER_WS_SECURE_MUTUAL_VERIFY: int = const(10)


class EspAtMqtt:
    def __init__(self, stream):
        self._stream = stream

    @property
    def stream(self):
        return self._stream

    def user_config(
        self,
        scheme: int,
        client_id: str,
        username: str,
        password: str,
        path: str,
    ):
        if not 1 <= scheme <= 10:
            return False

        if client_id is None or username is None or password is None or path is None:
            return False

        command = 'AT+MQTTUSERCFG=0,{},"{}","{}","{}",0,0,"{}"'.format(
            scheme, client_id, username, password, path
        )
        self._stream.write(command + "\r\n")
        return find_util(self._stream, "\r\nOK\r\n", 1000)

    def connect_mqtt(self, host: str, port: int, reconnect: bool, timeout_ms: int):
        if not host or not 1 <= port <= 65535 or timeout_ms <= 0:
            return False

        command = 'AT+MQTTCONN=0,"{}",{},{}'.format(host, port, 1 if reconnect else 0)
        self._stream.write(command + "\r\n")
        return find_util(self._stream, "\r\nOK\r\n", timeout_ms)

    def publish(self, topic: str, data: str, qos: int, retain: bool, timeout_ms: int):
        if not topic or data is None or not 0 <= qos <= 2 or timeout_ms <= 0:
            return False

        data_bytes = data.encode("utf-8")

        command = 'AT+MQTTPUBRAW=0,"{}",{},{},{}'.format(
            topic, len(data_bytes), qos, 1 if retain else 0
        )

        self._stream.write(command + "\r\n")
        if not find_util(self._stream, "\r\nOK\r\n\r\n>", 1000):
            return False

        self._stream.write(data_bytes)

        return find_util(self._stream, "+MQTTPUB:OK", timeout_ms)

    def subscribe(self, topic: str, qos: int):
        if not topic or not 0 <= qos <= 2:
            return False

        command = 'AT+MQTTSUB=0,"{}",{}'.format(topic, qos)
        self._stream.write(command + "\r\n")
        return find_util(self._stream, "\r\nOK\r\n", 1000)

    def unsubscribe(self, topic: str):
        if not topic:
            return False
        command = 'AT+MQTTUNSUB=0,"{}"'.format(topic)
        self._stream.write(command + "\r\n")
        return find_util(self._stream, "\r\nOK\r\n", 1000)

    def clean(self):
        self._stream.write("AT+MQTTCLEAN=0\r\n")
        return find_util(self._stream, "\r\nOK\r\n", 1000)

    def receive(self, timeout_ms: int):
        if timeout_ms <= 0:
            return (None, 0)

        header = '+MQTTSUBRECV:0,"'
        if not find_util(self._stream, header, timeout_ms):
            return (None, 0)

        topic = read_until(self._stream, '"', 1000)

        if not skip_next(self._stream, ",", 1000):
            return (None, 0)

        length = parse_int(self._stream, 1000)
        if length <= 0:
            return (None, 0)
        return (topic, length)
