gds read /foss/designs/build/array_3x3.gds
load array_3x3
select top cell
# Add explicit top ports to labels read from the GDS.
set idx 1
foreach pin {VDD VRESET GND RST0 RST1 RST2 ROW0 ROW1 ROW2 COL0 COL1 COL2} {
 catch {port $pin make $idx}
 port $pin index $idx
 incr idx
}
drc check
drc catchup
puts "ARRAY_DRC_COUNT=[drc list count total]"
set report [open drc-details.txt w]
puts $report [drc listall why]
close $report
save array_3x3
extract all
ext2spice lvs
ext2spice hierarchy on
ext2spice subcircuits top on
ext2spice -o array_extracted.spice
quit -noprompt
