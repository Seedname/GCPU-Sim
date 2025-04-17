dialer: equ     $0701
num:    equ     7
neg1:   equ     $FF

org $100
PhNum:  dc.b    3,9,2,2,5,4,1

main:
    org 0
    ldx #PhNum
    ldaa #Num

loop:
    ldab 0,X
    stab dialer
    inx
    ldab #neg1
    sum_ba
    bne loop

exit:
    beq exit