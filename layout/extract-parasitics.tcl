# Run from a dedicated output directory; delivered GDS remains unchanged.
puts "MAGIC_VERSION=[version]"
gds read $env(PEX_GDS)
load array_3x3
select top cell
set idx 1
foreach pin {VDD VRESET GND RST0 RST1 RST2 ROW0 ROW1 ROW2 COL0 COL1 COL2} {
 catch {port $pin make $idx}
 port $pin index $idx
 incr idx
}
extract do capacitance
extract do coupling
puts "EXTRACT_STYLE=[extract style]"
extract all
ext2spice lvs
ext2spice cthresh 0
ext2spice hierarchy on
ext2spice subcircuits top on
ext2spice -o array_capacitance.spice
quit -noprompt
