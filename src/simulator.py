import re
import cv2
import numpy as np
from pynput import keyboard
import pathlib
import threading
import time
import platform

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
                    ranged_memory = re.match(r"^\[([0-9A-Fa-f]+)\.\.([0-9A-Fa-f]+)\]\s*:\s*([0-9A-Fa-f]+);$", line)

                    if ranged_memory:
                        start, end, value = ranged_memory.groups()
                        start = int(start, 16)
                        end = int(end, 16)
                        value = int(value, 16)

                        for address in range(start, end + 1):
                            self.memory[address + offset] = value

                        continue
                    
                    # single memory
                    single_memory = re.match(r"^([0-9A-Fa-f]+)\s*:\s*([0-9A-Fa-f]+);$", line)
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
    while True:
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
            return True



def display_screen_2bit(cpu: CPU, start: int = 0x1000, screen_scale: int = 1) -> bool:
    display_map = [(0, 0, 0), (0, 255, 0), (0, 0, 255), (255, 255, 255)]
    while True:
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
            return True

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

    listener = keyboard.Listener(on_press=on_press,
                                 on_release=on_release)
    listener.daemon = True
    listener.start()

    return listener



def clock_cpu(cpu: CPU, debug: bool = False, step: bool = False, accurate_clocks: bool = False) -> None:
    # Disable on Windows 
    if platform.system() == "Windows":
        accurate_clocks = False


    start = time.perf_counter_ns()
    clock_speed = 1_100

    if accurate_clocks:
        frame_time = 10**9 / clock_speed
    else:
        frame_time = 1 / clock_speed

    while True:

        if debug:
            display_info(cpu, memory_locations={
                # specify memory locations & names to debug here 
            })
        
        cpu.clock()

        if not step:
            if accurate_clocks:
                while time.perf_counter_ns() < start:
                    pass
                start += frame_time
            else:
                time.sleep(frame_time)
        else:
            input()



def main(debug: bool = False, screen: int = 0, screen_scale = 1, sticky: bool = False, accurate_clocks: bool = False) -> None:
    path = pathlib.Path(__file__).parent.joinpath('output')
    cpu = CPU(rom=path.joinpath('rom.mif'), ram=path.joinpath('ram.mif'))
    
    if screen == 0:
        clock_cpu(cpu, debug, debug)
    else:
        clock_cpu_threaded = threading.Thread(target=clock_cpu, args=(cpu,debug,debug,accurate_clocks), daemon=True)
        register_keys(cpu, start=0x1400, sticky=sticky)
        
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
    screen = 2
    sticky = True
    accurate_clocks = True

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

    main(debug=debug, screen=screen, screen_scale=screen_scale, sticky=sticky, accurate_clocks=accurate_clocks)
