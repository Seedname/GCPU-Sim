org $1000
screen: ds.b    128 ; 0x1000 to 0x1080 for the screen

up:     equ     $1400
left:   equ     $1401
down:   equ     $1402
right:  equ     $1403
@ w:      equ     $1404
@ a:      equ     $1405
@ s:      equ     $1406
@ d:      equ     $1407
@ space:  equ     $1408

org $1409
row:    dc.b    0
col:    dc.b    0
temp:   dc.b    $80
mod:    dc.b    0

neg1:   equ     $FF
neg8:   equ     $F8

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
    ldx #screen
    beq afterGetRow
    ldab #neg1

getRow:
    @ increment x pointer row * 4 times
    inx
    inx
    inx
    inx
  
    sum_ba ; decrement a

    bne getRow ; if not zero, keep going

afterGetRow:
    @ load a with the col
    ldaa col
    
    @ get box by dividing by 8
    shfa_r
    shfa_r
    shfa_r

    @ move x pointer to the box
    beq afterGetCol
    ldab #neg1

getCol:
    inx
    sum_ba
    bne getCol

afterGetCol:
    @ find the col % 8
    ldaa col
    ldab #neg8

getMod:
    sum_ba
    @ if still positive, keep subtracting
    bp getMod

    @ if negative, add an 8 to get the mod
    ldab #8
    sum_ba

    staa mod

    ldab #$80 ; 1000 0000 bitmask
    stab temp
    
    beq writeScreen ; dont modify the bitmask if the modulus is 0

    @ shift right to get the bitmask
getMask:
    ldab temp
    shfb_r
    stab temp
    ldab #neg1
    sum_ba
    bne getMask ; if modulus zero, keep going

writeScreen:
    @ load bitmask into a, and the screen into b
    ldaa temp
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

    @ clip at 31
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
    @ when moving left, subtract 1 from the column, and wrap around to 31
    ldaa col

    @ if column == 0, wrap around to 31
    ldab #31
    stab col

    beq continue

    @ else, subtract 1 from the column
    ldab #neg1
    sum_ba
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
