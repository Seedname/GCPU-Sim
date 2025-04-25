mouseX:     equ     $1400
mouseY:     equ     $1401
mouseEvent: equ     $1402
; mouse event states:
; 0- mouse moved
; 1- left click
; 2- right click
; 3- middle click
; 4- left click release
; 5- right click release
; 6- middle click release
; 7- left button double click
; 8- right button double click
; 9- middle button double click
; 10- scroll wheel movement

up:         equ     $1403
left:       equ     $1404
down:       equ     $1405
right:      equ     $1406

org $1000
screen:         ds.b    128
screenPointer:  dc.b    $00,$10

tempX:          ds.b    1
tempY:          ds.b    1
origY:          ds.b    1

currX:          ds.b    1
currY:          ds.b    1

neighbors:      ds.b    1
count:          ds.b    1
tempMask:       ds.b    1

; lookup table for bitmasks
org $1100
maskTable:      dc.b    $80,$40,$20,$10,$08,$04,$02,$01
maskPointer:    dc.b    $00,$11

org $1200
buffer:         ds.b    128
bufferPointer:  dc.b    $00,$12


org 0
readMouse:
    ldaa mouseEvent
    ldab #$FF ; load b with -1
    beq16 readKeys ; it's 0, dont do anything
    sum_ba
    beq16 writePixel ; it's 1, write a pixel
    sum_ba
    beq16 removePixel ; it's 2, remove a pixel

readKeys:
    ldy #up
    ldaa 0,y
    bne16 runGameOfLife ; if up arrow pressed, start the game of life

    beq16 readMouse ; if up arrow not pressed, keep reading
    
writePixel:
    ldaa mouseY
    ; multiply mouseY by 4 to get the row
    shfa_l
    shfa_l
    
    ; divide mouseX by 8 to get the offset
    ldab mouseX
    shfb_r
    shfb_r
    shfb_r

    sum_ba ; add a and b to get the byte

    staa screenPointer ; store this to the screen pointer

    ldaa mouseX
    ldab #07
    and_ba ; this will get the last 3 bits of the mouseX (mouseX % 8)

    staa maskPointer

    ldx screenPointer
    ldy maskPointer

    ldaa 0,x
    ldab 0,y
    or_ba
    staa 0,x

    ldaa #0
    beq16 readMouse

removePixel: 
    ldaa mouseY
    ; multiply mouseY by 4 to get the row
    shfa_l
    shfa_l
    
    ; divide mouseX by 8 to get the offset
    ldab mouseX
    shfb_r
    shfb_r
    shfb_r

    sum_ba ; add a and b to get the byte

    staa screenPointer ; store this to the screen pointer

    ldaa mouseX
    ldab #07
    and_ba ; this will get the last 3 bits of the mouseX (mouseX % 8)

    staa maskPointer

    ldx screenPointer
    ldy maskPointer

    ldaa 0,x
    ldab 0,y
    comb ; get the inverse of the mask
    and_ba ; and it with the screen to remove the pxiel
    staa 0,x

    ldaa #0
    beq16 readMouse

runGameOfLife:
    ; algorithm steps:
    ; go through each pixel in the screen and treat it as its own cell
    ; count the neighbors of each cell
    ; follow these rules: (https://en.wikipedia.org/wiki/Conway's_Game_of_Life):
    ; 1.  Any live cell with fewer than two live neighbours dies, as if by underpopulation.
    ; 2.  Any live cell with two or three live neighbours lives on to the next generation.
    ; 3.  Any live cell with more than three live neighbours dies, as if by overpopulation.
    ; 4.  Any dead cell with exactly three live neighbours becomes a live cell, as if by reproduction.
    ; write the result of each cell to the buffer
    ; copy the buffer to the screen
    ; repeat

    ; store the neighbor count in neighbors
    ldaa #0
    staa currX
    staa currY

startCycle:
    ; reset the variables
    ldaa #0 
    staa neighbors
    staa count ; load count with 0

    ldaa currY

    ; subtract 1 from y

    ldab #$FF
    sum_ba
    ldab #31
    and_ba ; clip to 32 
    staa tempY ; update Y
    staa origY ; store the original y position to jump back to later

    ldaa currX

    ; subtract 1 from x

    ldab #$FF
    sum_ba
    ldab #31
    and_ba ; clip to 32
    staa tempX ; update X

    ; next, we need to go over all the neighbors and update the neighbors variable
getState:
    ldaa tempY
    ; multiply tempY by 4 to get the row
    shfa_l
    shfa_l
    
    ; divide tempX by 8 to get the offset
    ldab tempX
    shfb_r
    shfb_r
    shfb_r

    sum_ba ; add a and b to get the byte

    staa screenPointer ; store this to the screen pointer

    ldaa tempX
    ldab #07
    and_ba ; this will get the last 3 bits of the tempX (tempX % 8)

    staa maskPointer

    ldx screenPointer
    ldy maskPointer
    
    ldaa 0,y ; get the mask for the pixel
    ldab 0,x ; get the pixel from the screen
    and_ba ; extract the pixel from the screen
    ; if a == 0, the pixel is dead
    ; if a != 0, the pixel is alive

    beq16 continue ; if equal to 0, dont add 1 to neighbors

    ldaa neighbors
    ldab #1
    sum_ba
    staa neighbors ; add 1 to neighbors

continue:
    ; increment counter
    ldaa count
    ldab #1
    sum_ba
    staa count

    ; increment y and roll over if necessary
    ldaa tempY
    sum_ba
    ldab #31
    and_ba
    staa tempY ; increment y once and clip to 0-31

    ; need to check if count == 3 or count == 6
    ; if so, we need to set y to 0, then increment x
    ldaa count
    ldab #$FD ; negative 3
    sum_ba
    beq16 moveRight ; move right if count is 3
    sum_ba
    beq16 moveRight ; move right if count is 6
    sum_ba
    beq16 getNextState ; then, if count == 9, we need to exit the loop and do logic for the next state
    
    ; else, just continue to loop through
    bne16 getState

moveRight:
    ldaa origY
    staa tempY ; reset Y to the original position

    ldaa tempX
    ldab #1
    sum_ba ; add 1 to tempX
    ldab #31
    and_ba ; clip from 0-31
    staa tempX

    ldaa #0
    beq16 getState ; continue looping through

getNextState:
    ; here, we need to use the neighbors variable to determine the outcome of our cell
    ldaa currY
    ; multiply tempY by 4 to get the row
    shfa_l
    shfa_l
    
    ; divide tempX by 8 to get the offset
    ldab currX
    shfb_r
    shfb_r
    shfb_r

    sum_ba ; add a and b to get the byte

    staa screenPointer ; store this to the screen pointer
    
    ldaa currX
    ldab #07
    and_ba ; this will get the last 3 bits of the currX (currX % 8)
    staa maskPointer

    ldx screenPointer
    ldy maskPointer
    ldaa 0,x ; load a with the value at the pixel
    ldab 0,y ; load b with the mask of the pixel

    and_ba ; extract the pixel

    beq16 deadPixel ; if its 0, its dead
    bne16 alivePixel ; if its not 0, its alive

deadPixel:
    ldaa neighbors
    ldab #$FD ; negative 3
    sum_ba
    beq16 setToOne ; if neighbors == 3, set the next state to 1
    bne16 setToZero ; else, set it to 0

alivePixel:
    ldaa neighbors
    ldab #$FD ; negative 3
    sum_ba

    bn16 setToZero; if its negative, then it was 0, 1, or 2. in these cases, we want the cell to die
    beq16 setToOne; if it's 0, then it was 3. the cell should live

    ldab #$FF ; negative 1
    sum_ba ; subtract 1
    
    beq16 setToOne; if it's equal to 0, we know that it was 4. it should live in this case
    bne16 setToZero ; otherwise, set it to 0.

setToOne:
    ; copy the current pixel to the buffer pointer
    ldab screenPointer
    stab bufferPointer

    ldx bufferPointer
    ldaa 0,x ; load a with the value at the pixel
    ldab 0,y ; load b with the mask of the pixel
    or_ba ; add the pixel to the buffer

    ; store the new result at the buffer
    staa 0,x

    ldaa #0
    beq16 nextPixel

setToZero:
    ; copy the current pixel to the buffer pointer
    ldab screenPointer
    stab bufferPointer
    ldx bufferPointer

    ldaa 0,x ; load a with the value at the pixel
    ldab 0,y ; load b with the mask of the pixel
    comb ; take the complement of b
    and_ba ; remove the pixel from the screen

    ; store the new result at the buffer
    staa 0,x

    ldaa #0
    beq16 nextPixel

nextPixel:
    ; increment the current pixel
    ldaa currX
    ldab #1
    sum_ba
    ldab #31
    and_ba
    staa currX
    bne16 startCycle

moveDown:
    ldaa currY
    ldab #1
    sum_ba
    ldab #31
    and_ba
    staa currY
    bne16 startCycle

copyBuffer:
    @ load screen and buffer pointers, initialize a at 0
    ldaa #0
    staa screenPointer
    staa bufferPointer

    ldx screenPointer
    ldy bufferPointer

fillScreen:
    ldab 0,y
    stab 0,x
    inx
    iny

    ldab #2
    sum_ba

    @ if a is 0, it wrapped around when it hit 256, meaning we reached the end of the arrays (because we're adding 2)
    bne16 fillScreen
    beq16 runGameOfLife
