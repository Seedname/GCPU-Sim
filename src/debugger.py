from simulator import CPU, clock_cpu, register_keys, register_mouse, display_screen, display_screen_2bit
from pynput import keyboard
import cv2
import numpy as np
import pathlib
import threading
import time

def clock_cpu(cpu: CPU) -> None:

    while True:
        input()
        cpu.clock()


def main(screen: int = 0, screen_scale: int = 1, sticky: bool = False, accurate_clocks: bool = False, io_address: int = None) -> None:
    path = pathlib.Path(__file__).parent.joinpath('output')
    cpu = CPU(rom=path.joinpath('rom.mif'), ram=path.joinpath('ram.mif'))
    
    if screen == 0:
        clock_cpu(cpu, debug, debug)
    else:
        clock_cpu_threaded = threading.Thread(target=clock_cpu, args=(cpu,debug,debug,accurate_clocks), daemon=True)
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

    main(debug=debug, screen=screen, screen_scale=screen_scale, sticky=sticky, accurate_clocks=accurate_clocks, io_address=io_address)
