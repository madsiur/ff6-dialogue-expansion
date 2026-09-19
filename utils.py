import json


def get_bool_dict_entry(data: dict, key: str) -> bool:
    if key not in data:
        raise KeyError(f"Missing key: {key}")
    if type(data[key]) is not bool:
        raise TypeError(
            f"get_bool_dict_entry() expected bool, got {type(data[key]).__name__}"
        )
    return data[key]


def get_hex_dict_entry(data: dict, key: str) -> int:
    if not data[key]:
        raise KeyError(f"Missing key: {key}")
    return hex_string_to_int(data[key])


def hex_string_to_int(value: str) -> int:
    if not isinstance(value, str):
        if isinstance(value, int):
            return value
        else:
            raise TypeError(
                f"hex_string_to_int() expected str or int, got {type(value).__name__}"
            )
    if not value.startswith(("0x", "0X")):
        raise ValueError(f"Invalid hex string: {value}")
    try:
        return int(value, 16)
    except ValueError as e:
        raise ValueError(f"Invalid hex string: {value}") from e


def read_bin_file(filename: str) -> bytearray:
    try:
        with open(filename, "rb") as f:
            return bytearray(f.read())
    except OSError as e:
        raise OSError(f"An OSError occurred while reading {filename}: {e}") from e


def read_json(filename: str) -> dict:
    try:
        with open(filename, "r", encoding="utf-8") as f:
            json_content = json.load(f)
            return json_content
    except OSError as e:
        raise OSError(f"An OSError occurred while reading {filename}: {e}") from e


def write_bin_file(data: bytearray, filename: str):
    try:
        with open(filename, "wb") as f:
            f.write(data)
    except OSError as e:
        raise OSError(f"An OSError occurred while writing {filename}: {e}") from e


def write_text_file(text: list, filename: str):
    try:
        with open(filename, "w") as f:
            f.write("".join(text))
    except OSError as e:
        raise OSError(f"An OSError occurred while writing {filename}: {e}") from e
