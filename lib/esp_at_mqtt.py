from esp_at_stream_util import *
from micropython import const

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
        command = 'AT+MQTTUSERCFG=0,{},"{}","{}","{}",0,0,"{}"'.format(
            scheme, client_id, username, password, path
        )
        return self._send_command(command, "\r\nOK\r\n", 500)

    def connect_mqtt(self, host: str, port: int, reconnect: bool):
        command = 'AT+MQTTCONN=0,"{}",{},{}'.format(host, port, 1 if reconnect else 0)
        return self._send_command(command, "\r\nOK\r\n", 10000)

    def publish(self, topic: str, data: str, qos: int, retain: bool, timeout_ms: int):
        data_bytes = data.encode("utf-8")
        command = 'AT+MQTTPUBRAW=0,"{}",{},{},{}'.format(
            topic, len(data_bytes), qos, 1 if retain else 0
        )
        if not self._send_command(command, "\r\nOK\r\n\r\n>", 500):
            return False
        self._stream.write(data_bytes)
        targets = (
            "+MQTTPUB:OK",
            "+MQTTPUB:FAIL",
        )
        return multi_find_util(self._stream, targets, timeout_ms) == 0

    def subscribe(self, topic: str, qos: int):
        command = 'AT+MQTTSUB=0,"{}",{}'.format(topic, qos)
        return self._send_command(command, "\r\nOK\r\n", 500)

    def receive(self, timeout_ms: int):
        if multi_find_util(self._stream, ('+MQTTSUBRECV:0,"',), timeout_ms) != 0:
            return ("", 0)
        topic = read_until(self._stream, '"', 500)
        if topic is None or not skip_next(self._stream, ",", 500):
            return ("", 0)
        length = parse_int(self._stream, 500)
        if length is None or length <= 0:
            return ("", 0)
        return (topic, length)
