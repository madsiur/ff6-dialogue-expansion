# FF6DPE

FF6DPE (short for ff6-dialogue-pointer-expansion) is a small python utility that expand to three bytes and relocate dialogue pointers as well as the dialogue script in other to allow more pointers and more dialogue space what the current FF3usME dialogue expansion allows.

It also generate an abcde-compatible script that can be edited and then reinserted in the ROM via command line.

## Usage

First place your FF3us 1.0 or FF3us 1.1 ROM in the `roms` folder. Then edit `definition.json` if needed. If you ever only used FF3usME for dialogues there are only three settings you should touch in this file. The rest of the setting entries are there more or less to avoid too much hardcoding:

1. `ff3usme_expansion`: Set to `True` if you currently use FF3usME town dialogue expansion.
2. `new_dialog_start`: Bank where you want dialogues to start. (HiROM notation)
3. `new_dialog_ptr_start`: ROM offset where you want dialogue pointers to start. (HiROM notation)

Note: By default, `definition.json` will move dialogues to `$F30000` and keep pointers more or less at the same place, overflowing a bit on the old dialogues place.

Finally run FF6DPE with the command `python ff6dpe.py`. This command will take the first ROM in the `roms` folder and output a ROM with the name `rom-name-dpe.{sfc/smc}` in the `output` folder and the atlas-compatible dialogue dump named `rom-name-dump.txt` in the `output` folder as well.

Note that if you place your dialogues or dialogue pointers in expanded space and your ROM is not expanded, you will be ask if you want FF6DPE to expand the ROM to 4MiB.

## abcde usage

abcde's Atlas module is what is used to insert `rom-name-dump.txt` in the new ROM. Download abcde from [RHDI](https://romhack.ing/database/content/entry/FdNw5JQBNs8FWu0CRI_v/abcde) or [RHDN](https://www.romhacking.net/utilities/1392/).

At the root of abcde folder, create a folder (e.g. `ff6`). In that folder, place `table.tbl`, `rom-name-dump.txt` and your new ROM (`rom-name-dpe.{sfc/smc}`). In that folder run the following command:

`perl ../abcde.pl -cm abcde::Atlas rom-name-dpe.smc dialogue-dump.txt`

This will insert the text in the new ROM. You can freely edit in any (correct) way `rom-name-dump.txt` and re-run abcde.

## DTE optimization

Once the base expansion is done, you can run `python ff6dpe.py -dte` to optimize the DTE table. This command will take the first ROM in the `roms` folder and generate a new ROM named `rom-name-dte.{sfc/smc}` and a new table named `rom-name-table.tbl`, both placed in the `output` folder.

Note that for now, in order to complete this process, you must re-run abcde with your script, the new ROM and the new table. You script must have the correct table name at `#ADDTBL("table.tbl", dialogue)` so you can just rename the new table `table.tbl`.

DTE optimization on the vanilla script saves about 0x130 bytes of dialogues.

## Assembly hack

This is the assembly hack that FF6DPE does in order to use expanded pointers:
```
C0/7FBF: C2 20    	    REP #$20       (16 bit accum./memory)
C0/7FC1: A5 D0    	    LDA $D0        (Get dialog index)
C0/7FC3: 0A      	    ASL A          (Times 2)
C0/7FC4: 18             CLC            (Clear carry flag)
C0/7FC5: 65 D0          ADC $D0        (Times 3 since pointers are 3 bytes)
C0/7FC7: AA      	    TAX            (This gives us the index X)
C0/7FC8: BF 00 E6 CC	LDA $CCE600,X  (Loads pointer to dialogue X low bytes)
C0/7FCC: 85 C9    	    STA $C9        (The pointer low bytes goes in $C9)
C0/7FCE: 7B      	    TDC            (Clear accumulator)
C0/7FCF: E2 20          SEP #$20       (8 bit accum./memory)
C0/7FD1: BF 02 E6 CC	LDA $CCE602,X  (Loads pointer to dialogue X bank byte)
C0/7FD5: 85 CB    	    STA $CB        (The pointer bank byte goes in $CB)
C0/7FD7: A9 01    	    LDA #$01       (Put a 1 in the accumulator)
C0/7FD9: 8D 68 05  	    STA $0568      (Store 1 into $0568)
C0/7FDC: 60      	    RTS
```

## Notes

- FF6DPE was coded with python 3.13 installed. it requires python to run.
- abcde requires Perl 5.X to run.

## TODO

- Validate all `definition.json` offsets.
- Add FF6DE usage flag functionality.
- Make a chart explaining `table.tbl` special opcodes.
- Detail all `definition.json` settings in the readme.
- Write insertion code instead of using abcde.

