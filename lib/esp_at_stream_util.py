import time


def multi_find_util(stream, targets: tuple, timeout_ms: int):
    if not targets or timeout_ms < 0:
        raise ValueError("Error: 'multi_find_util' function, invalid parameters.")
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
                    offset_diff = original_offset - offset
                    for j in range(offset):
                        if target[j] != target[j + offset_diff]:
                            break
                    if j == offset - 1:
                        offset += 1
                        break
                offsets[i] = offset
        if time.ticks_diff(time.ticks_ms(), end_time) >= 0:
            return None


def single_find_util(stream, target: str, timeout_ms: int):
    if target is None or target == "" or timeout_ms < 0:
        raise ValueError("Error: 'single_find_util' function, invalid parameters.")

    byte_target = target.encode("utf-8")
    offset = 0
    end_time = time.ticks_add(time.ticks_ms(), timeout_ms)
    while True:
        if stream.any():
            current_read_byte = stream.read(1)[0]
            if current_read_byte == byte_target[offset]:
                offset += 1
                if offset == len(byte_target):
                    return True
                continue
            original_offset = offset
            while offset > 0:
                offset -= 1
                if current_read_byte != byte_target[offset]:
                    continue

                if offset == 0:
                    offset += 1
                    break

                offset_diff = original_offset - offset
                for j in range(offset):
                    if target[j] != target[j + offset_diff]:
                        break
                if j == offset - 1:
                    offset += 1
                    break
        if time.ticks_diff(time.ticks_ms(), end_time) >= 0:
            return False


def skip_next(stream, target: str, timeout_ms: int):
    if target is None or target == "" or timeout_ms < 0:
        raise ValueError("Error: 'skip_next' function, invalid parameters.")
    end_time = time.ticks_add(time.ticks_ms(), timeout_ms)
    while True:
        if stream.any():
            return stream.read(1)[0] == ord(target)
        if time.ticks_diff(time.ticks_ms(), end_time) >= 0:
            return False


def read_until(stream, delimiter: str, timeout_ms: int):
    if delimiter is None or delimiter == "" or timeout_ms < 0:
        raise ValueError("Error: 'read_until' function, invalid parameters.")
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
    if timeout_ms < 0:
        raise ValueError("Error: 'parse_int' function, invalid parameter.")
    num_bytes = bytearray()
    end_time = time.ticks_add(time.ticks_ms(), timeout_ms)
    while True:
        if stream.any():
            current_read_byte = stream.read(1)[0]
            if current_read_byte in (ord(","), ord("\r"), ord("\n")):
                break
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
