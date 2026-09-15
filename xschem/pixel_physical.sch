v {xschem version=3.4.8RC file_version=1.2}
G {}
K {}
V {}
S {}
E {}
C {symbols/nfet_03v3.sym} 220 -360 0 0 {name=rst W=1u L=0.5u nf=1 m=1 ad=0.44p as=0.44p pd=2.88u ps=2.88u nrd=0 nrs=0 sa=0 sb=0 sd=0 model=nfet_03v3 spiceprefix=X}
C {devices/lab_pin.sym} 240 -390 0 0 {name=l7 sig_type=std_logic lab=VRESET}
C {devices/lab_pin.sym} 200 -360 0 0 {name=l8 sig_type=std_logic lab=RST}
C {devices/lab_pin.sym} 240 -330 0 0 {name=l9 sig_type=std_logic lab=sense}
C {devices/lab_pin.sym} 240 -360 0 0 {name=l10 sig_type=std_logic lab=GND}
C {symbols/nfet_03v3.sym} 500 -260 0 0 {name=sf W=1u L=0.5u nf=1 m=1 ad=0.44p as=0.44p pd=2.88u ps=2.88u nrd=0 nrs=0 sa=0 sb=0 sd=0 model=nfet_03v3 spiceprefix=X}
C {devices/lab_pin.sym} 520 -290 0 0 {name=l12 sig_type=std_logic lab=VDD}
C {devices/lab_pin.sym} 480 -260 0 0 {name=l13 sig_type=std_logic lab=sense}
C {devices/lab_pin.sym} 520 -230 0 0 {name=l14 sig_type=std_logic lab=sf}
C {devices/lab_pin.sym} 520 -260 0 0 {name=l15 sig_type=std_logic lab=GND}
C {symbols/nfet_03v3.sym} 500 -100 0 0 {name=sel W=1u L=0.5u nf=1 m=1 ad=0.44p as=0.44p pd=2.88u ps=2.88u nrd=0 nrs=0 sa=0 sb=0 sd=0 model=nfet_03v3 spiceprefix=X}
C {devices/lab_pin.sym} 520 -130 0 0 {name=l17 sig_type=std_logic lab=sf}
C {devices/lab_pin.sym} 480 -100 0 0 {name=l18 sig_type=std_logic lab=ROW}
C {devices/lab_pin.sym} 520 -70 0 0 {name=l19 sig_type=std_logic lab=COL}
C {devices/lab_pin.sym} 520 -100 0 0 {name=l20 sig_type=std_logic lab=GND}
N 240 -330 240 -260 {}
N 240 -260 480 -260 {}
N 520 -230 520 -130 {}
C {symbols/diode_nd2ps_03v3.sym} 240 -150 2 0 {name=Dphoto model=diode_nd2ps_03v3 r_w=5u r_l=5u m=1}
N 240 -260 240 -180 {}
C {devices/lab_pin.sym} 240 -120 0 0 {name=l26 sig_type=std_logic lab=GND}
C {devices/iopin.sym} 80 50 0 0 {name=p27 lab=VDD}
C {devices/iopin.sym} 190 50 0 0 {name=p28 lab=VRESET}
C {devices/iopin.sym} 300 50 0 0 {name=p29 lab=GND}
C {devices/iopin.sym} 410 50 0 0 {name=p30 lab=RST}
C {devices/iopin.sym} 520 50 0 0 {name=p31 lab=ROW}
C {devices/iopin.sym} 630 50 0 0 {name=p32 lab=COL}
T {Physical GF180 pixel: 3 NMOS + 5 x 5 um N+/substrate diode} 60 -470 0 0 0.4 0.4 {}
T {No optical current source or ideal capacitor in the physical cell.
All NMOS: W=1 um, L=0.5 um; junction geometry from the primitive.} 80 130 0 0 0.3 0.3 {}
