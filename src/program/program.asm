@ Snake

org $1000
screen: ds.b    128 ; 0x1000 to 0x1080 for the screen

up:     equ     $1400
left:   equ     $1401
down:   equ     $1402
right:  equ     $1403

org $1409
row:    dc.b    0
col:    dc.b    0
temp:   dc.b    $80
mod:    dc.b    0
