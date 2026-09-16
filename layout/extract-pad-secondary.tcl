drc off
gds read /foss/designs/build/pad-layout/analog_secondary.gds
load analog_secondary
select top cell
extract do capacitance
extract do coupling
extract do resistance
extract all
ext2spice lvs
ext2spice hierarchy on
ext2spice cthresh 0
ext2spice subcircuits top on
ext2spice -o secondary_c.spice
quit -noprompt
