#!/usr/bin/env python
# -*- coding: utf-8 -*-

import re
import pathlib
# TODO: make this a cli tool, clean up the code, add debugger by adding another file that maps rom to labels & line numbers

asm_map = {
    # Data Movement Instructions
    r"^tab$": [0x00],
    r"^tba$": [0x01],
    r"^ldaa\s+#((?:\$|%)?[a-z0-9_]+)$": [0x02, "mm"],
    r"^ldab\s+#((?:\$|%)?[a-z0-9_]+)$": [0x03, "mm"],
    r"^ldaa\s+((?:\$|%)?[a-z0-9_]+)$": [0x04, "ll", "hh"],
    r"^ldab\s+((?:\$|%)?[a-z0-9_]+)$": [0x05, "ll", "hh"],
    r"^staa\s+((?:\$|%)?[a-z0-9_]+)$": [0x06, "ll", "hh"],
    r"^stab\s+((?:\$|%)?[a-z0-9_]+)$": [0x07, "ll", "hh"],
    r"^ldx\s+#((?:\$|%)?[a-z0-9_]+)$": [0x08, "ii", "jj"],
    r"^ldy\s+#((?:\$|%)?[a-z0-9_]+)$": [0x09, "ii", "jj"],
    r"^ldx\s+((?:\$|%)?[a-z0-9_]+)$": [0x0A, "ll", "hh"],
    r"^ldy\s+((?:\$|%)?[a-z0-9_]+)$": [0x0B, "ll", "hh"],

    # regular data movement instructions
    r"^ldaa\s+((?:\$|%)?[a-z0-9_]+),x$": [0x0C, "dd"],
    r"^ldaa\s+((?:\$|%)?[a-z0-9_]+),y$": [0x0D, "dd"],
    r"^ldab\s+((?:\$|%)?[a-z0-9_]+),x$": [0x0E, "dd"],
    r"^ldab\s+((?:\$|%)?[a-z0-9_]+),y$": [0x0F, "dd"],
    r"^staa\s+((?:\$|%)?[a-z0-9_]+),x$": [0x10, "dd"],
    r"^staa\s+((?:\$|%)?[a-z0-9_]+),y$": [0x11, "dd"],
    r"^stab\s+((?:\$|%)?[a-z0-9_]+),x$": [0x12, "dd"],
    r"^stab\s+((?:\$|%)?[a-z0-9_]+),y$": [0x13, "dd"],

    # ALU Related Instructions
    r"^sum_ba$": [0x14],
    r"^sum_ab$": [0x15],
    r"^and_ba$": [0x16],
    r"^and_ab$": [0x17],
    r"^or_ba$": [0x18],
    r"^or_ab$": [0x19],
    r"^coma$": [0x1A],
    r"^comb$": [0x1B],
    r"^shfa_l$": [0x1C],
    r"^shfa_r$": [0x1D],
    r"^shfb_l$": [0x1E],
    r"^shfb_r$": [0x1F],
    r"^inx$": [0x30],
    r"^iny$": [0x31],
    # Branch Instructions
    r"^beq\s+((?:\$|%)?[a-zA-Z0-9_]+)$": [0x20, "bb"],
    r"^bne\s+((?:\$|%)?[a-zA-Z0-9_]+)$": [0x21, "bb"],
    r"^bn\s+((?:\$|%)?[a-zA-Z0-9_]+)$": [0x22, "bb"],
    r"^bp\s+((?:\$|%)?[a-zA-Z0-9_]+)$": [0x23, "bb"],
    # 16-bit branch instructions... 8 bits doesnt cut it
    r"^beq16\s+((?:\$|%)?[a-zA-Z0-9_]+)$": [0x24, "ll", "hh"],
    r"^bne16\s+((?:\$|%)?[a-zA-Z0-9_]+)$": [0x25, "ll", "hh"],
    r"^bn16\s+((?:\$|%)?[a-zA-Z0-9_]+)$": [0x26, "ll", "hh"],
    r"^bp16\s+((?:\$|%)?[a-zA-Z0-9_]+)$": [0x27, "ll", "hh"],
}

# Assembler directives:
# org <address> - Set the origin for the program
# <label>: equ <value> - Define a macro
# dc.b <value> - Define a constant byte
# ds.b <size> - Define a block of memory
asm_directives = [
    r"^(org)\s+((?:\$|%)?[a-f0-9]+)$",
    r"^(equ)\s+((?:\$|%)?[a-f0-9]+)$",
    r"^(db)\s+((?:\$|%)?[a-f0-9]+)$",
    r"^(dc.b)\s+([\$%a-f0-9,\s]+)$",
    r"^(ds.b)\s+((?:\$|%)?[a-f0-9]+)$",
]

def read_asm(filename: str) -> list[str]:
    with open(filename, 'r') as f:
        lines = f.readlines()
    
    # remove spaces from beginning and end, as well as newlines
    lines = [line.strip() for line in lines]

    # remove comments
    lines = [re.sub(r';.*|@.*', '', line).strip() for line in lines]
    
    # remove empty lines
    lines = [line for line in lines if line.strip()]

    # merge labels with instructions
    for i, line in enumerate(lines):
        if line.endswith(':'):
            # If the line ends with a colon, it's a label
            lines[i+1] = line + ' ' + lines[i+1]
            # make label empty to remove it
            lines[i] = ""

    # remove empty lines and make everything lowercase
    lines = [line.lower().strip() for line in lines if line.strip()]

    return lines

def parse_number(num: str) -> int:
    if num.startswith("$"):
        return int(num[1:], 16)
    elif num.startswith("%"):
        return int(num[1:], 2)
    
    return int(num)

def hexify(value: int, digits: int = 4) -> str:
    return hex(value)[2:].zfill(digits).upper()[-digits:]
    
def process_asm(lines: list[str]) -> None:
    memory = {}

    instruction_format = r"^(?:([a-zA-Z0-9_]+):)?\s*(.*)\s*$"
    
    macros = {}

    already_checked = {}

    running_address = 0x0000
    
    # first pass: assembler directives
    for line_num, line in enumerate(lines):
        label, instruction = re.match(instruction_format, line).groups()
        
        for format in asm_directives:
            matches = re.match(format, instruction)
            if matches:
                already_checked[line_num] = True
                pnemonic, argument = matches.groups()
                
                match pnemonic:
                    case "org":
                        running_address = parse_number(argument)
                        if label is not None:
                            macros[label] = running_address
                        break
                    case "equ":
                        macros[label] = argument
                        break
                    case "dc.b":
                        if label is not None:
                            macros[label] = str(running_address)
                        
                        arguments = argument.split(",")
                        arguments = [arg.strip() for arg in arguments]

                        for i in range(len(arguments)):
                            num = arguments[i]
                            if (running_address + i) in memory:
                                raise ValueError(f"Address ${running_address + i:04X} already defined in memory")
                            
                            memory[running_address + i] = parse_number(num)

                        running_address += len(arguments)
                        break
                    case "ds.b":
                        if label is not None:
                            macros[label] = str(running_address)
                        size = parse_number(argument)

                        for i in range(size):
                            if (running_address + i) in memory:
                                raise ValueError(f"Address ${running_address + i:04X} already defined in memory")
                            memory[running_address + i] = 0
                      
                        running_address += size
                        break
                    case _:
                        continue

                break

    prev_running_address = running_address

    # second pass: labels to addresses
    for line_num, line in enumerate(lines):
        label, instruction = re.match(instruction_format, line).groups()
        
        for format in asm_map:
            match = re.match(format, instruction)
            if match:
                opcode = asm_map[format]

                if label is not None:
                    macros[label] = str(running_address)

                running_address += len(opcode)
                break

    running_address = prev_running_address

    # third pass: assemble
    for line_num, line in enumerate(lines):
        label, instruction = re.match(instruction_format, line).groups()

        for format in asm_map:
            match = re.match(format, instruction)
            if match:
                opcode = asm_map[format]
                operands = list(match.groups())

                for i, operand in enumerate(operands):
                    if operand in macros:
                        operands[i] = macros[operand]

                    operands[i] = parse_number(operands[i])

                memory[running_address] = opcode[0]

                if len(opcode) == 2:
                    memory[running_address + 1] = operands[0]
                if len(opcode) == 3:
                    operand_bytes = int.to_bytes(operands[0], byteorder='little', length=2)
                    memory[running_address + 1] = operand_bytes[0]
                    memory[running_address + 2] = operand_bytes[1]

                running_address += len(opcode)
                break
        else:
            if not already_checked.get(line_num, False):
                raise ValueError(f"Unknown instruction: {instruction}")

    
    header = """DEPTH = 4096;
WIDTH = 8;
ADDRESS_RADIX = HEX;
DATA_RADIX = HEX;
CONTENT 
BEGIN

"""

    rom = ""
    ram = ""

    last_location = 0
    
    for location in sorted(memory.keys()):
        if location <= 0x0FFF:
            hex_value = hexify(location)
        else:
            hex_value = hexify(location - 0x1000)

        data = hexify(memory[location], 2)

        if location - last_location > 0:

            if last_location <= 0x0FFF and location > 0x0FFF:
                rom += f"[{hexify(last_location)}..0FFF] : 00;\n"
                if location != 0x1000:
                    ram += f"[0000..{hexify(location - 0x1001)}] : 00;\n"
            elif last_location <= 0x0FFF:
                rom += f"[{hexify(last_location)}..{hexify(location-1)}] : 00;\n"
            else:
                ram += f"[{hexify(last_location - 0x1000)}..{hexify(location - 0x1001)}] : 00;\n"

        if location <= 0x0FFF:
            rom += f"{hex_value} : {data};\n"
        else:   
            ram += f"{hex_value} : {data};\n"

        last_location = location + 1
    else:
        location = 0x1FFF
        if location - last_location > 0:
            if last_location <= 0x0FFF:
                rom += f"[{hexify(last_location)}..0FFF] : 00;\n"
                ram += f"[0000..0FFF] : 00;\n"
            else:
                ram += f"[{hexify(last_location - 0x1000)}..0FFF] : 00;\n"
                

    path = pathlib.Path(__file__).parent.joinpath('output')
    path.mkdir(parents=True, exist_ok=True)
    
    with open(path.joinpath('rom.mif'), 'w') as f:
        f.write(header)
        f.write(rom)
        f.write("\nEND;\n")

    with open(path.joinpath('ram.mif'), 'w') as f:
        f.write(header)
        f.write(ram)
        f.write("\nEND;\n")


def main() -> None:
    path = pathlib.Path(__file__).parent
    filename = path.joinpath("program", "snake.asm")
    lines = read_asm(filename)
    process_asm(lines)


if __name__ == "__main__":
    main()