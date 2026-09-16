drc off
gds read /foss/designs/build/power-ring/power_ring.gds
load power_ring
select top cell
# Flatten for device LVS; distributed resistance extraction is separate.
flatten ring_flat
load ring_flat
select top cell
extract no capacitance
extract no coupling
extract no resistance
extract all
ext2spice lvs
ext2spice extresist off
ext2spice short resistor
ext2spice -o ring_flat_lvs.spice ring_flat
quit -noprompt
