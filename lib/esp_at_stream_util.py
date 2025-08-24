import time


def find_util(stream, targets: tuple, timeout_ms: int):
    if not targets or timeout_ms <= 0:
        return -1

    byte_targets = []
    for target in targets:
        if isinstance(target, str):
            byte_targets.append(target.encode("utf-8"))
        else:
            byte_targets.append(target)

    offsets = [0] * len(byte_targets)
    end_time = time.ticks_add(time.ticks_ms(), timeout_ms)

    while time.ticks_diff(end_time, time.ticks_ms()) > 0:
        if not stream.any():
            continue

        current_char = stream.read(1)[0]
        for i in range(len(byte_targets)):
            target = byte_targets[i]
            offset = offsets[i]

            if current_char == target[offset]:
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
                if current_char != target[offset]:
                    continue
                offset_diff = original_offset - offset
                matched = True
                for j in range(offset):
                    if target[j] != target[j + offset_diff]:
                        matched = False
                        break
                if matched:
                    offset += 1
                    break
            offsets[i] = offset

    return -1


def skip_next(stream, target_char: str, timeout_ms: int):
    if not target_char:
        return False
    
    end_time = time.ticks_add(time.ticks_ms(), timeout_ms)
    while stream.any() == 0:
        if time.ticks_diff(time.ticks_ms(), end_time) >= 0:
            return False  
        time.sleep_ms(1)  

    current_char = stream.read(1).decode("utf-8")
    return current_char == target_char


def empty_rx(stream, duration_ms: int):
    if duration_ms < 0:
        return False
    start_time = time.ticks_ms()

    while True:
        while stream.any() > 0:
            stream.read(1)

        if time.ticks_diff(time.ticks_ms(), start_time) >= duration_ms:
            break
    return True


def read_until(stream, delimiter: str, timeout_ms: int):
    result = ""
    end_time = time.ticks_add(time.ticks_ms(), timeout_ms)

    while True:
        if time.ticks_diff(time.ticks_ms(), end_time) >= 0:
            break

        if stream.any() <= 0:
            time.sleep_ms(10)
            continue  

        current_char = stream.read(1).decode("utf-8")
        if not current_char:
            continue

        if current_char == delimiter:
            break
        result += current_char
        
    return result


def parse_int(stream, timeout_ms: int):
    num_str = ""
    end_time = time.ticks_add(time.ticks_ms(), timeout_ms)

    while True:
        if time.ticks_diff(time.ticks_ms(), end_time) >= 0:
            break
        if stream.any() <= 0:
            time.sleep_ms(10)
            continue

        current_char = stream.read(1).decode("utf-8")

        if current_char in (",", "\r", "\n"):
            break

        if current_char.isdigit() or (current_char == "-" and not num_str):
            num_str += current_char
        else:
            break

    if not num_str or num_str == "-":
        return 0
    return int(num_str)
