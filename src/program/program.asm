@ Snake
@ Author: Julian Dominguez
@ Date: 04-17-2025

org $1000
screen: ds.b    123 ; 0…122 all zeros
        dc.b    $55 ; byte 123: 01 01 01 01 (green in cols 12,13,14,15 of row 15)
        ds.b    2   ; 2 empty bytes
        dc.b    $80 ; byte 124: 00 00 00 10 (red in col 27 of row 15)
        ds.b    129 ; pad out to 256 bytes total

org $1100

@ array of snake x positions
snakeX:     dc.b    12,13,14,15
            ds.b    252

@ array of snake y positions
snakeY:     dc.b    15,15,15,15
            ds.b    252

@ pointers to the head and tail in the snake arrays
headPointer:    dc.b    3
tailPointer:    dc.b    0

@ pointer to the address of the x and y arrays
snakeXAddr:     dc.b    $00,$11
snakeYAddr:     dc.b    $00,$12

@ two global variables to store values across "functions"
tempX:  dc.b    0
tempY:  dc.b    0

@ direction of snake movement
@ dir = 0: move right
@ dir = 1: move down
@ dir = 2: move left
@ dir = 3: move up
dir:       dc.b     0

@ position of the apple
appleX:   dc.b    27
appleY:   dc.b    15

@ seed for random movement
seed:   dc.b    0

@ pointer to address of the screen array
address:    dc.b    $00,$10

@ maps for arrow keys
up:     equ     $1400
left:   equ     $1401
down:   equ     $1402
right:  equ     $1403

org $1500
@ lookup table of snake bitmasks
snakeMask:  dc.b    %01000000,%00010000,%00000100,%00000001

@ XOR to remove it on the next frame
org $1600
@ lookup table of apple bitmasks, maybe we can reuse the snake and then shift right once
appleMask:  dc.b    %10000000,%00100000,%00001000,%00000010

org $1700
@ lookup table of bitmasks to delete a pixel from the screen
eraseMask:  dc.b    %00111111,%11001111,%11110011,%11111100

org $1504
@ pointers to masks
snakeMaskAddr:  dc.b    $00,$15
appleMaskAddr:  dc.b    $00,$16
eraseMaskAddr:  dc.b    $00,$17

@ pointers to the program
programPointer: dc.b    $00,$00

@ logic:
@ 1. Spawn snake in the middle of the screen

@ 2. spawn the apple
@    only generating numbers between 0 and 31
@    only need 5/8 bits to be for the random number
@    add the seed to the current row
@    and the row by $1F
@    add the col to the seed
@    then do the inverse for the col

@ 3. move the snake 
@    note: store a buffer of the keys so that the snake cant move in the opposite direction 
@    check if head is on the apple
@    if so, spawn a new apple
@    if not, calculate the snakes next position
@    if the snake's next position is white, the snake dies. reset the screen (make each pixel white then black??). then reset the snake
@    if the snake's next position is black, use the mask to make the tail pixel black, and the new head pixel white


@ NEVERMIND:
@   use a LFSR to get a random apple position instead
@   then also add the snake tail or something to make it less deterministic


@ NOTE: Try using branching instead of repeated addition / repeated subtraction to make clocks consistent. it would be weird if some regions moved faster than others



main:
    org 0

removeTail:
    @ remove the old tail
    ldaa tailPointer
    
    @ load x and y pointers with the memory locations for the x and y positions of the snake tail
    staa snakeXAddr
    staa snakeYAddr

    ldx snakeXAddr
    ldy snakeYAddr

    @ calculate byte 
    ldaa 0,y ; load row into a

    @ multiply row by 8 
    shfa_l
    shfa_l
    shfa_l

    ldab 0,x ; load col into b

    @ divide col by 4
    shfb_r
    shfb_r

    sum_ba ; add them together to get the byte

    staa address ; update the address

    @ get the mask by doing col % 4
    ldaa 0,x
    ldab #%00000011 ; the last two bits will give the modulo 4
    and_ab ; get col % 4 and put it in b

    @ Use the lookup table to get the mask of this pixel
    stab snakeMaskAddr
    ldx snakeMaskAddr
    ldab 0,x ; load the mask into b

    ldx address ; move x pointer to the screen location

    @ to remove the pixel from the screen, we can use A & /B 
    @ where A is the current screen and B is the mask of the pixel we want to remove
    ldaa 0,x ; A
    comb ; /B
    and_ba ; A & /B
    staa 0,x ; write the pixel to the screen

    @ increment the tail pointer (tail pointer + 1) % 256
    ldaa tailPointer 
    ldab #1
    sum_ba
    staa tailPointer

readKeys:
    
    ldy #right
    ldaa 0,y
    bne16 setDir0

    ldy #down
    ldaa 0,y
    bne16 setDir1

    ldy #left
    ldaa 0,y
    bne16 setDir2

    ldy #up
    ldaa 0,y
    bne16 setDir3

    @ if no keys are pressed, dont set a new dir
    beq16 moveHeadPointer

setDir0:
    ldaa #0
    staa dir
    beq16 moveHeadPointer

setDir1:
    ldaa #1
    staa dir
    bne16 moveHeadPointer

setDir2:
    ldaa #2
    staa dir
    bne16 moveHeadPointer

setDir3:
    ldaa #3
    staa dir
    bne16 moveHeadPointer

moveHeadPointer:

    @ move pointers to head instead of tail
    ldaa headPointer

    staa snakeXAddr
    staa snakeYAddr

    ldx snakeXAddr
    ldy snakeYAddr

gameLoop:
    @ implement as cyclic snake buffer
    @ tail pos = length % 256

    @ update the seed 
    ldaa seed
    ldab #1
    sum_ba
    staa seed

    ldaa dir

    beq16 moveRight ; if dir == 0, move right

    ldab #$FF

    sum_ba
    beq16 moveDown ; if dir == 1, move down

    sum_ba
    beq16 moveLeft ; if dir == 2, move left

    sum_ba
    beq16 moveUp ; if dir == 3, move up


moveRight:
    @ calculate the new head and store them in tempX and tempY
    ldaa 0,x ; col
    ldab #1
    sum_ba ; increment col

    staa tempX ; store the next col in tempX

    @ see if the col % 32 makes it run into a wall
    ldab #31
    and_ba

    beq16 gameOver ; snake ran into the wall

    ldaa 0,y ; next row
    staa tempY ; store the next row in tempY

    ldaa #0
    beq16 updateHead ; if it didnt die, update the head

moveDown:
    @ calculate the new head and store them in tempX and tempY
    ldaa 0,y ; row
    ldab #1
    sum_ba ; increment row

    staa tempY ; store the next row in tempY

    @ see if the row % 32 makes it run into a wall
    ldab #31
    and_ba

    beq16 gameOver ; snake ran into the wall

    ldaa 0,x ; next col
    staa tempX ; store the next col in tempX

    ldaa #0
    beq16 updateHead ; if it didnt die, update the head

moveUp:
    @ calculate the new head and store them in tempX and tempY
    ldaa 0,y ; row

    @ see if the row == 0
    beq16 gameOver ; snake ran into the wall

    ldab #$FF
    sum_ba ; decrement row

    staa tempY ; store the next row in tempY

    ldaa 0,x ; next col
    staa tempX ; store the next col in tempX

    ldaa #0
    beq16 updateHead ; if it didnt die, update the head

moveLeft:
    @ calculate the new head and store them in tempX and tempY
    ldaa 0,x ; col
    
    @ see if the col == 0
    beq16 gameOver ; snake ran into the wall
    
    ldab #$FF
    sum_ba ; increment col

    staa tempX ; store the next col in tempX

    ldaa 0,y ; next row
    staa tempY ; store the next row in tempY

    ldaa #0
    beq16 updateHead ; if it didnt die, update the head


updateHead:
    @ load the head pointer
    ldaa headPointer

    ldab #1
    sum_ba ; add 1 to the head pointer to get the new head 
    staa headPointer

    @ update the snake address to the head pointer
    staa snakeXAddr
    staa snakeYAddr

    @ move the x and y pointers to the new location
    ldx snakeXAddr
    ldy snakeYAddr

    @ write the head to the new spots
    ldaa tempX ; retrieve the new column
    ldab tempY ; retrieve the new row
    
    staa 0,x ; add the new column
    stab 0,y ; add the new row

    @ divide col by 4
    shfa_r
    shfa_r

    @ multiply row by 8 
    shfb_l
    shfb_l
    shfb_l

    sum_ba ; a = row * 8 + col / 4

    staa address ; update the address

    @ get the mask by doing col % 4
    ldaa 0,x ; col
    ldab #%00000011 ; the last two bits will give the modulo 4
    and_ba ; get col % 4 and put it in a


    @ check for collisions
    
    @ Use the lookup table to get the erase mask of this pixel
    staa eraseMaskAddr ; a contains col % 4
    staa snakeMaskAddr ; a contains col % 4
        
    ldx eraseMaskAddr
    ldab 0,x ; load the mask into b
    comb ; invert the mask to extract instead of erase
    
    @ get whats on the screen
    ldx address ; move x pointer to the screen location
    ldaa 0,x
    @ use the inverted mask to extract the pixel value at the location
    and_ba

    @ if the pixel is black, the spot is empty, so no collision
    beq16 continue


    @ get whats on the screen
    @ ldx address ; move x pointer to the screen location
    @ ldaa 0,x

    @ load b with the snake mask
    ldx snakeMaskAddr
    ldab 0,x
    comb ; get the complement of b

    @ if A & /B is 0, then the pixels are the same, meaning there's a collision
    @ if A & /B is anything but 0, then we know there is an apple at that pixel because red is 10 while green is 01
    and_ba 

    beq16 gameOver
    bne16 eatApple


continue:
    @ Use the lookup table to get the mask of this pixel
    ldx snakeMaskAddr
    ldab 0,x ; load the mask into b

    ldx address ; move x pointer to the screen location

    @ update the screen with the mask
    ldaa 0,x
    or_ba
    staa 0,x ; write to screen

    ldaa #0
    beq16 removeTail

eatApple:
    @ delete the apple, and move it to a new pseudo-random position, and make the snake bigger
    ldx eraseMaskAddr
    ldy snakeMaskAddr
    ldab 0,x ; load the mask into b

    ldx address ; move x pointer to the screen location

    @ update the screen with the mask
    ldaa 0,x
    and_ba

    @ write the snake pixel over the black pixel
    ldab 0,y
    or_ba
    
    staa 0,x ; write to screen

    @ how to make the snake bigger?
    @ increment the head pointer but dont increment or remove the tail
    @ you can check if the buffer is full if head == tail

    @ next: make a new apple

    @ read random program data cuz why not
    ldaa seed
    staa programPointer
    ldx programPointer
    
    @ get random program data
    ldaa 0,x
    
    coma
    shfa_l
    shfa_l

    ldab 1,x

    or_ba

    staa address ; use that for screen byte

    ldaa 2,x
    ldab #3 ; get a number from 0 to 3 to get the pixel
    and_ab

    stab appleMaskAddr
    ldx appleMaskAddr
    ldab 0,x ; get the pixel value for the apple

    ldx address
    ldaa 0,x ; get whats at the screen for the chosen address

    or_ba ; add the apple to the screen

    ldx address
    staa 0,x

    ldaa #0
    beq16 readKeys

gameOver:
    ldaa #0
    staa address

fillScreen:
    ldx address

    ldab #$FF
    stab 0,x
    
    ldaa address
    ldab #1
    sum_ba
    staa address

    ldaa #0
    beq16 fillScreen

exit:
    ldaa #0
    beq16 exit

