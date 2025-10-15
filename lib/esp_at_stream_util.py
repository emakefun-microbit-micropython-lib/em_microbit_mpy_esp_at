import time

def multi_find_util(stream, targets: tuple, timeout_ms: int):
    byte_targets = [t.encode("utf-8") for t in targets]
    offsets = [0] * len(byte_targets)
    end_time = time.ticks_add(time.ticks_ms(), timeout_ms)
    while True:
        if stream.any():
            current_read_byte = stream.read(1)[0]
            for i in range(len(byte_targets)):
                target = byte_targets[i]
                offset = offsets[i]
                if current_read_byte == target[offset]:
                    offset += 1
                    if offset == len(target):
                        return i
                    offsets[i] = offset
                    continue

                if offset == 0:
                    continue

                original_offset = offset
                while offset > 0:
                    offset -= 1
                    if current_read_byte != target[offset]:
                        continue
                    if offset == 0:
                        offset += 1
                        break
                    for j in range(offset):
                        if target[j] != target[j + original_offset - offset]:
                            break
                    if j == offset - 1:
                        offset += 1
                offsets[i] = offset
        if time.ticks_diff(time.ticks_ms(), end_time) >= 0:
            return None


def skip_next(stream, target: str, timeout_ms: int):
    end_time = time.ticks_add(time.ticks_ms(), timeout_ms)
    while True:
        if stream.any():
            return stream.read(1)[0] == ord(target)
        if time.ticks_diff(time.ticks_ms(), end_time) >= 0:
            return False


def read_until(stream, delimiter: str, timeout_ms: int):
    received_data = bytearray()
    end_time = time.ticks_add(time.ticks_ms(), timeout_ms)
    while True:
        if stream.any():
            current_read_byte = stream.read(1)[0]
            if current_read_byte == ord(delimiter):
                if len(received_data) == 0:
                    return None
                return received_data.decode("utf-8")
            received_data.append(current_read_byte)
        if time.ticks_diff(time.ticks_ms(), end_time) >= 0:
            return None


def parse_int(stream, timeout_ms: int):
    num_bytes = bytearray()
    end_time = time.ticks_add(time.ticks_ms(), timeout_ms)
    while True:
        if stream.any():
            current_read_byte = stream.read(1)[0]
            if ord("0") <= current_read_byte <= ord("9") or (
                current_read_byte == ord("-") and not num_bytes
            ):
                num_bytes.append(current_read_byte)
            else:
                break
        if time.ticks_diff(time.ticks_ms(), end_time) >= 0:
            return None
    if len(num_bytes) > 0 and not (len(num_bytes) == 1 and num_bytes[0] == ord("-")):
        return int(num_bytes.decode("utf-8"))
    else:
        return None
