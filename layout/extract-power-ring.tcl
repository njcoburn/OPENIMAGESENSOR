drc off
gds read /foss/designs/build/power-ring/power_ring.gds
load power_ring
select top cell
flatten ring_flat
load ring_flat
select top cell
extract do capacitance
extract do coupling
extract do resistance
extresist threshold 1
extresist minres 1
extresist mindelay 0
puts "EXTRACT_STYLE=[extract style]"
extract all
ext2spice lvs
ext2spice cthresh 0
ext2spice extresist on
ext2spice subcircuits top on
ext2spice -o ring_rc.spice
quit -noprompt
