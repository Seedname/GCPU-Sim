# GCPU-Sim

## Installation

1. **Clone the repository:**
    ```sh
    git clone https://github.com/Seedname/GCPU-Sim.git
    cd GCPU-Sim
    ```

2. **Install dependencies:**
    ```sh
    pip install -r requirements.txt
    ```
    Required packages include:
    - `numpy`
    - `opencv-python`
    - `pynput`

## Assembling a Program

To assemble an assembly script (e.g., `program/snake.asm`):

```sh
python assembler.py
```

This will generate `rom.mif` and `ram.mif` files in the `output/` directory. The filename can be changed in the main function of the assembler. This will soon be changed to a command line tool.  

### Differences with this Assembler
- Labels must be followed by a colon, but can have any whitespace between them and the next instruction. 
- Added 4 new 16-bit branch instructions for programs >256 bytes: `beq16`, `bne16`, `bp16`, `bn16`. Programs with these instruction will not run on the official Gator CPU, but will work in this simulator.
- Either `@` or `;` symbols can be used for comments. Anything after them on the same line will be ignored.


## Simulating a Program

To run the simulator:

```sh
python simulator.py
```

### Simulator Options

The main function in `simulator.py` supports several options:

- **debug**: Print CPU and specified memory states, and step through each cycle.
- **screen**: 
  - `0` = no display
  - `1` = 1-bit 32x32 monochrome display mapped to the first 128 bytes of RAM (needed for `etch-a-sketch.asm`)
  - `2` = 2-bit 32x32 color display mapped to the first 256 bytes of RAM (needed for `snake.asm`)
- **screen_scale**: Scale the display window (default: 15).
- **sticky**: The last key pressed stays down until another key is pressed (recommended: `True` for Snake).

You can adjust these options by editing the variables at the bottom of `simulator.py` before running.

#### Note
- Keys are mapped in RAM starting at the address 0x1400 by default. The keys and the starting address can be specified in the simulator

## Snake Game

The Snake game is written in `program/snake.asm`. After assembling and running the simulator, you can play Snake:

- **Movement**: Use the arrow keys.
- **Restart after Game Over**: Press any arrow key while on the score screen.
- **Exit Program** Press "Q" to exit the game window and stop the program.
