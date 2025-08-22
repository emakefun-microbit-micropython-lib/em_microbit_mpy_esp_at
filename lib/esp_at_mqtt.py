from stream_util import *
from result_code import ResultCode
from result_data import ResultData
from micropython import const

__version__ = "1.0.0"


class EspAtMqtt:
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

    def __init__(self, stream):
        self._stream = stream

    def _send_command(self, command: str, timeout: int, success_target: str):
        if not command or not success_target or timeout < 0:
            return ResultCode.ERROR

        self._stream.write(command + "\r\n")
        targets = [success_target, "\r\nERROR\r\n", "busy p...\r\n"]
        index = find_util(self._stream, targets, timeout)

        if index == 0:
            return ResultCode.OK
        elif index == 1:
            return ResultCode.ERROR
        elif index == 2:
            return ResultCode.BUSY
        else:
            return ResultCode.TIMEDOUT

    def get_stream(self):
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
            return ResultCode.INVALID_PARAMETERS

        if client_id is None or username is None or password is None or path is None:
            return ResultCode.INVALID_PARAMETERS

        if (
            len(client_id.encode("utf-8")) > 256
            or len(username.encode("utf-8")) > 64
            or len(password.encode("utf-8")) > 64
            or len(path.encode("utf-8")) > 32
        ):
            return ResultCode.INVALID_PARAMETERS

        command = 'AT+MQTTUSERCFG=0,{},"{}","{}","{}",0,0,"{}"'.format(
            scheme, client_id, username, password, path
        )
        return self._send_command(command, 1000, "\r\nOK\r\n")

    def connect(self, host: str, port: int, reconnect: bool):
        if not host or len(host.encode("utf-8")) > 128 or not 1 <= port <= 65535:
            return ResultCode.INVALID_PARAMETERS

        command = 'AT+MQTTCONN=0,"{}",{},{}'.format(host, port, 1 if reconnect else 0)
        return self._send_command(command, 10000, "\r\nOK\r\n")

    def aliyun_connect(
        self,
        host: str,
        port: int,
        product_key: str,
        device_name: str,
        device_secret: str,
    ):
        if (
            not all([host, product_key, device_name, device_secret])
            or len(host.encode("utf-8")) > 128
            or not 1 <= port <= 65535
        ):
            return ResultCode.INVALID_PARAMETERS

        command = 'AT+ALIYUN_MQTTCONN="{}",{},"{}","{}","{}"'.format(
            host, port, product_key, device_name, device_secret
        )
        return self._send_command(command, 10000, "\r\nOK\r\n")

    def publish(
        self,
        topic: str,
        data: str,
        qos: int,
        retain: bool,
    ):
        if (
            not topic
            or len(topic.encode("utf-8")) > 128
            or data is None
            or not 0 <= qos <= 2
        ):
            return ResultCode.INVALID_PARAMETERS

        data_bytes = data.encode("utf-8")

        command = 'AT+MQTTPUBRAW=0,"{}",{},{},{}'.format(
            topic, len(data_bytes), qos, 1 if retain else 0
        )
        send_result = self._send_command(command, 1000, "\r\nOK\r\n\r\n>")
        if send_result != ResultCode.OK:
            return send_result

        self._stream.write(data_bytes)

        targets = ["+MQTTPUB:OK", "+MQTTPUB:FAIL"]
        index = find_util(self._stream, targets, 10000)
        if index == 0:
            return ResultCode.OK
        elif index == 1:
            return ResultCode.ERROR
        else:
            return ResultCode.TIMEDOUT

    def subscribe(self, topic: str, qos: int):
        if not topic or len(topic.encode("utf-8")) > 128 or not 0 <= qos <= 2:
            return ResultCode.INVALID_PARAMETERS

        command = 'AT+MQTTSUB=0,"{}",{}'.format(topic, qos)
        return self._send_command(command, 1000, "\r\nOK\r\n")

    def unsubscribe(self, topic: str):
        if not topic or len(topic.encode("utf-8")) > 128:
            return ResultCode.INVALID_PARAMETERS
        command = 'AT+MQTTUNSUB=0,"{}"'.format(topic)
        return self._send_command(command, 1000, "\r\nOK\r\n")

    def clean(self):
        return self._send_command("AT+MQTTCLEAN=0", 1000, "\r\nOK\r\n")

    def receive(self):
        header = '+MQTTSUBRECV:0,"'
        if find_util(self._stream, [header], 5000) < 0:
            return ResultData(ResultCode.TIMEDOUT)

        topic = read_until(self._stream, '"')

        if not skip_next(self._stream, ","):
            return ResultData(ResultCode.OK, topic="", length=0)

        length = parse_int(self._stream)
        if length <= 0:
            return ResultData(ResultCode.OK, topic="", length=0)
        return ResultData(ResultCode.OK, topic=topic, length=length)
