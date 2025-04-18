@ Snake
@ Author: Julian Dominguez
@ Date: 04-17-2025

org $1000
screen: ds.b    256 ; 0x1000 to 0x10FF for the screen

up:     equ     $1400
left:   equ     $1401
down:   equ     $1402
right:  equ     $1403

org $1409

headRow:    dc.b    15
headCol:    dc.b    15

tailRow:    dc.b    15
tailCol:    dc.b    15

nextRow:    dc.b    0
nextCol:    dc.b    0

appleRow:   dc.b    0
appleCol:   dc.b    0

mask:       dc.b    $80

seed:       dc.b    $42

address:    dc.b    $00,$10

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
    ldx address
    
    ldaa #0
    staa address

fillScreen:
    ldaa address
    ldab #$03 ; get last two bits to do address mod 8
    and_ab

    @ get the pixel at the address
    ldx address
    ldaa 0,x

    

    ldaa address
    ldab #1
    sum_ba
    staa address

    bne fillScreen

exit:
    ldaa #0
    beq exit

