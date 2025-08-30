import time


def find_util(stream, targets, timeout_ms: int):
    if not targets or not isinstance(targets, (str, tuple)) or timeout_ms < 0:
        raise ValueError("find util,invalid parameter.")

    if isinstance(targets, str):
        targets = (targets,)
    byte_targets = []
    for target in targets:
        byte_targets.append(
            target.encode("utf-8") if isinstance(target, str) else target
        )
    offsets = [0] * len(byte_targets)
    end_time = time.ticks_add(time.ticks_ms(), timeout_ms)
    while True:
        if stream.any():
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
        if time.ticks_diff(end_time, time.ticks_ms()) <= 0:
            return -1


def skip_next(stream, target_char: str, timeout_ms: int):
    if not target_char or timeout_ms < 0:
        raise ValueError("skip next,invalid parameter.")

    end_time = time.ticks_add(time.ticks_ms(), timeout_ms)
    while True:
        if stream.any():
            return stream.read(1).decode("utf-8") == target_char
        if time.ticks_diff(time.ticks_ms(), end_time) >= 0:
            return False


def read_until(stream, delimiter: str, timeout_ms: int):
    if not delimiter or timeout_ms < 0:
        raise ValueError("read until,invalid parameter.")
    result = ""
    end_time = time.ticks_add(time.ticks_ms(), timeout_ms)
    while True:
        if stream.any():
            current_char = stream.read(1).decode("utf-8")
            if current_char == delimiter:
                return result
            result += current_char

        if time.ticks_diff(time.ticks_ms(), end_time) >= 0:
            return None


def parse_int(stream, timeout_ms: int):
    if timeout_ms < 0:
        raise ValueError("parse int,invalid parameter.")
    num_str = ""
    end_time = time.ticks_add(time.ticks_ms(), timeout_ms)
    while True:
        if stream.any():
            current_char = stream.read(1).decode("utf-8")
            if current_char in (",", "\r", "\n"):
                break
            if current_char.isdigit() or (current_char == "-" and not num_str):
                num_str += current_char
            else:
                break
        if time.ticks_diff(time.ticks_ms(), end_time) >= 0:
            break
    return int(num_str) if num_str and num_str != "-" else -1
