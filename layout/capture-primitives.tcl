# First physical capture-column devices, using the installed GF180 generators.
# Run in a fresh experiment directory with the pinned tools image.
drc off
load capture_plate -silent
box values 0 0 0 0
set pars [gf180mcu::cap_mim_2p0fF_defaults]
if {![info exists plate_width_um]} {set plate_width_um 64.0}
if {![info exists plate_length_um]} {set plate_length_um 38.880}
dict set pars w $plate_width_um
dict set pars l $plate_length_um
gf180mcu::cap_mim_2p0fF_draw $pars
foreach {pin idx x y} [list STORE 1 0 0 GND 2 [expr {$plate_width_um / 2 + 0.67}] 0] {
 box values ${x}um ${y}um ${x}um ${y}um
 label $pin center metal5
 port make $idx
}
select top cell
drc on
drc check
drc catchup
puts "PLATE_DRC_COUNT=[drc list count total]"
puts "PLATE_DRC_DETAILS=[drc listall why]"
save capture_plate
extract all
ext2spice lvs
ext2spice
gds write capture_plate.gds

load capture_pfet -silent
box values 0 0 0 0
set pars [gf180mcu::pfet_03v3_defaults]
dict set pars w 2.0
dict set pars l 0.5
dict set pars diff_spacing 0.6
dict set pars diff_gate_space 0.4
gf180mcu::pfet_03v3_draw $pars
# Enlarge gate pads for the minimum metal-area rule.
box values -0.24um 1.165um 0.24um 1.55um
paint metal1
box values -0.24um -1.55um 0.24um -1.165um
paint metal1
foreach {pin idx x y} {D 1 0.51 0 G 2 0 1.28 S 3 -0.51 0 B 4 0 -2.04} {
 box values ${x}um ${y}um ${x}um ${y}um
 label $pin center metal1
 port make $idx
}
select top cell
drc check
drc catchup
puts "PFET_DRC_COUNT=[drc list count total]"
puts "PFET_DRC_DETAILS=[drc listall why]"
save capture_pfet
extract all
ext2spice lvs
ext2spice
gds write capture_pfet.gds
quit -noprompt
