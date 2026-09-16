gds read /foss/designs/build/output_buffer.gds
load output_buffer
select top cell
set idx 1
foreach pin {IN BUF PREF VDD GND} {
 catch {port $pin make $idx}
 port $pin index $idx
 incr idx
}
drc check
drc catchup
puts "BUFFER_DRC_COUNT=[drc list count total]"
puts "BUFFER_DRC_DETAILS=[drc listall why]"
extract all
ext2spice lvs
ext2spice hierarchy on
ext2spice subcircuits top on
ext2spice -o buffer_extracted.spice
quit -noprompt
