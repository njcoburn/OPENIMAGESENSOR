v {xschem version=3.4.8RC file_version=1.2}
G {}
K {}
V {}
S {}
E {}
C {symbols/nfet_03v3.sym} 220 -380 0 0 {name=rst W=1u L=0.28u nf=1 m=1 ad=0 as=0 pd=0 ps=0 nrd=0 nrs=0 sa=0 sb=0 sd=0 model=nfet_03v3 spiceprefix=X}
C {devices/lab_pin.sym} 240 -380 0 0 {name=l7 sig_type=std_logic lab=0}
C {devices/lab_pin.sym} 200 -380 0 0 {name=l8 sig_type=std_logic lab=rst}
C {devices/lab_pin.sym} 240 -410 0 0 {name=l9 sig_type=std_logic lab=vreset}
N 240 -350 240 -280 {}
N 240 -280 480 -280 {}
C {devices/lab_pin.sym} 240 -280 0 0 {name=l12 sig_type=std_logic lab=sense}
C {symbols/nfet_03v3.sym} 500 -280 0 0 {name=sf W=5u L=0.5u nf=1 m=1 ad=0 as=0 pd=0 ps=0 nrd=0 nrs=0 sa=0 sb=0 sd=0 model=nfet_03v3 spiceprefix=X}
C {devices/lab_pin.sym} 520 -280 0 0 {name=l14 sig_type=std_logic lab=0}
C {devices/lab_pin.sym} 520 -310 0 0 {name=l15 sig_type=std_logic lab=vdd}
N 520 -250 520 -180 {}
C {symbols/nfet_03v3.sym} 500 -150 0 0 {name=sel W=2u L=0.28u nf=1 m=1 ad=0 as=0 pd=0 ps=0 nrd=0 nrs=0 sa=0 sb=0 sd=0 model=nfet_03v3 spiceprefix=X}
C {devices/lab_pin.sym} 520 -150 0 0 {name=l18 sig_type=std_logic lab=0}
C {devices/lab_pin.sym} 480 -150 0 0 {name=l19 sig_type=std_logic lab=row}
C {devices/lab_pin.sym} 520 -220 0 0 {name=l20 sig_type=std_logic lab=sf}
N 520 -120 520 -80 {}
N 520 -80 700 -80 {}
C {devices/lab_pin.sym} 700 -80 0 0 {name=l23 sig_type=std_logic lab=col}
N 120 -280 120 -220 {}
C {devices/diode.sym} 120 -190 2 0 {name=Dphoto model=photo area=1}
C {devices/lab_pin.sym} 120 -160 0 0 {name=l26 sig_type=std_logic lab=0}
N 240 -280 240 -220 {}
C {devices/capa.sym} 240 -190 0 0 {name=Csense value=10f m=1}
C {devices/lab_pin.sym} 240 -160 0 0 {name=l29 sig_type=std_logic lab=0}
N 360 -280 360 -220 {}
C {devices/isource.sym} 360 -190 0 0 {name=Iphoto value=1p}
C {devices/lab_pin.sym} 360 -160 0 0 {name=l32 sig_type=std_logic lab=0}
N 120 -280 240 -280 {}
N 600 -80 600 -30 {}
C {devices/res.sym} 600 0 0 0 {name=Rload value=1Meg}
C {devices/lab_pin.sym} 600 30 0 0 {name=l36 sig_type=std_logic lab=0}
N 700 -80 700 -30 {}
C {devices/capa.sym} 700 0 0 0 {name=Ccol value=1p m=1}
C {devices/lab_pin.sym} 700 30 0 0 {name=l39 sig_type=std_logic lab=0}
C {devices/vsource.sym} 100 170 0 0 {name=Vdd value="3.3"}
C {devices/lab_pin.sym} 100 140 0 0 {name=l41 sig_type=std_logic lab=vdd}
C {devices/lab_pin.sym} 100 200 0 0 {name=l42 sig_type=std_logic lab=0}
C {devices/vsource.sym} 300 170 0 0 {name=Vrst value="PULSE(3.3 0 20u 10n 10n 979.98u 1m)"}
C {devices/lab_pin.sym} 300 140 0 0 {name=l44 sig_type=std_logic lab=rst}
C {devices/lab_pin.sym} 300 200 0 0 {name=l45 sig_type=std_logic lab=0}
C {devices/vsource.sym} 500 170 0 0 {name=Vrow value="PULSE(0 3.3 920u 10n 10n 60u 1m)"}
C {devices/lab_pin.sym} 500 140 0 0 {name=l47 sig_type=std_logic lab=row}
C {devices/lab_pin.sym} 500 200 0 0 {name=l48 sig_type=std_logic lab=0}
T {GF180 pixel - 2.0 V reset candidate} 80 -510 0 0 0.5 0.5 {}
T {Photodiode capacitance and light current are assumptions.
MOS diffusion area/perimeter = 0 in this initial model.
Row selected 920-980 us each cycle.
1 Mohm passive column load (testbench).} 80 250 0 0 0.3 0.3 {}
C {devices/vsource.sym} 700 170 0 0 {name=Vreset value="2.0"}
C {devices/lab_pin.sym} 700 140 0 0 {name=reset_supply sig_type=std_logic lab=vreset}
C {devices/lab_pin.sym} 700 200 0 0 {name=reset_ground sig_type=std_logic lab=0}
C {devices/code_shown.sym} 850 -470 0 0 {name=SIM only_toplevel=false value=".include /foss/pdks/gf180mcuD/libs.tech/ngspice/design.ngspice
.lib /foss/pdks/gf180mcuD/libs.tech/ngspice/sm141064.ngspice typical
.model photo D(Is=1e-18 N=1 Cjo=0)
.options gmin=1e-17 abstol=1e-16 reltol=1e-5 chgtol=1e-18 trtol=1 method=gear
.ic v(sense)=0 v(sf)=0 v(col)=0
.control
set num_threads=1
save all
set wr_singlescale
set wr_vecnames
foreach light 0 1p 5p
alter Iphoto $light
tran 0.2u 20m uic
write /foss/designs/simulations/reset_candidate_raw_$light
wrdata /foss/designs/simulations/reset_candidate_$light v(rst) v(row) v(sense) v(col)
end
.endc"}
