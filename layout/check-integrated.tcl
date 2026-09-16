gds read /foss/designs/build/integrated/sensor_3x3.gds
load sensor_3x3
select top cell
set idx 1
foreach pin {VDD VRESET GND RST0 RST1 RST2 ROW0 ROW1 ROW2 BIAS SEL0 SEL1 SEL2 PREF BUF COL0 COL1 COL2 OUT} {
 catch {port $pin make $idx}
 port $pin index $idx
 incr idx
}
drc check
drc catchup
puts "INTEGRATED_DRC_COUNT=[drc list count total]"
puts "INTEGRATED_DRC_DETAILS=[drc listall why]"
extract all
ext2spice lvs
ext2spice hierarchy on
ext2spice subcircuits top on
ext2spice -o integrated_extracted.spice
quit -noprompt
