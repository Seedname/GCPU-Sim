import re
import cv2
import numpy as np
from pynput import keyboard
import pathlib
import threading
import time
import platform
import json
from collections import OrderedDict
import math

# TODO: add comments & docstrings, make into CLI tool, add debug options 

class CPU:
    def __init__(self, rom: str = "rom.mif", ram: str = "ram.mif"):
        self.a = 0
        self.b = 0

        self.x = 0
        self.y = 0

        self.pc = 0
        
        self.memory = [0] * 0x2000 # 4Kib ROM, 4Kib RAM

        self.load_memory(rom, ram)

        self.instructions = {
            0x00: Instruction.tab,
            0x01: Instruction.tba,
            0x02: Instruction.ldaai,
            0x03: Instruction.ldabi,
            0x04: Instruction.ldaa,
            0x05: Instruction.ldab,
            0x06: Instruction.staa,
            0x07: Instruction.stab,
            0x08: Instruction.ldxi,
            0x09: Instruction.ldyi,
            0x0A: Instruction.ldx,
            0x0B: Instruction.ldy,
            0x0C: Instruction.ldaax,
            0x0D: Instruction.ldaay,
            0x0E: Instruction.ldabx,
            0x0F: Instruction.ldaby,
            0x10: Instruction.staax,
            0x11: Instruction.staay,
            0x12: Instruction.stabx,
            0x13: Instruction.staby,
            0x14: Instruction.sum_ba,
            0x15: Instruction.sum_ab,
            0x16: Instruction.and_ba,
            0x17: Instruction.and_ab,
            0x18: Instruction.or_ba,
            0x19: Instruction.or_ab,
            0x1A: Instruction.coma,
            0x1B: Instruction.comb,
            0x1C: Instruction.shfa_l,
            0x1D: Instruction.shfa_r,
            0x1E: Instruction.shfb_l,
            0x1F: Instruction.shfb_r,
            0x30: Instruction.inx,
            0x31: Instruction.iny,
            0x20: Instruction.beq,
            0x21: Instruction.bne,
            0x22: Instruction.bn,
            0x23: Instruction.bp,

            # extra instructions that I added (not part of G-CPU)
            0x24: Instruction.beq16,
            0x25: Instruction.bne16,
            0x26: Instruction.bn16,
            0x27: Instruction.bp16,
        }

    def load_memory_file(self, filename: str, offset: int):
        with open(filename, 'r') as f:
            start_loading = False
            for line in f.readlines():
                line = line.strip()
                
                if line == "BEGIN":
                    start_loading = True
                
                if line == "END":
                    start_loading = False
                    break
                
                if start_loading and line:
                    # ranged memory
                    ranged_memory = re.match(r"^\[([0-9A-Fa-f]+)\.\.([0-9A-Fa-f]+)\]\s*\t*:\s*\t*([0-9A-Fa-f]+);.*$", line)

                    if ranged_memory:
                        start, end, value = ranged_memory.groups()
                        start = int(start, 16)
                        end = int(end, 16)
                        value = int(value, 16)

                        for address in range(start, end + 1):
                            self.memory[address + offset] = value

                        continue
                    
                    # single memory
                    single_memory = re.match(r"^([0-9A-Fa-f]+)\s*\t*:\s*\t*([0-9A-Fa-f]+);.*$", line)
                    if single_memory:
                        address, value = single_memory.groups()
                        address = int(address, 16)
                        value = int(value, 16)

                        self.memory[address + offset] = value


    def load_memory(self, rom: str, ram: str):
        self.load_memory_file(rom, 0x0000)
        self.load_memory_file(ram, 0x1000)

    def get_memory(self, address: int = None) -> int:
        if address is None:
            if self.pc >= 0x2000:
                raise ValueError("Program counter is out of bounds")
            
            return self.memory[self.pc]
        
        if address >= 0x2000:
            raise ValueError("Memory address is out of bounds")
        
        return self.memory[address]
    
    def write_memory(self, address: int, value: int) -> None:
        if address < 0x1000:
            raise ValueError("Cannot write to ROM")
        
        self.memory[address] = value
        
    def inc_pc(self) -> None:
        self.pc += 1
        self.pc &= 0xFFFF # trim to 16 bits
    
    def clock(self):
        instruction = self.get_memory()

        if instruction in self.instructions:
            self.instructions[instruction](self)
        else:
            raise ValueError(f"Unknown instruction: ${instruction:02X}")


class Instruction:
    def tab(cpu: CPU):
        cpu.b = cpu.a
        cpu.inc_pc()

    def tba(cpu: CPU):
        cpu.a = cpu.b
        cpu.inc_pc()

    def ldaai(cpu: CPU):
        cpu.inc_pc()
        cpu.a = cpu.get_memory()
        cpu.inc_pc()
    
    def ldabi(cpu: CPU):
        cpu.inc_pc()
        cpu.b = cpu.get_memory()
        cpu.inc_pc()

    def ldaa(cpu: CPU):
        cpu.inc_pc()
        
        lower = cpu.get_memory()
        cpu.inc_pc()

        upper = cpu.get_memory()

        address = (upper << 8) | lower
        cpu.a = cpu.get_memory(address=address)

        cpu.inc_pc()
    
    def ldab(cpu: CPU):
        cpu.inc_pc()
        
        lower = cpu.get_memory()
        cpu.inc_pc()

        upper = cpu.get_memory()

        address = (upper << 8) | lower
        cpu.b = cpu.get_memory(address=address)

        cpu.inc_pc()
    
    def staa(cpu: CPU):
        cpu.inc_pc()
        
        lower = cpu.get_memory()
        cpu.inc_pc()

        upper = cpu.get_memory()

        address = (upper << 8) | lower
        cpu.write_memory(address=address, value=cpu.a)

        cpu.inc_pc()
    
    def stab(cpu: CPU):
        cpu.inc_pc()
        
        lower = cpu.get_memory()
        cpu.inc_pc()

        upper = cpu.get_memory()

        address = (upper << 8) | lower

        cpu.write_memory(address=address, value=cpu.b)

        cpu.inc_pc()

    def ldxi(cpu: CPU):
        cpu.inc_pc()
        
        lower = cpu.get_memory()
        cpu.inc_pc()

        upper = cpu.get_memory()

        value = (upper << 8) | lower
        cpu.x = value

        cpu.inc_pc()
    
    def ldyi(cpu: CPU):
        cpu.inc_pc()
        
        lower = cpu.get_memory()
        cpu.inc_pc()

        upper = cpu.get_memory()

        value = (upper << 8) | lower
        cpu.y = value

        cpu.inc_pc()
    
    def ldx(cpu: CPU):
        cpu.inc_pc()
        
        lower = cpu.get_memory()
        cpu.inc_pc()

        upper = cpu.get_memory()

        address = (upper << 8) | lower

        lower = cpu.get_memory(address)
        upper = cpu.get_memory(address + 1) << 8
        cpu.x = lower | upper

        cpu.inc_pc()
    
    def ldy(cpu: CPU):
        cpu.inc_pc()
        
        lower = cpu.get_memory()
        cpu.inc_pc()

        upper = cpu.get_memory()

        address = (upper << 8) | lower

        lower = cpu.get_memory(address)
        upper = cpu.get_memory(address + 1) << 8
        cpu.y = lower | upper

        cpu.inc_pc()

    def ldaax(cpu: CPU):
        cpu.inc_pc()
        displacement = cpu.get_memory()
        address = (cpu.x + displacement) & 0xFFFF # trim to 16 bits
        cpu.a = cpu.get_memory(address)
        cpu.inc_pc()
    
    def ldaay(cpu: CPU):
        cpu.inc_pc()
        displacement = cpu.get_memory()
        address = (cpu.y + displacement) & 0xFFFF # trim to 16 bits
        cpu.a = cpu.get_memory(address)
        cpu.inc_pc()

    def ldabx(cpu: CPU):
        cpu.inc_pc()
        displacement = cpu.get_memory()
        address = (cpu.x + displacement) & 0xFFFF # trim to 16 bits
        cpu.b = cpu.get_memory(address)
        cpu.inc_pc()
    
    def ldaby(cpu: CPU):
        cpu.inc_pc()
        displacement = cpu.get_memory()
        address = (cpu.y + displacement) & 0xFFFF # trim to 16 bits
        cpu.b = cpu.get_memory(address)
        cpu.inc_pc()

    def staax(cpu: CPU):
        cpu.inc_pc()
        displacement = cpu.get_memory()
        address = (cpu.x + displacement) & 0xFFFF # trim to 16 bits
        cpu.write_memory(address, cpu.a)
        cpu.inc_pc()
    
    def staay(cpu: CPU):
        cpu.inc_pc()
        displacement = cpu.get_memory()
        address = (cpu.y + displacement) & 0xFFFF # trim to 16 bits
        cpu.write_memory(address, cpu.a)
        cpu.inc_pc()
    
    def stabx(cpu: CPU):
        cpu.inc_pc()
        displacement = cpu.get_memory()
        address = (cpu.x + displacement) & 0xFFFF # trim to 16 bits
        cpu.write_memory(address, cpu.b)
        cpu.inc_pc()
    
    def staby(cpu: CPU):
        cpu.inc_pc()
        displacement = cpu.get_memory()
        address = (cpu.y + displacement) & 0xFFFF # trim to 16 bits
        cpu.write_memory(address, cpu.b)
        cpu.inc_pc()

    def sum_ba(cpu: CPU):
        cpu.a = (cpu.a + cpu.b) & 0xFF
        cpu.inc_pc()

    def sum_ab(cpu: CPU):
        cpu.b = (cpu.a + cpu.b) & 0xFF
        cpu.inc_pc()

    def and_ba(cpu: CPU):
        cpu.a = cpu.a & cpu.b
        cpu.inc_pc()
    
    def and_ab(cpu: CPU):
        cpu.b = cpu.a & cpu.b
        cpu.inc_pc()

    def or_ba(cpu: CPU):
        cpu.a = cpu.a | cpu.b
        cpu.inc_pc()
    
    def or_ab(cpu: CPU):
        cpu.b = cpu.a | cpu.b
        cpu.inc_pc()

    def coma(cpu: CPU):
        cpu.a = ~cpu.a & 0xFF
        cpu.inc_pc()
    
    def comb(cpu: CPU):
        cpu.b = ~cpu.b & 0xFF
        cpu.inc_pc()

    def shfa_l(cpu: CPU):
        cpu.a = (cpu.a << 1) & 0xFF
        cpu.inc_pc()
    
    def shfa_r(cpu: CPU):
        cpu.a >>= 1
        cpu.inc_pc()
    
    def shfb_l(cpu: CPU):
        cpu.b = (cpu.b << 1) & 0xFF
        cpu.inc_pc()

    def shfb_r(cpu: CPU):
        cpu.b >>= 1
        cpu.inc_pc()
    
    def inx(cpu: CPU):
        cpu.x = (cpu.x + 1) & 0xFFFF
        cpu.inc_pc()

    def iny(cpu: CPU):
        cpu.y = (cpu.y + 1) & 0xFFFF
        cpu.inc_pc()

    def beq(cpu: CPU):
        cpu.inc_pc()
        address = cpu.get_memory()

        if cpu.a == 0:
            # chop off the last byte of the program counter
            cpu.pc >>= 8
            cpu.pc <<= 8
            # replace it with the address
            cpu.pc |= address
        else:
            cpu.inc_pc()

    def bne(cpu: CPU):
        cpu.inc_pc()
        address = cpu.get_memory()

        if cpu.a != 0:
            # chop off the last byte of the program counter
            cpu.pc >>= 8
            cpu.pc <<= 8
            # replace it with the address
            cpu.pc |= address
        else:
            cpu.inc_pc()

    def bn(cpu: CPU):
        cpu.inc_pc()
        address = cpu.get_memory()

        # check if MSB of A is 1
        if cpu.a & 0x80:
            # chop off the last byte of the program counter
            cpu.pc >>= 8
            cpu.pc <<= 8
            # replace it with the address
            cpu.pc |= address
        else:
            cpu.inc_pc()
        
    def bp(cpu: CPU):
        cpu.inc_pc()
        address = cpu.get_memory()

        # check if MSB of A is 0
        if cpu.a & 0x80 == 0:
            # chop off the last byte of the program counter
            cpu.pc >>= 8
            cpu.pc <<= 8
            # replace it with the address
            cpu.pc |= address
        else:
            cpu.inc_pc()

    def beq16(cpu: CPU):
        cpu.inc_pc()
        low_byte = cpu.get_memory()
        cpu.inc_pc()
        high_byte = cpu.get_memory()
        
        if cpu.a == 0:
            address = (high_byte << 8) | low_byte
            cpu.pc = address
        else:
            cpu.inc_pc()

    def bne16(cpu: CPU):
        cpu.inc_pc()
        low_byte = cpu.get_memory()
        cpu.inc_pc()
        high_byte = cpu.get_memory()

        if cpu.a != 0:
            address = (high_byte << 8) | low_byte
            cpu.pc = address
        else:
            cpu.inc_pc()

    def bn16(cpu: CPU):
        cpu.inc_pc()
        low_byte = cpu.get_memory()
        cpu.inc_pc()
        high_byte = cpu.get_memory()

        # check if MSB of A is 1
        if cpu.a & 0x80:
            address = (high_byte << 8) | low_byte
            cpu.pc = address
        else:
            cpu.inc_pc()
        
    def bp16(cpu: CPU):
        cpu.inc_pc()
        low_byte = cpu.get_memory()
        cpu.inc_pc()
        high_byte = cpu.get_memory()

        # check if MSB of A is 0
        if cpu.a & 0x80 == 0:
            address = (high_byte << 8) | low_byte
            cpu.pc = address
        else:
            cpu.inc_pc()

run_program = True


def display_info(cpu: CPU, memory_locations: dict[str, int] = None) -> None:
    print("Expr\tValue\tMemory")

    if memory_locations is None:
        locations = []
    else:
        locations = [f"{location}:\t${memory_locations[location]:04X}\t${cpu.memory[memory_locations[location]]:02X}" for location in memory_locations]
    
    print(f"PC:\t${cpu.pc:04X}\t${cpu.memory[cpu.pc]:02X}",
          f"A:\t${cpu.a:02X}\nB:\t${cpu.b:02X}",
          f"X:\t${cpu.x:04X}\t${cpu.memory[cpu.x]:02X}",
          f"Y:\t${cpu.y:04X}\t${cpu.memory[cpu.y]:02X}",
          f"{'\n'.join(locations)}\n",
          sep="\n")

def display_screen(cpu: CPU, start: int = 0x1000, screen_scale: int = 1) -> bool:
    global run_program
    while run_program:
        for i in range(128):
            byte = cpu.memory[start + i]
            for j in range(8):
                val = i * 8 + j
                bit = (byte >> (7 - j)) & 1
                buffer[val // 32, val % 32] = (0,0,0) if bit == 0 else (255, 255, 255)
        
        big = cv2.resize(
            buffer,
            (buffer.shape[1] * screen_scale, buffer.shape[0] * screen_scale),
            interpolation=cv2.INTER_NEAREST
        )

        cv2.imshow("screen", big)

        key = chr(cv2.waitKey(1) & 0xFF)

        if key == 'q':
            run_program = False
            return True
        
        if cv2.getWindowProperty('screen', cv2.WND_PROP_VISIBLE) < 1:
            # window was closed manually
            run_program = False
            break

def display_screen_2bit(cpu: CPU, start: int = 0x1000, screen_scale: int = 1) -> bool:
    global run_program

    display_map = [(0, 0, 0), (0, 255, 0), (0, 0, 255), (255, 255, 255)]
    while run_program:
        for i in range(256):
            byte = cpu.memory[start + i]
            for j in range(0, 8, 2):
                val = i * 4 + j // 2
                high_bit = ((byte >> (7 - j)) & 1) << 1
                low_bit =  (byte >> (7 - (j + 1))) & 1

                buffer[val // 32, val % 32] = display_map[high_bit | low_bit]
        
        big = cv2.resize(
            buffer,
            (buffer.shape[1] * screen_scale, buffer.shape[0] * screen_scale),
            interpolation=cv2.INTER_NEAREST
        )

        cv2.imshow("screen", big)

        key = chr(cv2.waitKey(1) & 0xFF)

        if key == 'q':
            run_program = False
            return True
        
        if cv2.getWindowProperty('screen', cv2.WND_PROP_VISIBLE) < 1:
            # window was closed manually
            run_program = False
            break

def register_mouse(cpu: CPU, screen_scale: int, start: int = 0x1405):
    x_pos = start
    y_pos = start + 1
    event_pos = start + 2

    def on_mouse(event, x, y, flags, param):
        cpu.write_memory(x_pos, x // screen_scale)
        cpu.write_memory(y_pos, y // screen_scale)
        cpu.write_memory(event_pos, event)

    cv2.setMouseCallback("screen", on_mouse)

def register_keys(cpu: CPU, start: int = 0x1400, sticky: bool = False) -> threading.Thread:
    # TODO: fix memory leak with threads


    def on_press(key):
        nonlocal sticky

        if key not in keys: return

        idx = keys[key]

        if not sticky:
            cpu.memory[start + idx] = 1
        else:
            for i in range(len(keys)):
                cpu.memory[start + i] = 0
            cpu.memory[start + idx] = 1

        
    def on_release(key):
        if key not in keys: return

        idx = keys[key]

        if not sticky:
            cpu.memory[start + idx] = 0

    keyboard.Listener(on_press=on_press, on_release=on_release).start()

def load_symbols(symbol_file: str | pathlib.Path) -> dict[str, int]:
    with open(symbol_file, 'r') as f:
        result = json.load(f)
        lines = {int(key): value for key, value in result["lines"].items()}
        return result["symbols"], lines
    return {}, {}

def clock_cpu(cpu: CPU, accurate_clocks: bool = False, clock_speed: int = 1100) -> None:
    # Disable on Windows 
    if platform.system() == "Windows":
        accurate_clocks = False


    start = time.perf_counter_ns()
    clock_speed = clock_speed

    if accurate_clocks:
        frame_time = 10**9 / clock_speed
    else:
        frame_time = 1 / clock_speed

    skip_checks = False

    if clock_speed == math.inf:
        skip_checks = True

    while run_program:
        
        cpu.clock()

        if skip_checks: continue

        if accurate_clocks:
            while time.perf_counter_ns() < start:
                pass
            start += frame_time
        else:
            time.sleep(frame_time)

def parse_input(user_input: str):
    patterns = [
        r"^(?:s|step)$", # step to the next line of the program
        r"^(?:s|step)\s+([0-9]+)$", # step next n lines of the program
        r"^(?:r|run)$", # run from beginning until a breakpoint
        r"^(?:c|continue)$", # continue until the next breakpoint

        r"^(?:t|tap)\s+(\%[0-1]+|[0-9]+|\$[a-f0-9])$", # "tap" a spot in memory (prints it after each step / break)
        r"^(?:t|tap)\s+([a-z0-9_]+)$", # "tap" a spot in memory thats mapped to a label

        r"^(?:b|break|breakpoint)\s+(\%[0-1]+|[0-9]+|\$[a-f0-9]+)$", # breakpoint line number
        r"^(?:b|break|breakpoint)\s+([a-z0-9_]+)$",  # breakpoint to label

        r"^(?:i|info)\s+(?:b|breaks|breakpoints)$", # show the breakpoints and their ids
        r"^(?:i|info)\s+(?:r|regs|registers)$", # show CPU registers
        r"^(?:i|info)\s+(?:t|taps)$", # show taps

        r"^(?:d|delete)\s+(?:b|break)\s+([0-9]+)", # delete a breakpoint based on its id
        r"^(?:d|delete)\s+(?:t|tap)\s+([0-9]+)", # delete a tap based on its id

        r"^(?:l|ls|list)(?:\s+(?:l|labels))?$", # List the labels in the program
        r"^(?:p|print)\s+(?:l|line)$", # Print the current line of the program

        r"^save(?:\s+([a-z0-9_\-\.]+))?$", # Save the breakpoints & tags to a file (default = debug.json)
        r"^load(?:\s+([a-z0-9_\-\.]+))?$", # load the breakpoints & tags from a file

        r"^(?:q|quit|exit)$", # exit debugger
    ]

    for i, pattern in enumerate(patterns):
        matches = re.match(pattern, user_input)
        if matches:
            return (i, *matches.groups())
    
    return None


def print_taps(cpu: CPU, taps):
    if len(taps) == 0:
        return
    
    print("Id\tName\tLocs\tMemory")
    for i, (name, loc) in enumerate(taps):
        if name is None: name = ""
        print(f"{i}\t{name}\t${loc:04X}\t${cpu.memory[loc]:02X}")

def parse_number(num: str) -> int:
    if num.startswith("$"):
        return int(num[1:], 16)
    elif num.startswith("%"):
        return int(num[1:], 2)
    
    return int(num)

def process_input(cpu: CPU, taps: list[tuple[str, int]], breaks: OrderedDict[int, str], symbols: dict[str, int], lines: dict[int, tuple[int, str]], args):
    match args[0]:
        case 0: # step to the next line of the program
            cpu.clock()
            print_taps(cpu, taps)

        case 1: # step next n lines of the program
            times = int(args[1])
            for _ in range(times):
                cpu.clock()
            print_taps(cpu, taps)

        case 2: # run from beginning until a breakpoint
            action = True
            if cpu.pc != 0:
                action = input("This action will restart the program. Are you sure? (y/N): ").lower().strip() == "y"
                cpu.pc = 0

            while action:
                cpu.clock()
                if cpu.pc in breaks:
                    print(f"Stopped at line {cpu.pc:04X}. Breakpoint: {breaks[cpu.pc]}")
                    break

            if action:
                print_taps(cpu, taps)

        case 3: # continue until the next breakpoint
            while True:
                cpu.clock()
                if cpu.pc in breaks:
                    print(f"Stopped at line {cpu.pc:04X}. Breakpoint: {breaks[cpu.pc]}")
                    break

            print_taps(cpu, taps)

        case 4: # "tap" a spot in memory (prints it after each step / break)
            line = parse_number(args[1])
            taps.append((None, line))

        case 5: # "tap" a spot in memory thats mapped to a label
            name = args[1]
            if name in symbols:
                taps.append((name, symbols[name]))
            else:
                print(f"No label with the name {name} found.")

        case 6: # breakpoint line number
            break_line = parse_number(args[1])
            for rom_line in lines:
                if rom_line not in lines:
                    continue
                physical_line = lines[rom_line][0]
                if physical_line == break_line:
                    breaks[rom_line] = f"${break_line:04X}"
                    break

        case 7: # breakpoint to label
            name = args[1]
            if name in symbols:
                line = symbols[name]
                breaks[line] = name
            else:
                print(f"No label with the name {name} found.")

        case 8: # show the breakpoints and their ids
            if len(breaks) != 0:
                print("Id\tName\tLocation")
            for i, location in enumerate(breaks):
                print(f"{i}\t{breaks[location]}\t${location:04X}")

        case 9: # show CPU registers
            print("Expr\tValue\tMemory")
            print(f"PC:\t${cpu.pc:04X}\t${cpu.memory[cpu.pc]:02X}",
                f"A:\t${cpu.a:02X}\nB:\t${cpu.b:02X}",
                f"X:\t${cpu.x:04X}\t${cpu.memory[cpu.x]:02X}",
                f"Y:\t${cpu.y:04X}\t${cpu.memory[cpu.y]:02X}",
                sep="\n")
            
        case 10: # show taps
            print_taps(cpu, taps)

        case 11: # delete a breakpoint based on its id
            break_id = int(args[1])
            if break_id < 0 or break_id >= len(breaks):
                print("Not a valid breakpoint id.")
            else:
                for i, location in enumerate(breaks):
                    if i == break_id:
                        del breaks[location]
                        break

        case 12: # delete a tap based on its id
            tap_id = int(args[1])
            if tap_id < 0 or tap_id >= len(taps):
                print("Not a valid tap id.")
            else:
                taps.pop(tap_id)

        case 13: # List the labels in the program
            print("Labels:", ", ".join(symbols.keys()))

        case 14: # Print the current line of the program 
            print(f"Line {lines[cpu.pc][0]}: {lines[cpu.pc][1]}")

        case 15: # Save the breakpoints & taps to a file (default = debug.json)
            name = args[1]
            if args[1] is None:
                name = "debug.json"
            file = pathlib.Path(__file__).parent / name

            with open(file, 'w') as f:
                json.dump({"breaks": breaks, "taps": taps}, f)

        case 16: # load the breakpoints & taps from a file (default = debug.json)
            name = args[1]
            if args[1] is None:
                name = "debug.json"
            file = pathlib.Path(__file__).parent / name
            if not file.exists():
                print(f"File {file.name} not found.")
            else:
                with open(file, 'r') as f:
                    result = json.load(f)

                breaks.clear()
                for break_num in result["breaks"]:
                    breakpoint: str = result["breaks"][break_num]
                    if breakpoint.isnumeric() or breakpoint.startswith("$") or breakpoint.startswith("%"): continue
                    if breakpoint in symbols:
                        breaks[symbols[breakpoint]] = breakpoint
                taps.clear()
                taps.extend(result["taps"])
        case 17:
            # exit program
            return True
    
    return False



def clock_cpu_debug(cpu: CPU) -> None:
    global run_program
    taps = []
    breaks = OrderedDict()
    path = pathlib.Path(__file__).parent.joinpath('output')
    symbols, lines = load_symbols(path / "symbols.dbg")

    while run_program:
        user_input = input("(dbg) ")
        parsed = parse_input(user_input.lower().strip())
        if parsed is None:
            print("Command not recognized.")
            continue
        
        if process_input(cpu, taps, breaks, symbols, lines, parsed):
            run_program = False
            break

def main(debug: bool = False, screen: int = 0, screen_scale: int = 1, sticky: bool = False, accurate_clocks: bool = False, clock_speed: int = 1100, io_address: int = None) -> None:
    path = pathlib.Path(__file__).parent.joinpath('output')
    cpu = CPU(rom=path.joinpath('rom.mif'), ram=path.joinpath('ram.mif'))
    
    if screen == 0:
        if debug:
            clock_cpu_debug(cpu)
        else:
            clock_cpu(cpu, accurate_clocks, clock_speed)
    else:
        if debug:
            clock_cpu_threaded = threading.Thread(target=clock_cpu_debug, args=(cpu,), daemon=True)
        else:
            clock_cpu_threaded = threading.Thread(target=clock_cpu, args=(cpu, accurate_clocks, clock_speed), daemon=True)
        
        if io_address is not None:
            register_keys(cpu, start=io_address+3, sticky=sticky)
            register_mouse(cpu, start=io_address, screen_scale=screen_scale)
        
        clock_cpu_threaded.start()
        
        if screen == 1:
            display_screen(cpu,screen_scale=screen_scale)
        elif screen == 2:
            display_screen_2bit(cpu, screen_scale=screen_scale)
    
        cv2.destroyAllWindows()


if __name__ == "__main__":
    buffer = np.zeros((32, 32, 3), dtype=np.uint8)

    keys = {keyboard.Key.up: 0, 
            keyboard.Key.left: 1, 
            keyboard.Key.down: 2, 
            keyboard.Key.right: 3}

    screen_scale = 15

    debug = False
    screen = 1
    sticky = True
    accurate_clocks = True
    clock_speed = math.inf

    io_address = 0x1400

    if screen != 0:
        cv2.namedWindow(
            'screen',
            cv2.WINDOW_NORMAL    |
            cv2.WINDOW_GUI_NORMAL
        )
        cv2.setWindowProperty(
            'screen',
            cv2.WND_PROP_ASPECT_RATIO,
            cv2.WINDOW_KEEPRATIO
        )

        cv2.resizeWindow('screen', 32 * screen_scale, 32 * screen_scale)

    main(debug=debug, screen=screen, screen_scale=screen_scale, sticky=sticky, accurate_clocks=accurate_clocks, clock_speed=clock_speed, io_address=io_address)
