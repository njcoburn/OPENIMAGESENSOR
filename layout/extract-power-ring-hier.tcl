drc off
gds read /foss/designs/build/power-ring/power_ring_macroflat.gds
load power_ring
select top cell
extract do capacitance
extract do coupling
extract do resistance
extresist threshold 0
extresist minres 1
extresist mindelay 0
extresist simplify off
extract all
ext2spice lvs
ext2spice cthresh 0
ext2spice extresist on
ext2spice hierarchy on
ext2spice short resistor
ext2spice subcircuits top on
ext2spice -o ring_rc.spice
quit -noprompt
