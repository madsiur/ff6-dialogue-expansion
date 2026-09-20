import glob
import os
import sys
from pathlib import Path

import rom_utils as rutl
import utils as utl
from dialogue_entry import DialogueEntry, build_dte, load_table, save_table
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
DTE_TABLE = 0
APPROX_DLG_SIZE = 0


def is_dte_optimization():
    i = 1
    while i < len(sys.argv):
        arg = sys.argv[i]
        i += 1
        if arg == "-dte":
            return True
        else:
            if not os.path.exists(arg):
                print(f"Error: '{arg}' not found")
                sys.exit(1)
    return False


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


def get_num_pointers(rom: bytearray) -> int:
    num_pointers = 0
    dlg_size_limit = 0x500
    new_dlg_ptr_start = rutl.hirom_to_abs(NEW_DLG_PTR_START)
    dlg_ptr_1 = rutl.get_long(rom, new_dlg_ptr_start)
    new_dlg_ptr_start += 3
    dlg_ptr_2 = rutl.get_long(rom, new_dlg_ptr_start)
    while dlg_ptr_2 >= dlg_ptr_1 and dlg_ptr_1 + dlg_size_limit > dlg_ptr_2:
        num_pointers += 1
        dlg_ptr_1 = rutl.get_long(rom, new_dlg_ptr_start)
        new_dlg_ptr_start += 3
        dlg_ptr_2 = rutl.get_long(rom, new_dlg_ptr_start)
    return num_pointers


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
            break
        new_ptr_offset = ptr_id + dlg_index + new_dlg_ptr_start
        rom[new_ptr_offset : new_ptr_offset + 2] = old_pointers[ptr_id : ptr_id + 2]
        rutl.set_byte(rom, new_ptr_offset + 2, new_dialog_bank)
        if dlg_index == last_cd_index - 1:
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
            break
        new_ptr_offset = ptr_id + dlg_index + new_dlg_ptr_start
        rom[new_ptr_offset : new_ptr_offset + 2] = old_pointers[ptr_id : ptr_id + 2]
        rutl.set_byte(rom, new_ptr_offset + 2, new_dialog_bank)
        if dlg_index == last_ce_index - 1:
            new_dialog_bank += 1
        if dlg_index == last_cd_index - 1:
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


def dump_dialogues(rom: bytearray, table: dict[int, tuple[str, int]]) -> list:
    global NUM_POINTERS, NEW_DLG_END

    if NUM_POINTERS == 0:
        NUM_POINTERS = get_num_pointers(rom)

    if NEW_DLG_END == 0:
        NEW_DLG_END = NEW_DLG_PTR_START + 0x300000

    dlg_entries = []
    new_dlg_ptr_start = rutl.hirom_to_abs(NEW_DLG_PTR_START)
    new_dlg_end = rutl.hirom_to_abs(NEW_DLG_END)
    prev_ptr = 0

    for dlg_index in range(NUM_POINTERS):
        ptr_offset = new_dlg_ptr_start + (dlg_index * 3)
        ptr = rutl.hirom_to_abs(rutl.get_long(rom, ptr_offset))
        if ptr < prev_ptr:
            raise ValueError(
                f"dump_dialogues() dialogue {dlg_index:04X} ptr ({ptr:06X}) is smaller than previous ptr ({prev_ptr:06X})"
            )
        dlg_entry = DialogueEntry(dlg_index)
        dlg_entry.decode(rom, ptr, new_dlg_end, table)
        dlg_entries.append(dlg_entry)

    return dlg_entries


def build_text_dump(dlg_entries: list[DialogueEntry], dump_header: list):
    output = dump_header
    for dlg_entry in dlg_entries:
        output.append(f"// Caption #{dlg_entry.id}\n")
        output.append("#WRITE(PtrTable)\n")
        output.append(f"{dlg_entry.string}\n\n")

    return output


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


def print_confirmation(rom_name: str, dump_name: str):
    new_dlg_ptr_end = NEW_DLG_PTR_START + (NUM_POINTERS * 3) - 1
    print(
        f"Dialogues pointers are now from ${NEW_DLG_PTR_START:06X} to ${new_dlg_ptr_end:06X}"
    )
    print(f"Dialogues are not at ${NEW_DLG_START:06X}")
    print(f"Wrote {dump_name}")
    print(f"Wrote {rom_name}")


def expand_rom(rom: bytearray):
    new_dlg_start = rutl.hirom_to_abs(NEW_DLG_START)
    if len(rom) < new_dlg_start + APPROX_DLG_SIZE:
        if utl.confirm("Inssuficent ROM space! Expand ROM to 4MiB?"):
            rutl.expand_rom(rom)
            return True
        return False
    return True


def optimize_table(
    table: dict[int, tuple[str, int]], dte: dict[int, tuple[int, int]]
) -> dict[int, tuple[str, int]]:
    for dte_id, dte_value in dte.items():
        val_0 = table[dte_value[0]][0]
        val_1 = table[dte_value[1]][0]
        table[dte_id] = (val_0 + val_1, 0)
    return table


def write_dte_to_rom(rom: bytearray, dte: dict[int, tuple[int, int]]):
    dte_offset = rutl.hirom_to_abs(DTE_TABLE)
    for dte_id, bigram in dte.items():
        offset = dte_offset + (dte_id - 0x80) * 2
        rom[offset] = bigram[0]
        rom[offset + 1] = bigram[1]


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
        FF3USME_DLG_END, \
        APPROX_DLG_SIZE, \
        DTE_TABLE

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
    DTE_TABLE = utl.get_hex_dict_entry(json_data, "dte_table")

    APPROX_DLG_SIZE = 0x30000 if FF3USME_EXP else 0x20000


if __name__ == "__main__":
    roms_dir = "roms"
    output_dir = "output"
    json_data = utl.read_json("definition.json")
    get_json_vars(json_data)

    files = glob.glob(f"{roms_dir}/*.sfc") + glob.glob(f"{roms_dir}/*.smc")

    if files:
        file = min(files)
        filename = Path(file).stem
        extension = Path(file).suffix
        rom = utl.read_bin_file(file)
        had_header = rutl.trim_header(rom)

        dte_optimization = is_dte_optimization()

        if dte_optimization:
            table = load_table("table.tbl")
            dlg_entries = dump_dialogues(rom, table)
            dte = build_dte(dlg_entries)
            new_table = optimize_table(table, dte)
            table_file = os.path.join(output_dir, f"{filename}-table.tbl")
            save_table(new_table, table_file)
            write_dte_to_rom(rom, dte)
            rom_file = os.path.join(output_dir, f"{filename}-dte{extension}")
            utl.write_bin_file(rom, rom_file)
            print(f"Wrote {table_file}")
            print(f"Wrote {rom_file}")
        else:
            if expand_rom(rom):
                write_asm_hack(rom)

                if FF3USME_EXP:
                    move_ff3usme_dialogs(rom)
                    expand_ff3usme_pointers(rom)
                else:
                    move_vanilla_dialogs(rom)
                    expand_vanilla_pointers(rom)

                os.makedirs(output_dir, exist_ok=True)

                dump_header = write_dump_header()
                table = load_table("table.tbl")
                dlg_entries = dump_dialogues(rom, table)
                dump = build_text_dump(dlg_entries, dump_header)
                dump_file = os.path.join(output_dir, f"{filename}-dump.txt")
                utl.write_text_file(dump, dump_file)
                rom_file = os.path.join(output_dir, f"{filename}-dpe{extension}")
                utl.write_bin_file(rom, rom_file)
                print_confirmation(rom_file, dump_file)
            else:
                print("Program stopped")

    else:
        print(f"No ROM file provided in the '{roms_dir}' folder!")
