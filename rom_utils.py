def get_short(data: bytearray, offset: int) -> int:
    validate_long(offset)
    short = data[offset + 1] * 0x100
    short = short + data[offset]
    return short


def get_long(data: bytearray, offset: int) -> int:
    long = data[offset + 2] * 0x10000
    long = long + data[offset + 1] * 0x100
    long = long + data[offset]
    return long


def set_byte(data: bytearray, offset: int, value: int):
    validate_long(offset)
    validate_byte(value)
    data[offset] = value & 0xFF


def set_short(data: bytearray, offset: int, value: int):
    validate_long(offset)
    validate_short(value)
    data[offset] = value & 0xFF
    data[offset + 1] = (value >> 8) & 0xFF


def set_long(data: bytearray, offset: int, value: int):
    validate_long(offset)
    validate_long(value)
    data[offset] = value & 0xFF
    data[offset + 1] = (value >> 8) & 0xFF
    data[offset + 2] = (value >> 16) & 0xFF


def trim_header(data: bytearray) -> bool:
    if len(data) % 0x80000 == 0x200:
        del data[:0x200]
        return True
    return False


def add_header(data: bytearray):
    data[:0] = bytearray(0x200)


def hirom_to_abs(value: int) -> int:
    if value > 0xC00000:
        return value - 0xC00000
    return value


def validate_byte(value: int):
    if value < 0 or value > 0xFF:
        raise ValueError(f"Byte value {value} is smaller than 0x00 or bigger than 0xFF")


def validate_short(value: int):
    if value < 0 or value > 0xFFFF:
        raise ValueError(
            f"Short value {value} is smaller than 0x0000 or bigger than 0xFFFF"
        )


def validate_long(value: int):
    if value < 0 or value > 0xFFFFFF:
        raise ValueError(
            f"Long value {value} is smaller than 0x000000 or bigger 0xFFFFFF)."
        )
