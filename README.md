# FF6DPE

FF6DPE (short for ff6-dialogue-pointer-expansion) is a small python utility that expand to three bytes and relocate dialogue pointers as well as the dialogue script in other to allow more pointers and more dialogue space than the current FF3usME dialogue expansion.

It also generate an abcde-compatible Atlas script that can be edited and then reinserted in the ROM via command line.

## Usage

First place your FF3us ROM in the `roms` folder. Then edit `definition.json`. If you ever only used FF3usME there are only three things you should touch in this file. The rest was just to more or less to avoid too much hardcoding:

1. ff3usme_expansion: Set to `true` if you use FF3usME town dialogue expansion.
2. new_dialog_start: Where in your ROM you want dialogues moved (HiROM notation, beginning of a bank)
3. new_dialog_ptr_start: Where in your ROM you want dialogue pointers (HiROM notation)

Note: As it is, `definition.json` will move dialogues to `$F30000` and keep pointers at the same place, overflowing a bit on the old dialogues place.

Finally run FF6DPE with the command `python ff6dpe.py`. The output will be a ROM with the name `rom-name-dpe.{sfc/smc}` in the `roms` folder and the atlas-compatible dialogue dump named `dialogue-dump.txt` in the root folder (same level as `ff6dpe.py`).

If you see no error it means everything went well!

## abcde usage

abcde's Atlas functionality is what is used to insert `dialogue-dump.txt` in the new ROM. Download abcde from [RHDI](https://romhack.ing/database/content/entry/FdNw5JQBNs8FWu0CRI_v/abcde) or [RHDN](https://www.romhacking.net/utilities/1392/). 

At the root of abcde folder, create a folder (e.g. `ff6`). In that folder, place `table.tbl`, `dialogue-dump.txt` and your new ROM (`rom-name-dpe.{sfc/smc}`). In that folder run the following command:

`perl ../abcde.pl -cm abcde::Atlas rom-name-dpe.smc dialogue-dump.txt`

This will insert the text in the new ROM. You can freely edit in any (correct) way `dialogue-dump.txt` and re-run abcde.

## Notes

- FF6DPE was coded with python 3.13 installed. it requires python to run.
- abcde requires Perl 5.X to run.

## TODO

- Remove print() statements in the code.
- Add automatic ROM expansion code if expansion needed.
- Add FF6DE usage flag functionality.
- Make a chart explaining `table.tbl` special opcodes.
- Detail all `definition.json` settings in the readme.
- Write insertion code instead of using abcde.

