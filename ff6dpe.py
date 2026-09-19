import glob
import os
from pathlib import Path

import rom_utils as rutl
import utils as utl
from dialogue_entry import DialogueEntry, load_table
from hack_writer import HackWriter

LAST_CD_INDEX = 0
DLG_PTR_START = 0
DLG_PTR_END = 0
DLG_START = 0
DLG_END = 0
NEW_DLG_PTR_START = 0
NEW_DLG_START = 0
FF3USME_EXP = False
FF3SUME_LAST_CD_OFFSET = 0
FF3SUME_LAST_CE_OFFSET = 0
FF3USME_DLG_START = 0
FF3USME_DLG_END = 0
NUM_POINTERS = 0
NEW_DLG_END = 0


def write_asm_hack(rom: bytearray):
    hw = HackWriter(rom, 0x007FBF)
    hw.write_bytes(0xC2, 0x20)
    hw.write_bytes(0xA5, 0xD0)
    hw.write_bytes(0x0A)
    hw.write_bytes(0x18)
    hw.write_bytes(0x65, 0xD0)
    hw.write_bytes(0xAA)
    hw.write_bytes(0xBF)
    hw.write_long(NEW_DLG_PTR_START)
    hw.write_bytes(0x85, 0xC9)
    hw.write_bytes(0x7B)
    hw.write_bytes(0xE2, 0x20)
    hw.write_bytes(0xBF)
    hw.write_long(NEW_DLG_PTR_START + 2)
    hw.write_bytes(0x85, 0xCB)
    hw.write_bytes(0xA9, 0x01)
    hw.write_bytes(0x8D, 0x68, 0x05)
    hw.write_bytes(0x60)


def move_vanilla_dialogs(rom: bytearray):
    global NEW_DLG_END
    dlg_start = rutl.hirom_to_abs(DLG_START)
    dlg_end = rutl.hirom_to_abs(DLG_END)
    new_dlg_start = rutl.hirom_to_abs(NEW_DLG_START)
    dlg_size = dlg_end + 1 - dlg_start
    # print(f"{dlg_size:06X}")
    if new_dlg_start > (len(rom) - dlg_size):
        raise ValueError("New dialog range exceeds ROM end!")

    data_to_move = rom[dlg_start : dlg_end + 1]
    rom[new_dlg_start : new_dlg_start + len(data_to_move)] = data_to_move
    NEW_DLG_END = new_dlg_start + len(data_to_move)


def move_ff3usme_dialogs(rom: bytearray):
    global NEW_DLG_END
    dlg_start = rutl.hirom_to_abs(DLG_START)
    dlg_end = rutl.hirom_to_abs(DLG_END)
    ff3usme_dlg_start = rutl.hirom_to_abs(FF3USME_DLG_START)
    ff3usme_dlg_end = rutl.hirom_to_abs(FF3USME_DLG_END)
    new_dlg_start = rutl.hirom_to_abs(NEW_DLG_START)
    dlg_size = dlg_end + 1 - dlg_start
    ff3usme_dlg_size = ff3usme_dlg_end + 1 - ff3usme_dlg_start
    if new_dlg_start > (len(rom) - dlg_size + ff3usme_dlg_size):
        raise ValueError("New dialog range exceeds ROM end!")

    vanilla_data_to_move = rom[dlg_start : dlg_end + 1]
    new_dlg_end = new_dlg_start + len(vanilla_data_to_move)
    rom[new_dlg_start:new_dlg_end] = vanilla_data_to_move

    ff3usme_data_to_move = rom[ff3usme_dlg_start : ff3usme_dlg_end + 1]
    new_ff3usme_dlg_start = new_dlg_start + 0x20000
    new_ff3usme_dlg_end = new_ff3usme_dlg_start + len(ff3usme_data_to_move)
    rom[new_ff3usme_dlg_start:new_ff3usme_dlg_end] = ff3usme_data_to_move
    NEW_DLG_END = new_ff3usme_dlg_end


def is_null_ptr(data: bytearray, id: int, null_value: int) -> bool:
    return data[id] == null_value and data[id + 1] == null_value


def is_null_ptr_next(data: bytearray, id: int, null_value: int) -> bool:
    return (
        data[id] == null_value
        and data[id + 1] == null_value
        and data[id + 2] == null_value
        and data[id + 3] == null_value
    )


def expand_vanilla_pointers(rom: bytearray):
    global NUM_POINTERS
    dlg_ptr_start = rutl.hirom_to_abs(DLG_PTR_START)
    dlg_ptr_end = rutl.hirom_to_abs(DLG_PTR_END)
    new_dlg_ptr_start = rutl.hirom_to_abs(NEW_DLG_PTR_START)
    new_dialog_bank = (NEW_DLG_START >> 16) & 0xFF
    last_cd_index = rutl.get_short(rom, rutl.hirom_to_abs(LAST_CD_INDEX))
    old_pointers = rom[dlg_ptr_start : dlg_ptr_end + 1]

    for ptr_id in range(0, len(old_pointers) - 2, 2):
        dlg_index = int(ptr_id / 2)
        is_null_00 = is_null_ptr_next(old_pointers, ptr_id, 0x00)
        is_null_ff = is_null_ptr_next(old_pointers, ptr_id, 0xFF)
        if (dlg_index > last_cd_index) and (is_null_00 or is_null_ff):
            NUM_POINTERS = dlg_index
            # print(f"Break (id: {dlg_index})")
            break
        new_ptr_offset = ptr_id + dlg_index + new_dlg_ptr_start
        rom[new_ptr_offset : new_ptr_offset + 2] = old_pointers[ptr_id : ptr_id + 2]
        rutl.set_byte(rom, new_ptr_offset + 2, new_dialog_bank)
        if dlg_index == last_cd_index:
            new_dialog_bank += 1

    last_ptr = len(old_pointers) - 2
    is_null_00 = is_null_ptr(old_pointers, last_ptr, 0x00)
    is_null_ff = is_null_ptr(old_pointers, last_ptr, 0xFF)
    if not is_null_00 and not is_null_ff:
        dlg_index = int(last_ptr / 2)
        NUM_POINTERS = dlg_index
        new_ptr_offset = last_ptr + dlg_index + new_dlg_ptr_start
        rom[new_ptr_offset : new_ptr_offset + 2] = old_pointers[last_ptr : last_ptr + 2]
        rutl.set_byte(rom, new_ptr_offset + 2, new_dialog_bank)


def expand_ff3usme_pointers(rom: bytearray):
    global NUM_POINTERS
    dlg_ptr_start = rutl.hirom_to_abs(DLG_PTR_START)
    dlg_ptr_end = rutl.hirom_to_abs(DLG_PTR_END)
    new_dlg_ptr_start = rutl.hirom_to_abs(NEW_DLG_PTR_START)
    new_dialog_bank = (NEW_DLG_START >> 16) & 0xFF
    last_cd_index = rutl.get_short(rom, rutl.hirom_to_abs(FF3SUME_LAST_CD_OFFSET))
    last_ce_index = rutl.get_short(rom, rutl.hirom_to_abs(FF3SUME_LAST_CE_OFFSET))
    old_pointers = rom[dlg_ptr_start : dlg_ptr_end + 1]

    for ptr_id in range(0, len(old_pointers) - 2, 2):
        dlg_index = int(ptr_id / 2)
        is_null_00 = is_null_ptr_next(old_pointers, ptr_id, 0x00)
        is_null_ff = is_null_ptr_next(old_pointers, ptr_id, 0xFF)
        if (dlg_index > last_ce_index) and (is_null_00 or is_null_ff):
            NUM_POINTERS = dlg_index
            # print(f"Break (id: {dlg_index})")
            break
        new_ptr_offset = ptr_id + dlg_index + new_dlg_ptr_start
        rom[new_ptr_offset : new_ptr_offset + 2] = old_pointers[ptr_id : ptr_id + 2]
        rutl.set_byte(rom, new_ptr_offset + 2, new_dialog_bank)
        if dlg_index == last_ce_index:
            new_dialog_bank += 1
        if dlg_index == last_cd_index:
            new_dialog_bank += 1

    last_ptr = len(old_pointers) - 2
    is_null_00 = is_null_ptr(old_pointers, last_ptr, 0x00)
    is_null_ff = is_null_ptr(old_pointers, last_ptr, 0xFF)
    if not is_null_00 and not is_null_ff:
        dlg_index = int(last_ptr / 2)
        NUM_POINTERS = dlg_index
        new_ptr_offset = last_ptr + dlg_index + new_dlg_ptr_start
        rom[new_ptr_offset : new_ptr_offset + 2] = old_pointers[last_ptr : last_ptr + 2]
        rutl.set_byte(rom, new_ptr_offset + 2, new_dialog_bank)


def dump_dialogues(rom: bytearray, dump_header: list):
    dlg_entries = []
    new_dlg_ptr_start = rutl.hirom_to_abs(NEW_DLG_PTR_START)
    new_dlg_end = rutl.hirom_to_abs(NEW_DLG_END)
    table = load_table("table.tbl")
    prev_ptr = 0
    for dlg_index in range(NUM_POINTERS):
        ptr_offset = new_dlg_ptr_start + (dlg_index * 3)
        # print(f"ptr_offset: {ptr_offset:06X}")
        ptr = rutl.hirom_to_abs(rutl.get_long(rom, ptr_offset))
        # print(f"ptr_hr: {rutl.get_long(rom, ptr_offset):06X}")
        # print(f"ptr: {ptr:06X}")
        if ptr < prev_ptr:
            raise ValueError(
                f"dump_dialogues() dialogue {dlg_index:04X} ptr ({ptr:06X}) is smaller than previous ptr ({prev_ptr:06X})"
            )
        dlg_entry = DialogueEntry(dlg_index)
        dlg_entry.decode(rom, ptr, new_dlg_end, table)
        dlg_entries.append(dlg_entry)
        # print(f"Dumping id {dlg_entry.id}")

    output = dump_header
    for dlg_entry in dlg_entries:
        output.append(f"// Caption #{dlg_entry.id}\n")
        output.append("#WRITE(PtrTable)\n")
        output.append(f"{dlg_entry.string}\n\n")

    utl.write_text_file(output, "dialogue-dump.txt")


def write_dump_header() -> list:
    new_dlg_ptr_start = rutl.hirom_to_abs(NEW_DLG_PTR_START)
    new_dlg_start = rutl.hirom_to_abs(NEW_DLG_START)
    header = []
    header.append("#VAR(dialogue, TABLE)\n")
    header.append('#ADDTBL("table.tbl", dialogue)\n')
    header.append("#ACTIVETBL(dialogue)\n")
    header.append("#VAR(Ptr, CUSTOMPOINTER)\n")
    header.append('#CREATEPTR(Ptr, "HIROM", $0, 24)\n')
    header.append("#VAR(PtrTable, POINTERTABLE)\n")
    header.append(f"#PTRTBL(PtrTable, ${new_dlg_ptr_start:06X}, 3, Ptr)\n")
    header.append("#HDR($0)\n\n")
    header.append(f"#JMP(${new_dlg_start:06X})\n\n")
    return header


def get_json_vars(json_data: dict):
    global \
        LAST_CD_INDEX, \
        DLG_PTR_START, \
        DLG_PTR_END, \
        DLG_START, \
        DLG_END, \
        NEW_DLG_PTR_START, \
        NEW_DLG_START, \
        FF3USME_EXP, \
        FF3SUME_LAST_CD_OFFSET, \
        FF3SUME_LAST_CE_OFFSET, \
        FF3USME_DLG_START, \
        FF3USME_DLG_END

    LAST_CD_INDEX = utl.get_hex_dict_entry(json_data, "last_bank_cd_dialog_index")
    DLG_PTR_START = utl.get_hex_dict_entry(json_data, "dialog_ptr_start")
    DLG_PTR_END = utl.get_hex_dict_entry(json_data, "dialog_ptr_end")
    DLG_START = utl.get_hex_dict_entry(json_data, "dialog_start")
    DLG_END = utl.get_hex_dict_entry(json_data, "dialog_end")
    NEW_DLG_PTR_START = utl.get_hex_dict_entry(json_data, "new_dialog_ptr_start")
    NEW_DLG_START = utl.get_hex_dict_entry(json_data, "new_dialog_start_bank") << 16

    FF3USME_EXP = utl.get_bool_dict_entry(json_data, "ff3usme_expansion")
    FF3SUME_LAST_CD_OFFSET = utl.get_hex_dict_entry(
        json_data, "ff3usme_last_bank_cd_dialog_index"
    )
    FF3SUME_LAST_CE_OFFSET = utl.get_hex_dict_entry(
        json_data, "ff3usme_last_bank_ce_dialog_index"
    )
    FF3USME_DLG_START = utl.get_hex_dict_entry(json_data, "ff3usme_dialog_start")
    FF3USME_DLG_END = utl.get_hex_dict_entry(json_data, "ff3usme_dialog_end")


if __name__ == "__main__":
    json_data = utl.read_json("definition.json")
    get_json_vars(json_data)

    files = glob.glob("roms/*.sfc") + glob.glob("roms/*.smc")

    if files:
        file = min(files)
        # print(file)
        rom = utl.read_bin_file(file)
        had_header = rutl.trim_header(rom)
        write_asm_hack(rom)

        if FF3USME_EXP:
            move_ff3usme_dialogs(rom)
            expand_ff3usme_pointers(rom)
        else:
            move_vanilla_dialogs(rom)
            expand_vanilla_pointers(rom)

        dump_header = write_dump_header()
        dump_dialogues(rom, dump_header)

        if had_header:
            rutl.add_header(rom)

        filename = Path(file).stem
        extension = Path(file).suffix
        new_file = os.path.join("roms", f"{filename}-dpe{extension}")
        utl.write_bin_file(rom, new_file)

    else:
        print("No ROM file provided in the 'roms' folder!")
