org $1000
screen: ds.b    128 ; 0x1000 to 0x1080 for the screen

org $1400
keys:   ds.b    4   ; block out the next 4 bytes for keys
up:     equ     $1400
left:   equ     $1401
down:   equ     $1402
right:  equ     $1403

org $1409           ; 0x1409 to 0x140B for the variables
row:    dc.b    0
col:    dc.b    0
mask:   dc.b    $80

neg1:   equ     $FF
neg8:   equ     $F8

address:    dc.b    $00,$10

org $1500
maskTable:  dc.b    $80,$40,$20,$10,$08,$04,$02,$01

maskAdr:    dc.b    $00,$15


main: 
    org 0

readKeys:
    ldy #left
    ldaa 0,y
    bne moveLeft

    ldy #right
    ldaa 0,y
    bne moveRight

    ldy #up
    ldaa 0,y
    bne moveUp

    ldy #down
    ldaa 0,y
    bne moveDown
    
continue:
    @ load a with the row
    ldaa row
    
    @ multiply the row by 4
    shfa_l
    shfa_l

    @ load b with the col
    ldab col
    
    @ get byte by dividing by 8
    shfb_r
    shfb_r
    shfb_r

    sum_ba ; add a and b to get the byte

    staa address ; store the address of the byte


    @ find the col % 8
    @ find this by doing col & $07. this will get the last 3 bits, or the octal word that comes out
    ldaa col
    ldab #07
    and_ba ; this will get the last 3 bits of the col

@     ldab #$80 ; load the mask
@     stab mask
@     beq writeScreen ; dont do anything if col % 8 is 0

@ getMask:
@     ldab mask
@     shfb_r ; shift right 1 bit
@     stab mask ; store the new mask
@     ldab #neg1
@     sum_ba
@     bne getMask

    @ find the bitmask with the lookup table
    ldab maskAdr ; load b with lower byte of the mask table address
    sum_ab ; add col % 8 to the lower byte of the mask table address
    stab maskAdr ; store the lower byte of the mask table address

    ldx maskAdr

    @ restore the lower byte
    ldaa #0
    staa maskAdr

    @ load bitmask into a, and the screen into b
    ldaa 0,x ; get the bitmask from the table

writeScreen:
    ldx address ; load the address into x

    @ ldaa mask ; load the mask into b
    ldab 0,x

    or_ba ; add the bitmask to the screen
    staa 0,x

    ldaa #0
    beq readKeys

moveUp:
    @ when moving up, subtract 1 from the row
    ldaa row
    ldab #neg1
    sum_ba

    @ if it goes below 0, wrap around to 31
    ldab #31
    and_ba

    staa row

    ldaa #0
    beq continue

moveDown:
    @ when moving down, add 1 to the row
    ldaa row
    ldab #1
    sum_ba

    @ clip at 31
    ldab #31
    and_ba

    staa row

    ldaa #0
    beq continue

moveLeft:
    @ when moving left, subtract 1 from the column
    ldaa col
    ldab #neg1
    sum_ba

    @ if it goes below 0, wrap around to 31
    ldab #31
    and_ba

    staa col

    ldaa #0
    beq continue

moveRight:
    @ when moving right, add 1 to the column

    ldaa col
    ldab #1
    sum_ba

    @ clip at 31 (if col is 32, wrap around to 0)
    ldab #31
    and_ba

    staa col

    ldaa #0
    beq continue

exit:
    ldaa #0
    beq exit
