@ Snake
@ Author: Julian Dominguez
@ Date: 04-17-2025

@ program flow:
@ 1. remove the tail by looking at the tail pointer and removing the green pixel at that address
@
@ 2. read the keys and set a new direction if necessary
@
@ 3. update the random seed to make the PRNG a little less noticable
@
@ 4. jump to different move procedures depending on the dir variable, 
@    these all calculate the new head, put it in tempX & tempY,and check for wall collisions
@
@ 5. increment the head pointer, check if it equals the tail. if they are, the snake's length is 256, which is the entire snake buffer. exit the game
@
@ 6. decode the row and column of the new head & get the pixel at the location. invert the erase mask and and it with the pixel to extract the pixel 
@    then, check for collisions by matching the extracted pixel with the snake mask & apple masks
@    if it's black, write the head pixel to the next position & start at step 1
@    if it's green or white, game over. 
@    if it's red, eat the apple.
@
@ 7. Eating the apple: 
@    replace the red pixel with a green pixel
@    use the lookup table to generate 2 random numbers for the byte to write the new apple to (0-255), and the column (0-3)
@    write the apple to that location, random seed increments by 2
@    increase the BCD score and start over at step 1
@
@ 8. Game over:
@    use each digit of the binary coded decimal score to write the digits to the buffered score screen
@    Fill the screen with the buffered score screen
@    reset all values that need to be reset, 
@    poll for user input to continue
@    clear the screen then draw the snake and apple to the original locations

@ the screen is mapped to $1000-$10FF
@ each byte contains 4 pixels, 2 bits each, for 4 distinct colors
@ 00 = black
@ 01 = green
@ 10 = red
@ 11 = white
@ the screen is 32x32 pixels, and turning the row and column into the address and offset is done with this equation:
@ address = row * 8 + col / 4
@ offset = col % 4

org $1000
screen: ds.b    123 ; 0…122 all zeros
        dc.b    $55 ; byte 123: 01 01 01 01 (green in cols 12,13,14,15 of row 15)
        ds.b    2   ; 2 empty bytes
        dc.b    $02 ; byte 126: 00 00 00 10 (red in col 27 of row 15)
        ds.b    129 ; pad out to 256 bytes total

@ the snake buffer is stored in two separate arrays
@ one array contains the x positions, and the other contains the y positions
@ this is done because one axis is 5 bits wide, so you cant store both in one byte
@ storing them contiguously in 256 bytes allows for some optimizations later on 

org $1100
@ array of snake x positions
snakeX:     dc.b    12,13,14,15
            ds.b    252

org $1200
@ array of snake y positions
snakeY:     dc.b    15,15,15,15
            ds.b    252

@ to avoid "snaking" through memory, the snake buffer is a cyclical array
@ this abuses the fact that the registers are the same width as the arrays, 
@ so no extra logic other than adding one is needed to wrap around to the beginning

org $1300
@ pointers to the head and tail in the snake arrays
headPointer:    dc.b    3
tailPointer:    dc.b    0

@ these pointers are used for reading & writing to the snake buffers
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

org $1600
@ lookup table of apple bitmasks, maybe we can reuse the snake and then shift right once
appleMask:  dc.b    %10000000,%00100000,%00001000,%00000010

org $1700
@ lookup table of bitmasks to delete or extract a pixel from the screen
eraseMask:  dc.b    %00111111,%11001111,%11110011,%11111100

org $1800
@ lookup table of 256 pre-generated random numbers (LFSR takes like 40 instructions, while this takes 3)
randomTable:    dc.b    $95,$DB,$EB,$6A,$72,$23,$1F,$BF,$8E,$34,$EC,$54,$62,$74,$6C,$BB,$AB,$EA,$61,$3B,$E4,$37,$5E,$7E,$9D,$49,$F1,$86,$D2,$8D,$60,$DD,$65,$68,$BE,$CB,$6E,$1B,$CA,$8C,$79,$82,$4E,$22,$97,$E8,$6B,$75,$87,$B2,$5D,$C3,$03,$6F,$41,$F0,$A3,$26,$0B,$39,$80,$12,$C7,$64,$C9,$2C,$3C,$15,$E9,$1E,$C1,$D7,$CD,$F3,$AA,$28,$F2,$9B,$B0,$4A,$29,$7B,$24,$35,$ED,$E3,$E1,$04,$0E,$3D,$FD,$98,$0C,$C4,$43,$D8,$33,$84,$D9,$A2,$3A,$A8,$2F,$DC,$D1,$53,$76,$C2,$F5,$81,$EF,$85,$01,$69,$D4,$D0,$99,$C8,$A6,$71,$2D,$17,$55,$07,$E2,$B5,$BD,$D3,$BA,$20,$A5,$E5,$47,$44,$FF,$4D,$BC,$FE,$4B,$0D,$36,$90,$9A,$6D,$5B,$30,$4F,$2A,$42,$1C,$A9,$66,$EE,$B6,$3F,$F8,$FB,$9E,$0F,$88,$2B,$B8,$46,$F4,$25,$16,$38,$AF,$F7,$9F,$D5,$13,$1D,$96,$00,$77,$AE,$CF,$A0,$CC,$10,$11,$1A,$02,$E0,$06,$C5,$94,$93,$A4,$5C,$21,$7F,$DE,$40,$AC,$08,$7D,$8F,$A7,$83,$8A,$7C,$DF,$E7,$48,$59,$19,$91,$57,$B4,$50,$DA,$2E,$4C,$52,$73,$3E,$92,$B3,$C0,$32,$B9,$7A,$5A,$89,$51,$FA,$56,$27,$AD,$58,$CE,$C6,$67,$0A,$B7,$14,$F9,$A1,$18,$B1,$63,$FC,$45,$78,$31,$F6,$E6,$70,$8B,$9C,$D6,$5F,$09,$05


org $1504
@ pointers to masks
snakeMaskAddr:  dc.b    $00,$15
appleMaskAddr:  dc.b    $00,$16
eraseMaskAddr:  dc.b    $00,$17

@ pointer to the random table
seedAddress:    dc.b    $00,$18

@ game over screen buffer
org $1900
gameOverScreen: dc.b    $00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$0F,$CF,$CF,$CF,$CF,$C0,$00,$00,$0C,$0C,$0C,$CC,$CC,$00,$00,$00,$0C,$0C,$0C,$CC,$CC,$0C,$00,$00,$0F,$CC,$0C,$CC,$CC,$00,$00,$00,$00,$CC,$0C,$CF,$0F,$00,$00,$00,$00,$CC,$0C,$CC,$CC,$0C,$00,$00,$00,$CC,$0C,$CC,$CC,$00,$00,$00,$0F,$CF,$CF,$CC,$CF,$C0,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00

@ BCD score counter
org $1A00
score:          dc.b    0,0,0
scorePointer:   dc.b    $00,$1A
overPointer:    dc.b    $00,$19

org $1B00
@ lookup table for digit table
digit0: dc.b    $FC,$CC,$CC,$CC,$CC,$CC,$CC,$FC
digit1: dc.b    $30,$30,$30,$30,$30,$30,$30,$30
digit2: dc.b    $FC,$0C,$0C,$FC,$C0,$C0,$C0,$FC
digit3: dc.b    $FC,$0C,$0C,$FC,$0C,$0C,$0C,$FC
digit4: dc.b    $CC,$CC,$CC,$FC,$0C,$0C,$0C,$0C
digit5: dc.b    $FC,$C0,$C0,$FC,$0C,$0C,$0C,$FC
digit6: dc.b    $FC,$C0,$C0,$FC,$CC,$CC,$CC,$FC
digit7: dc.b    $FC,$0C,$0C,$0C,$0C,$0C,$0C,$0C
digit8: dc.b    $FC,$CC,$CC,$FC,$CC,$CC,$CC,$FC
digit9: dc.b    $FC,$CC,$CC,$FC,$0C,$0C,$0C,$FC

digitPointer:   dc.b    $00,$1B

@ set the program to start at 0 in rom
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
    @ set the direction based on which keys are presed
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
    beq16 gameLoop

    @ set the new directions
setDir0:
    ldaa #0
    staa dir
    beq16 gameLoop

setDir1:
    ldaa #1
    staa dir
    bne16 gameLoop

setDir2:
    ldaa #2
    staa dir
    bne16 gameLoop

setDir3:
    ldaa #3
    staa dir
    bne16 gameLoop

gameLoop:
    @ move pointers to head instead of tail
    ldaa headPointer

    staa snakeXAddr
    staa snakeYAddr

    ldx snakeXAddr
    ldy snakeYAddr

    @ update the seed 
    ldaa seedAddress
    ldab #1
    sum_ba
    staa seedAddress

    @ move in each direction based on dir
    ldaa dir

    beq16 moveRight ; if dir == 0, move right

    ldab #$FF ; keep subtracting one

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

    @ check if head == tail. if this is true, the snake length is 256, and the buffer is full. the game should end here
    @ get two's complement of the tail pointer
    ldaa tailPointer
    coma
    sum_ab

    @ reload the head pointer
    ldaa headPointer

    sum_ba ; if this is 0, they are equal, and the player has won
    beq16 gameOver

    ldaa headPointer

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

    staa tempX ; store the extracted pixel temporarily

    @ load b with the snake mask
    ldx snakeMaskAddr
    ldab 0,x
    comb ; get the complement of b

    @ if A & /B is 0, then we know there is a collision because the pixel is green
    and_ba 

    beq16 gameOver

    ldaa tempX ; load the extracted pixel again
    @ set the apple mask to the snake mask position
    ldab snakeMaskAddr
    stab appleMaskAddr

    @ load b with the apple mask
    ldx appleMaskAddr
    ldab 0,x
    comb ; get the complement of b

    @ if A & /B is 0, we know there is an apple because the pixel is red
    and_ba

    beq16 eatApple

    @ if A & /B is not 0, we know the pixel is white, which means it collided with itself and theres an apple in its body
    bne16 gameOver


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

    @ use the seed to generate a pseudo random number generator
    ldx seedAddress
    ldaa 0,x
    staa address ; use that for screen byte

    @ increment the seed (wraps around to 0 if >= 256)    
    ldaa seedAddress
    ldab #1
    sum_ba
    staa seedAddress

    @ get another random value
    ldx seedAddress
    ldaa 0,x
    staa address

    ldab #3 ; get a number from 0 to 3 to get the pixel
    and_ab

    @ use that for the mask
    stab appleMaskAddr
    ldx appleMaskAddr
    ldab 0,x ; get the pixel value for the apple

    ldx address
    ldaa 0,x ; get whats at the screen for the chosen address

    @ write the new apple to the screen
    or_ba

    ldx address
    staa 0,x

    @ increment the seed (wraps around to 0 if >= 256)    
    ldaa seedAddress
    ldab #1
    sum_ba
    staa seedAddress

    @ add one to the score with binary coded decimal
    ldx scorePointer
    ldaa 0,x
    sum_ba
    staa 0,x ; store lower digit plus 1

    ldab #$F6 ; negative 10
    sum_ba ; if lower digit - 10 == 0, then it need to be rolled over to 0 and the next digit needs to be incremented

    bne16 readKeys ; if not equal to 0, just exit

    staa 0,x ; write the lowest digit with 0

    ldaa 1,x ; load the next digit
    ldab #1
    sum_ba ; increment one
    staa 1,x ; store the next digit plus 1

    ldab #$F6 ; negative 10
    sum_ba ; if middle digit - 10 == 0, then it need to be rolled over to 0 and the next digit needs to be incremented

    bne16 readKeys ; if not equal to 0, exit
    
    staa 1,x ; load the middle digit with 0

    ldaa 2,x
    ldab #1
    sum_ba ; increment once
    staa 2,x ; update the last digit

    ldaa #0
    beq16 readKeys

gameOver:
    ldaa #0
    staa tempX ; store this temporary variable to repeat this three time

writeScore:
    @ load the numbers to the screen
    ldab tempX
    stab scorePointer ; update score pointer with the current number to draw
    ldx scorePointer
    ldaa 0,x ; get lower digit
    
    @ multiply digit by 8 to get the pixels for it
    shfa_l
    shfa_l
    shfa_l

    staa digitPointer
    ldy digitPointer ; move y to the digit pointer

    ldaa #133 ; starting position for the lowest digit
    @ get twos complement of tempX and add it to a to get the proper column
    comb 
    sum_ba
    ldab #1
    sum_ba

    staa overPointer
    ldx overPointer

    @ load each pixel into the correct locations
    ldaa 0,y
    staa 0,x

    ldaa 1,y
    staa 8,x

    ldaa 2,y
    staa 16,x

    ldaa 3,y
    staa 24,x

    ldaa 4,y
    staa 32,x

    ldaa 5,y
    staa 40,x

    ldaa 6,y
    staa 48,x

    ldaa 7,y
    staa 56,x

    ldaa tempX
    
    @ increment tempX
    ldab #1
    sum_ba
    staa tempX

    ldab #$FD ; negative 3
    sum_ba

    @ if tempX == 3, continue
    bne16 writeScore

    @ load screen and buffer pointers, initialize a at 0
    ldaa #0
    staa address
    staa overPointer

    ldx address
    ldy overPointer

fillScreen:
    ldab 0,y
    stab 0,x
    inx
    iny

    ldab #1
    sum_ba

    @ if a is 0, it wrapped around when it hit 256, meaning we reached the end of the arrays
    bne16 fillScreen

restart:
    @ reset all values that need to be reset
    ldaa #0

    staa dir ; reset direction to 0

    @ reset score to 0
    staa scorePointer
    ldx scorePointer
    
    @ reset score
    staa 0,x
    staa 1,x
    staa 2,x

    @ reset snake pointers
    ldab #3
    staa tailPointer
    stab headPointer

    @ reset snake body
    staa snakeXAddr
    staa snakeYAddr

    @ reset rows to 15
    ldy snakeYAddr
    ldaa #15
    staa 0,y
    staa 1,y
    staa 2,y
    staa 3,y

    @ reset columns to proper values
    ldx snakeXAddr
    staa 3,x
    ldaa #14
    staa 2,x
    ldaa #13
    staa 1,x
    ldaa #12
    staa 0,x

    ldaa #0
    
    staa address
    ldx address
    
    @ reset keys so the next step can be triggered by user input
    staa up
    staa down
    staa left
    staa right

pollKeysForReset:
    ldy #right
    ldaa 0,y
    bne16 resetScreen

    ldy #down
    ldaa 0,y
    bne16 resetScreen

    ldy #left
    ldaa 0,y
    bne16 resetScreen

    ldy #up
    ldaa 0,y
    bne16 resetScreen

    beq16 pollKeysForReset

    @ reset the screen
resetScreen:
    ldab #0
    stab 0,x
    inx

    ldab #1
    sum_ba
    
    @ keep resetting the bytes until a == 0, which means it went through all 256 bytes
    bne16 resetScreen

resetSnake:
    @ add the snake and apple back to the screen
    ldaa #123
    staa address
    ldx address

    @ add the snake
    ldaa #$55
    staa 0,x

    ldaa #126
    staa address
    ldx address

    @ add the apple
    ldaa #$02
    staa 0,x

    ldaa #0

    @ reset keys so they dont die instantly
    staa up
    staa down
    staa left
    staa right

    beq16 removeTail
