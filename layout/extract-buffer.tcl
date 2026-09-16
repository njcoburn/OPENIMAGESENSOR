puts "MAGIC_VERSION=[version]"
drc off
gds read $env(PEX_GDS)
load output_buffer
select top cell
flatten rc_buffer
load rc_buffer
select top cell
extract do capacitance
extract do coupling
extract do resistance
extresist threshold 1000
extresist minres 100
extresist mindelay 0
puts "EXTRACT_STYLE=[extract style]"
extract all
ext2spice lvs
ext2spice cthresh 0
ext2spice extresist on
ext2spice subcircuits top on
ext2spice -o buffer_rc.spice
quit -noprompt
