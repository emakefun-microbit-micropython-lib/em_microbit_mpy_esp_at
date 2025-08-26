import time


def find_util(stream, target: str, timeout_ms: int):
    if not target or timeout_ms <= 0:
        return False

    byte_target = target.encode("utf-8")
    offset = 0
    end_time = time.ticks_add(time.ticks_ms(), timeout_ms)
    target_len = len(byte_target)

    while time.ticks_diff(time.ticks_ms(), end_time) < 0:
        if not stream.any():
            continue

        current_char = stream.read(1)[0]

        if current_char == byte_target[offset]:
            offset += 1
            if offset == target_len:
                return True
            continue

        if offset > 0:
            original_offset = offset
            for new_offset in range(offset - 1, -1, -1):
                if current_char == byte_target[new_offset]:
                    offset_diff = original_offset - new_offset
                    if all(
                        byte_target[j] == byte_target[j + offset_diff]
                        for j in range(new_offset)
                    ):
                        offset = new_offset + 1
                        break
            else:
                offset = 0

    return False


def skip_next(stream, target_char: str, timeout_ms: int):
    if not target_char or timeout_ms <= 0:
        return False

    end_time = time.ticks_add(time.ticks_ms(), timeout_ms)
    while stream.any() == 0:
        if time.ticks_diff(time.ticks_ms(), end_time) >= 0:
            return False
        time.sleep_ms(1)

    return target_char == stream.read(1).decode("utf-8")


def empty_rx(stream, duration_ms: int):
    if duration_ms < 0:
        return False
    start_time = time.ticks_ms()

    while time.ticks_diff(time.ticks_ms(), start_time) < duration_ms:
        while stream.any() > 0:
            stream.read(1)
    return True


def read_until(stream, delimiter: str, timeout_ms: int):
    if not delimiter:
        return ""

    result = ""
    end_time = time.ticks_add(time.ticks_ms(), timeout_ms)

    while time.ticks_diff(time.ticks_ms(), end_time) < 0:
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

    while time.ticks_diff(time.ticks_ms(), end_time) < 0:
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

    return int(num_str) if num_str and num_str != "-" else 0
