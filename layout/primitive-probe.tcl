# Verify the installed GF180 generator and extraction chain before pixel layout.
load nfet_probe -silent
box values 0 0 0 0
set pars [gf180mcu::nfet_03v3_defaults]
dict set pars w 1.0
dict set pars l 0.5
dict set pars diff_spacing 0.6
dict set pars diff_gate_space 0.4
gf180mcu::nfet_03v3_draw $pars
# Enlarge the gate landing pads to satisfy the metal minimum-area rule.
box values -0.24um 0.665um 0.24um 1.05um
paint metal1
box values -0.24um -1.05um 0.24um -0.665um
paint metal1
# Four explicit terminal ports for independent schematic comparison.
foreach {pin idx x y} {D 1 0.51 0 G 2 0 0.8 S 3 -0.51 0 B 4 0 1.54} {
    box values ${x}um ${y}um ${x}um ${y}um
    label $pin center metal1
    port make $idx
}
select top cell
drc check
drc catchup
puts "PROBE_DRC_COUNT=[drc list count total]"
puts "PROBE_DRC_DETAILS=[drc listall why]"
save nfet_probe
extract all
ext2spice lvs
ext2spice
cif write nfet_probe
gds write nfet_probe.gds
quit -noprompt
