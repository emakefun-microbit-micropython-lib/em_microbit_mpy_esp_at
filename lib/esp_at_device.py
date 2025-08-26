from esp_at_stream_util import *
from esp_at_result_data import ResultData
import time
from microbit import *


__version__ = "1.0.0"


class EspAtDevice:
    def __init__(self, stream):
        self._stream = stream

        if not self.restart():
            while True:
                display.show(Image.NO)
                sleep(1000)

        at_commands = (
            "ATE0",
            "AT+CWINIT=1",
            "AT+CWMODE=1",
            "AT+CIPDINFO=1",
            "AT+CWAUTOCONN=0",
            "AT+CWDHCP=1,1",
        )

        for command in at_commands:
            self._stream.write(command + "\r\n")
            if not find_util(self._stream, "\r\nOK\r\n", 1000):
                while True:
                    display.show(Image.NO)
                    sleep(1000)

    @property
    def stream(self):
        return self._stream

    def restart(self):
        start_time = time.ticks_ms()
        while time.ticks_diff(time.ticks_ms(), start_time) < 5000:
            self._stream.write("AT+RST\r\n")
            if find_util(self._stream, "\r\nOK\r\n", 100) and find_util(
                self._stream, "\r\nready\r\n", 2000
            ):
                self._stream.write("AT\r\n")
                if find_util(self._stream, "\r\nOK\r\n", 100):
                    return True
            else:
                self.cancel_send()

        return False

    def cancel_send(self):
        time.sleep_ms(30)
        self._stream.write("+++")
        if find_util(self._stream, "\r\nSEND Canceled\r\n", 100):
            self._stream.write("\r\n")
            empty_rx(self._stream, 100)
            return False
        return True

    def wifi_connect(self, ssid: str, password: str):
        if not ssid or password is None:
            return False

        command = 'AT+CWJAP="{}","{}"'.format(ssid, password)
        self._stream.write(command + "\r\n")
        return find_util(self._stream, "\r\nOK\r\n", 20000)

    def get_ip_info(self):
        self._stream.write("AT+CIPSTA?\r\n")
        if not find_util(self._stream, '+CIPSTA:ip:"', 1000):
            return ResultData(False)

        ip = read_until(self._stream, '"', 1000)

        gateway = None
        if find_util(self._stream, '+CIPSTA:gateway:"', 100):
            gateway = read_until(self._stream, '"', 1000)

        netmask = None
        if find_util(self._stream, '+CIPSTA:netmask:"', 100):
            netmask = read_until(self._stream, '"', 1000)

        if find_util(self._stream, "\r\nOK\r\n", 100):
            return ResultData(True, ip=ip, gateway=gateway, netmask=netmask)

        return ResultData(False)

    def get_mac(self):
        self._stream.write("AT+CIPSTAMAC?\r\n")
        if not find_util(self._stream, '+CIPSTAMAC:"', 1000):
            return ResultData(False)

        mac = read_until(self._stream, '"', 1000)
        if find_util(self._stream, "\r\nOK\r\n", 100):
            return ResultData(True, mac=mac)

        return ResultData(False)

    def get_ap_info(self):
        self._stream.write("AT+CWJAP?\r\n")
        if not find_util(self._stream, '+CWJAP:"', 1000):
            return ResultData(False)

        ssid = read_until(self._stream, '"', 1000)
        if not skip_next(self._stream, ",", 1000) or not skip_next(
            self._stream, '"', 1000
        ):
            return ResultData(False)

        bssid = read_until(self._stream, '"', 1000)
        if not skip_next(self._stream, ",", 1000):
            return ResultData(False)

        channel = parse_int(self._stream, 1000)
        rssi = parse_int(self._stream, 1000)

        if find_util(self._stream, "\r\nOK\r\n", 100):
            return ResultData(True, ssid=ssid, bssid=bssid, channel=channel, rssi=rssi)
        return ResultData(False)

    def mqtt_user_config(
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

    def mqtt_connect(self, host: str, port: int, reconnect: bool):
        if not host or not 1 <= port <= 65535:
            return False

        command = 'AT+MQTTCONN=0,"{}",{},{}'.format(host, port, 1 if reconnect else 0)
        self._stream.write(command + "\r\n")
        return find_util(self._stream, "\r\nOK\r\n", 10000)

    def mqtt_publish(
        self,
        topic: str,
        data: str,
        qos: int,
        retain: bool,
    ):
        if not topic or data is None or not 0 <= qos <= 2:
            return False

        data_bytes = data.encode("utf-8")

        command = 'AT+MQTTPUBRAW=0,"{}",{},{},{}'.format(
            topic, len(data_bytes), qos, 1 if retain else 0
        )

        self._stream.write(command + "\r\n")
        if not find_util(self._stream, "\r\nOK\r\n\r\n>", 1000):
            return False

        self._stream.write(data_bytes)

        return find_util(self._stream, "+MQTTPUB:OK", 10000)

    def mqtt_subscribe(self, topic: str, qos: int):
        if not topic or not 0 <= qos <= 2:
            return False

        command = 'AT+MQTTSUB=0,"{}",{}'.format(topic, qos)
        self._stream.write(command + "\r\n")
        return find_util(self._stream, "\r\nOK\r\n", 1000)

    def mqtt_unsubscribe(self, topic: str):
        if not topic:
            return False
        command = 'AT+MQTTUNSUB=0,"{}"'.format(topic)
        self._stream.write(command + "\r\n")
        return find_util(self._stream, "\r\nOK\r\n", 1000)

    def mqtt_clean(self):
        self._stream.write("AT+MQTTCLEAN=0\r\n")
        return find_util(self._stream, "\r\nOK\r\n", 1000)

    def mqtt_receive(self):
        header = '+MQTTSUBRECV:0,"'
        if not find_util(self._stream, header, 5000):
            return ResultData(False)

        topic = read_until(self._stream, '"', 1000)

        if not skip_next(self._stream, ",", 1000):
            return ResultData(True, topic="", length=0)

        length = parse_int(self._stream, 1000)
        if length <= 0:
            return ResultData(True, topic="", length=0)
        return ResultData(True, topic=topic, length=length)
