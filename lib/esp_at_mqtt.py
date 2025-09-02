from esp_at_stream_util import *
from micropython import const


__version__ = "1.0.0"

# <scheme>：
OVER_TCP: int = const(1)
OVER_TLS_NO_VERIFY: int = const(2)
OVER_TLS_VERIFY_SERVER_CERT: int = const(3)
OVER_TLS_PROVIDE_CLIENT_CERT: int = const(4)
OVER_TLS_MUTUAL_VERIFY: int = const(5)
OVER_WEB_SOCKET: int = const(6)
OVER_WS_SECURE_NO_VERIFY: int = const(7)
OVER_WS_SECURE_VERIFY_SERVER_CERT: int = const(8)
OVER_WS_SECURE_PROVIDE_CLIENT_CERT: int = const(9)
OVER_WS_SECURE_MUTUAL_VERIFY: int = const(10)


class EspAtMqtt:
    def __init__(self, stream):
        self._stream = stream

    @property
    def stream(self):
        return self._stream

    def _send_command(self, command: str, success_target: str, timeout_ms: int):
        if not command or not success_target or timeout_ms < 0:
            return False
        self._stream.write(command + "\r\n")
        targets = (
            success_target,
            "\r\nERROR\r\n",
            "busy p...\r\n",
        )
        return multi_find_util(self._stream, targets, timeout_ms) == 0

    def user_config(
        self,
        scheme: int,
        client_id: str,
        username: str,
        password: str,
        path: str,
    ):
        if not 1 <= scheme <= 10 or None in {client_id, username, password, path}:
            raise ValueError("mqtt user config,invalid scheme parameter.")
        command = 'AT+MQTTUSERCFG=0,{},"{}","{}","{}",0,0,"{}"'.format(
            scheme, client_id, username, password, path
        )
        return self._send_command(command, "\r\nOK\r\n", 500)

    def connect_mqtt(self, host: str, port: int, reconnect: bool):
        if not host or not 1 <= port <= 65535:
            raise ValueError("connect mqtt,invalid parameters.")
        command = 'AT+MQTTCONN=0,"{}",{},{}'.format(host, port, 1 if reconnect else 0)
        return self._send_command(command, "\r\nOK\r\n", 10000)

    def publish(self, topic: str, data: str, qos: int, retain: bool, timeout_ms: int):
        if not topic or data is None or not 0 <= qos <= 2 or timeout_ms < 0:
            raise ValueError("mqtt publish message,invalid parameters.")

        data_bytes = data.encode("utf-8")
        command = 'AT+MQTTPUBRAW=0,"{}",{},{},{}'.format(
            topic, len(data_bytes), qos, 1 if retain else 0
        )
        if not self._send_command(command, "\r\nOK\r\n\r\n>", 500):
            return False
        self._stream.write(data_bytes)
        return single_find_util(self._stream, "+MQTTPUB:OK", timeout_ms)

    def subscribe(self, topic: str, qos: int):
        if not topic or not 0 <= qos <= 2:
            raise ValueError("mqtt subscribe topic,invalid parameters.")
        command = 'AT+MQTTSUB=0,"{}",{}'.format(topic, qos)
        return self._send_command(command, "\r\nOK\r\n", 500)

    def unsubscribe(self, topic: str):
        if not topic:
            raise ValueError("mqtt unsubscribe topic,invalid topic parameter.")
        return self._send_command(
            'AT+MQTTUNSUB=0,"{}"'.format(topic), "\r\nOK\r\n", 500
        )

    def clean(self):
        return self._send_command("AT+MQTTCLEAN=0", "\r\nOK\r\n", 500)

    def receive(self, timeout_ms: int):
        if timeout_ms < 0:
            raise ValueError("mqtt receive message,invalid timeout_ms parameter.")

        header = '+MQTTSUBRECV:0,"'
        if not single_find_util(self._stream, header, timeout_ms):
            return (None, 0)

        topic = read_until(self._stream, '"', 500)
        if not topic or not skip_next(self._stream, ",", 500):
            return (None, 0)

        length = parse_int(self._stream, 500)
        if length is None or length <= 0:
            return (None, 0)
        return (topic, length)
