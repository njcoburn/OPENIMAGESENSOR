drc off
load bias_nfet -silent
box values 0 0 0 0
set pars [gf180mcu::nfet_03v3_defaults]
dict set pars w 2.0
dict set pars l 2.0
dict set pars diff_spacing 0.6
dict set pars diff_gate_space 0.4
gf180mcu::nfet_03v3_draw $pars
foreach {pin idx x y} {D 1 1.26 0 G 2 0 1.28 S 3 -1.26 0 B 4 0 -2.04} {
 box values ${x}um ${y}um ${x}um ${y}um
 label $pin center metal1
 port make $idx
}
select top cell
drc on
drc check
drc catchup
puts "BIAS_DRC=[drc listall why]"
save bias_nfet
extract all
ext2spice lvs
ext2spice
 gds write bias_nfet.gds
quit -noprompt
