import re
import cv2
import numpy as np
import keyboard

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

    def get_memory(self) -> int:
        return self.memory[self.pc % 0x2000]
    
    def clock(self):
        instruction = self.get_memory()

        if instruction in self.instructions:
            self.instructions[instruction](self)
        else:
            print(f"Unknown instruction: {instruction}")
            exit(1)

class Instruction:
    def tab(cpu: CPU):
        cpu.b = cpu.a
        cpu.pc += 1

    def tba(cpu: CPU):
        cpu.a = cpu.b
        cpu.pc += 1

    def ldaai(cpu: CPU):
        cpu.pc += 1
        cpu.a = cpu.get_memory()
        cpu.pc += 1
    
    def ldabi(cpu: CPU):
        cpu.pc += 1
        cpu.b = cpu.get_memory()
        cpu.pc += 1

    def ldaa(cpu: CPU):
        cpu.pc += 1
        
        lower = cpu.get_memory()
        cpu.pc += 1

        upper = cpu.get_memory()

        address = (upper << 8) | lower
        cpu.a = cpu.memory[address]

        cpu.pc += 1
    
    def ldab(cpu: CPU):
        cpu.pc += 1
        
        lower = cpu.get_memory()
        cpu.pc += 1

        upper = cpu.get_memory()

        address = (upper << 8) | lower
        cpu.b = cpu.memory[address]

        cpu.pc += 1
    
    def staa(cpu: CPU):
        cpu.pc += 1
        
        lower = cpu.get_memory()
        cpu.pc += 1

        upper = cpu.get_memory()

        address = (upper << 8) | lower
        cpu.memory[address] = cpu.a

        cpu.pc += 1
    
    def stab(cpu: CPU):
        cpu.pc += 1
        
        lower = cpu.get_memory()
        cpu.pc += 1

        upper = cpu.get_memory()

        address = (upper << 8) | lower
        cpu.memory[address] = cpu.b

        cpu.pc += 1

    def ldxi(cpu: CPU):
        cpu.pc += 1
        
        lower = cpu.get_memory()
        cpu.pc += 1

        upper = cpu.get_memory()

        value = (upper << 8) | lower
        cpu.x = value

        cpu.pc += 1
    
    def ldyi(cpu: CPU):
        cpu.pc += 1
        
        lower = cpu.get_memory()
        cpu.pc += 1

        upper = cpu.get_memory()

        value = (upper << 8) | lower
        cpu.y = value

        cpu.pc += 1
    
    def ldx(cpu: CPU):
        cpu.pc += 1
        
        lower = cpu.get_memory()
        cpu.pc += 1

        upper = cpu.get_memory()

        address = (upper << 8) | lower
        cpu.x = cpu.memory[address]

        cpu.pc += 1
    
    def ldy(cpu: CPU):
        cpu.pc += 1
        
        lower = cpu.get_memory()
        cpu.pc += 1

        upper = cpu.get_memory()

        address = (upper << 8) | lower
        cpu.y = cpu.memory[address]

        cpu.pc += 1

    def ldaax(cpu: CPU):
        cpu.pc += 1
        displacement = cpu.get_memory()
        cpu.a = cpu.memory[cpu.x + displacement]
        cpu.pc += 1
    
    def ldaay(cpu: CPU):
        cpu.pc += 1
        displacement = cpu.get_memory()
        cpu.a = cpu.memory[cpu.y + displacement]
        cpu.pc += 1

    def ldabx(cpu: CPU):
        cpu.pc += 1
        displacement = cpu.get_memory()
        cpu.b = cpu.memory[cpu.x + displacement]
        cpu.pc += 1
    
    def ldaby(cpu: CPU):
        cpu.pc += 1
        displacement = cpu.get_memory()
        cpu.y = cpu.memory[cpu.y + displacement]
        cpu.pc += 1

    def staax(cpu: CPU):
        cpu.pc += 1
        displacement = cpu.get_memory()
        cpu.memory[cpu.x + displacement] = cpu.a
        cpu.pc += 1
    
    def staay(cpu: CPU):
        cpu.pc += 1
        displacement = cpu.get_memory()
        cpu.memory[cpu.y + displacement] = cpu.a
        cpu.pc += 1
    
    def stabx(cpu: CPU):
        cpu.pc += 1
        displacement = cpu.get_memory()
        cpu.memory[cpu.x + displacement] = cpu.b
        cpu.pc += 1
    
    def staby(cpu: CPU):
        cpu.pc += 1
        displacement = cpu.get_memory()
        cpu.memory[cpu.y + displacement] = cpu.b
        cpu.pc += 1

    def sum_ba(cpu: CPU):
        cpu.a = (cpu.a + cpu.b) & 0xFF
        cpu.pc += 1

    def sum_ab(cpu: CPU):
        cpu.b = (cpu.a + cpu.b) & 0xFF
        cpu.pc += 1

    def and_ba(cpu: CPU):
        cpu.a = cpu.a & cpu.b
        cpu.pc += 1
    
    def and_ab(cpu: CPU):
        cpu.b = cpu.a & cpu.b
        cpu.pc += 1

    def or_ba(cpu: CPU):
        cpu.a = cpu.a | cpu.b
        cpu.pc += 1
    
    def or_ab(cpu: CPU):
        cpu.b = cpu.a | cpu.b
        cpu.pc += 1

    def coma(cpu: CPU):
        cpu.a = ~cpu.a
        cpu.pc += 1
    
    def comb(cpu: CPU):
        cpu.b = ~cpu.b
        cpu.pc += 1

    def shfa_l(cpu: CPU):
        cpu.a = (cpu.a << 1) & 0xFF
        cpu.pc += 1
    
    def shfa_r(cpu: CPU):
        cpu.a >>= 1
        cpu.pc += 1
    
    def shfb_l(cpu: CPU):
        cpu.b = (cpu.b << 1) & 0xFF
        cpu.pc += 1

    def shfb_r(cpu: CPU):
        cpu.b >>= 1
        cpu.pc += 1
    
    def inx(cpu: CPU):
        cpu.x = (cpu.x + 1) & 0xFFFF
        cpu.pc += 1

    def iny(cpu: CPU):
        cpu.y = (cpu.y + 1) & 0xFFFF
        cpu.pc += 1

    def beq(cpu: CPU):
        cpu.pc += 1
        address = cpu.get_memory()

        if cpu.a == 0:
            cpu.pc = address
        else:
            cpu.pc += 1

    def bne(cpu: CPU):
        cpu.pc += 1
        address = cpu.get_memory()

        if cpu.a != 0:
            cpu.pc = address
        else:
            cpu.pc += 1

    def bn(cpu: CPU):
        cpu.pc += 1
        address = cpu.get_memory()

        # check if MSB of A is 1
        if cpu.a & 0x80:
            cpu.pc = address
        else:
            cpu.pc += 1
        
    def bp(cpu: CPU):
        cpu.pc += 1
        address = cpu.get_memory()

        # check if MSB of A is 0
        if cpu.a & 0x80 == 0:
            cpu.pc = address
        else:
            cpu.pc += 1

def display_info(cpu: CPU) -> None:
    print("Expr\tValue\tMemory")
    print(f"PC:\t${cpu.pc:04X}\t${cpu.memory[cpu.pc]:02X}\nA:\t${cpu.a:02X}\nB:\t${cpu.b:02X}\nX:\t${cpu.x:04X}\t${cpu.memory[cpu.x]:02X}\nY:\t${cpu.y:04X}\t${cpu.memory[cpu.y]:02X}")

def display_screen(cpu: CPU) -> bool:
    for i in range(128):
        byte = cpu.memory[0x1000 + i]
        for j in range(8):
            bit = (byte >> (7 - j)) & 1
            buffer[i % 32, i // 32] = (0,0,0) if bit == 0 else (255, 255, 255)

    cv2.imshow("pixels", buffer)

    key = chr(cv2.waitKey(1) & 0xFF)

    if key == 'q':
        return True
    print(cpu.memory[0x1409], cpu.memory[0x140A], bin(cpu.memory[0x140B])[2:].zfill(8), cpu.x, cpu.a)
    return False
    
def register_keys(cpu: CPU) -> None:
    for i, key in enumerate(keys):
        if keyboard.is_pressed(key):
            cpu.memory[0x1400 + i] = 1
        else:
            cpu.memory[0x1400 + i] = 0

def main() -> None:
    cpu = CPU()

    while True:
        stop = display_screen(cpu)

        if stop:
            break
        
        register_keys(cpu)

        cpu.clock()

    cv2.destroyAllWindows()

if __name__ == "__main__":
    buffer = np.zeros((32, 32, 3), dtype=np.uint8)
    keys = ['up','left','down','right','w','a','s','d','space']

    cv2.namedWindow("pixels", cv2.WINDOW_AUTOSIZE)

    main()