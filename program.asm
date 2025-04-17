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
temp:   dc.b    1

neg1:   equ     $FF
neg2:   equ     $FE
neg3:   equ     $FD
neg4:   equ     $FC
neg5:   equ     $FB
neg6:   equ     $FA
neg7:   equ     $F9
neg8:   equ     $F8

;0000 0000
;0000 0010
;0000 0100
;0000 1000
;0001 0000
;0010 0000
;0100 0000
;1000 0000

main: 
    org 0

readKeys:
    ldy #up
    ldaa 0,y
    bne moveUp

    ldy #down
    ldaa 0,y
    bne moveDown

    ldy #left
    ldaa 0,y
    bne moveLeft

    ldy #right
    ldaa 0,y
    bne moveRight

continue:
    @ load a with the column
    ldaa row
    ldx #screen

getRow:
    @ increment x pointer row times
    inx
    ldab #neg1
    sum_ba
    bne getRow

    @ get bit mask by shifting 1 left by the column    
    ldab #1
    stab temp
    ldaa col

getMask:
    ldab temp
    shfl_b
    stab temp
    ldab #neg1
    sum_ba
    bne getMask

    @ add bitmask to screen
    ldaa temp
    staa 0,x

    ldaa #0
    beq readKeys

moveUp:
    @ when moving up, subtract 4 from the row
    ldaa row
    ldab #neg4
    sum_ba
    staa row

    ldaa #0
    beq continue

moveDown:
    @ when moving down, add 4 to the row
    ldaa row
    ldab #4
    sum_ba
    staa row

    ldaa #0
    beq continue

moveLeft:
    @ when moving left, subtract 1 from the column

    ldaa col
    ldab #neg1
    sum_ba
    staa col

    @ if column is positive, continue
    bp continue

    @ if column goes negative, wrap around to 7
    ldaa #7
    staa col

    ldaa #0
    beq continue

moveRight:
    @ when moving right, add 1 to the column

    ldaa col
    ldab #1
    sum_ba
    staa col

    ldab #neg8
    sum_ba

    @ if column - 8 != 0, continue
    bne continue

    @ if column is 8, wrap around to 0
    ldaa #0
    staa col

    beq continue

exit:
    ldaa #0
    beq exit
