import romutils as rutl


class HackWriter:
    def __init__(self, rom: bytearray, offset: int):
        self.rom = rom
        self.offset = offset

    def write_bytes(self, *values: int):
        for value in values:
            rutl.set_byte(self.rom, self.offset, value)
            self.offset += 1

    def write_short(self, value: int):
        rutl.set_short(self.rom, self.offset, value)
        self.offset += 2

    def write_long(self, value: int):
        rutl.set_long(self.rom, self.offset, value)
        self.offset += 3
