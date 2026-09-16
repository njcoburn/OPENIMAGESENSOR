puts "MAGIC_VERSION=[version]"
drc off
gds read $env(PEX_GDS)
load sensor_3x3
select top cell
flatten rc_sensor
load rc_sensor
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
ext2spice -o sensor_rc.spice
quit -noprompt
