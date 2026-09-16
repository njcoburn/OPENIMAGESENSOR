gds read /foss/designs/build/pad-layout/analog_secondary.gds
load analog_secondary
select top cell
foreach {pin idx} {PAD 1 CORE 2 VDD 3 VSS 4} {
 catch {port $pin make $idx}
 port $pin index $idx
}
drc check
drc catchup
puts "SECONDARY_DRC_COUNT=[drc list count total]"
puts "SECONDARY_DRC_DETAILS=[drc listall why]"
extract all
ext2spice lvs
ext2spice hierarchy on
ext2spice subcircuits top on
ext2spice -o secondary_extracted.spice
quit -noprompt
