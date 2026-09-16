foreach {cell length dx} {buffer_pfet 0.5 0.51 mirror_pfet 2.0 1.26} {
 load $cell -silent
 box values 0 0 0 0
 set pars [gf180mcu::pfet_03v3_defaults]
 dict set pars w 20.0
 dict set pars l $length
 dict set pars diff_spacing 0.6
 dict set pars diff_gate_space 0.4
 gf180mcu::pfet_03v3_draw $pars
 if {$length == 0.5} {
  box values -0.24um 10.165um 0.24um 10.55um
  paint metal1
  box values -0.24um -10.55um 0.24um -10.165um
  paint metal1
 }
 foreach {pin idx x y} [list D 1 $dx 0 G 2 0 10.28 S 3 [expr {-$dx}] 0 B 4 0 -11.04] {
  box values ${x}um ${y}um ${x}um ${y}um
  label $pin center metal1
  port make $idx
 }
 select top cell
 drc check
 drc catchup
 puts "${cell}_DRC=[drc listall why]"
 save $cell
 extract all
 ext2spice lvs
 ext2spice
 gds write ${cell}.gds
}
quit -noprompt
