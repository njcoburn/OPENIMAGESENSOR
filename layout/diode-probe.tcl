load photodiode -silent
box values 0 0 0 0
set pars [gf180mcu::diode_nd2ps_03v3_defaults]
dict set pars w 5
dict set pars l 5
gf180mcu::diode_nd2ps_03v3_draw $pars
# Replace the blanket central contact array with a small edge contact.
box values -2.5um -2.5um 2.5um 2.5um
erase metal1
erase ndic
paint ndiode
box values 1.885um -0.115um 2.115um 0.115um
paint ndic
box values 1.8um -0.2um 2.2um 0.2um
paint metal1
foreach {pin idx x y} {A 1 0 -2.99 K 2 2 0} {
 box values ${x}um ${y}um ${x}um ${y}um
 label $pin center metal1
 port make $idx
}
select top cell
drc check
drc catchup
puts "DIODE_DRC_COUNT=[drc list count total]"
puts "DIODE_DRC_DETAILS=[drc listall why]"
save photodiode
extract all
ext2spice lvs
ext2spice
gds write photodiode.gds
quit -noprompt
