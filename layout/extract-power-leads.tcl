drc off
gds read /foss/designs/build/power-ring/power_leads.gds
load power_leads
select top cell
box values 0um 0um 1200um 1200um
erase labels
foreach {n z x y idx role} {VDD_CORE m4 384 473 1 output VSS_CORE m4 384 469 2 output VDD_RING m2 385.735 365 3 input VSS_RING m2 460.735 355 4 input} {
 set xmin [expr {$x-0.1}]
 set xmax [expr {$x+0.1}]
 set ymin [expr {$y-0.1}]
 set ymax [expr {$y+0.1}]
 box values ${xmin}um ${ymin}um ${xmax}um ${ymax}um
 label $n center $z
 port make $idx
 port $n class $role
}
extract do capacitance
extract do coupling
extract do resistance
extresist threshold 0
extresist minres 1
extresist mindelay 0
extresist simplify off
extract all
ext2spice lvs
ext2spice cthresh 0
ext2spice extresist on
ext2spice subcircuits top on
ext2spice -o power_leads_rc.spice
quit -noprompt
