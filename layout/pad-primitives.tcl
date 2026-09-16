drc off
foreach {cell device w l} {protect_lo diode_nd2ps_03v3 1 12 protect_hi diode_pd2nw_03v3 1 12 protect_res ppolyf_u 3.2 1.0} {
 load $cell -silent
 box values 0 0 0 0
 set pars [gf180mcu::${device}_defaults]
 dict set pars w $w
 dict set pars l $l
 gf180mcu::${device}_draw $pars
 save $cell
 gds write ${cell}.gds
 extract all
 ext2spice lvs
 ext2spice
 drc on
 drc check
 drc catchup
 puts "${cell}_DRC=[drc listall why]"
 drc off
}
quit -noprompt
