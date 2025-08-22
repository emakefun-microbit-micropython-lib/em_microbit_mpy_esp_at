from stream_util import *
from result_code import ResultCode
from result_data import ResultData

__version__ = "1.0.0"


class EspAtWifi:
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

    def connect_wifi(self, ssid: str, password: str):
        if (
            not ssid
            or len(ssid.encode("utf-8")) > 32
            or password is None
            or len(password.encode("utf-8")) > 64
        ):
            return ResultCode.INVALID_PARAMETERS

        command = 'AT+CWJAP="{}","{}"'.format(ssid, password)
        return self._send_command(command, 20000, "\r\nOK\r\n")

    def get_ip_info(self):
        send_result = self._send_command("AT+CIPSTA?", 1000, '+CIPSTA:ip:"')
        if send_result != 0:
            return ResultData(send_result)

        ip = read_until(self._stream, '"')

        gateway = None
        if find_util(self._stream, ['+CIPSTA:gateway:"'], 100) == 0:
            gateway = read_until(self._stream, '"')

        netmask = None
        if find_util(self._stream, ['+CIPSTA:netmask:"'], 100) == 0:
            netmask = read_until(self._stream, '"')

        if find_util(self._stream, ["\r\nOK\r\n"], 100) == 0:
            return ResultData(ResultCode.OK, ip=ip, gateway=gateway, netmask=netmask)

        return ResultData(ResultCode.ERROR)

    def get_mac(self):
        send_result = self._send_command("AT+CIPSTAMAC?", 1000, '+CIPSTAMAC:"')
        if send_result != 0:
            return ResultData(send_result)

        mac = read_until(self._stream, '"')
        if find_util(self._stream, ["\r\nOK\r\n"], 100) == 0:
            return ResultData(ResultCode.OK, mac=mac)

        return ResultData(ResultCode.ERROR)

    def get_ap_info(self):
        send_result = self._send_command("AT+CWJAP?", 1000, '+CWJAP:"')
        if send_result != 0:
            return ResultData(send_result)

        ssid = read_until(self._stream, '"')
        if not skip_next(self._stream, ",") or not skip_next(self._stream, '"'):
            return ResultData(ResultCode.ERROR)

        bssid = read_until(self._stream, '"')
        if not skip_next(self._stream, ","):
            return ResultData(ResultCode.ERROR)

        channel = parse_int(self._stream)
        rssi = parse_int(self._stream)

        if find_util(self._stream, ["\r\nOK\r\n"], 100) == 0:
            return ResultData(
                ResultCode.OK, ssid=ssid, bssid=bssid, channel=channel, rssi=rssi
            )
        return ResultData(ResultCode.ERROR)
