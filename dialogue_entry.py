class DialogueEntry:
    def __init__(self, id: int):
        self.id = id
        self.string = ""
        self.data = []

    def decode(self, rom: bytearray, ptr: int, dlg_end: int, table: dict):
        output = []
        data = []
        i = ptr
        while i < dlg_end:
            if rom[i] == 0x00:
                entry = table.get(rom[i])
                if entry:
                    label, extra = entry
                    output.append(label)
                    data.append(rom[i])
                break
            entry = table.get(rom[i])
            if entry:
                label, extra = entry
                i += 1
                if extra > 0:
                    if label.startswith("<") and label.endswith(">"):
                        label = label[1:-1]
                    extra_bytes = rom[i : i + extra]
                    i += extra
                    extra_hex = " ".join(f"<${b:02X}>" for b in extra_bytes)
                    output.append(f"{label}{extra_hex}")
                    data.append(rom[i])
                    data.append(extra_bytes)
                else:
                    output.append(label)
                    data.append(rom[i])
                if rom[i - 1] == 0x01 or rom[i - 1] == 0x13:
                    output.append("\n")
            else:
                output.append(f"<${rom[i]:02X}>")
                data.append(rom[i])
                i += 1

        self.string = "".join(output)
        self.data = data


def load_table(filepath: str) -> dict:
    table = {}
    with open(filepath) as f:
        for line in f:
            line = line.rstrip("\r\n")
            if not line or "=" not in line:
                continue
            hex_part, rest = line.split("=", 1)
            hex_part = hex_part.removeprefix("!")
            key = int(hex_part.lstrip("$"), 16)

            if "," in rest:
                label, extra_str = rest.rsplit(",", 1)
                extra_str = extra_str.strip()
                try:
                    extra_bytes = int(extra_str)
                except ValueError:
                    label = rest
                    extra_bytes = 0
            else:
                label = rest
                extra_bytes = 0

            table[key] = (label, extra_bytes)
            # print(f"key: {key}")
    return table
