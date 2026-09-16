v {xschem version=3.4.8RC file_version=1.2}
G {}
K {}
V {}
S {}
E {}
T {External resistor bias for the extracted GF180 sensor} 80 50 0 0 0.4 0.4 {}
T {Existing on-chip mirrors connect to BIAS and PREF. These resistors belong on the PCB.} 80 100 0 0 0.25 0.25 {}
C {devices/iopin.sym} 200 170 0 0 {name=p1 lab=VDD}
C {devices/iopin.sym} 200 370 0 0 {name=p2 lab=GND}
C {devices/res.sym} 200 200 0 0 {name=Rcolumn value=5.1meg m=1}
C {devices/iopin.sym} 200 250 0 0 {name=p3 lab=BIAS}
N 200 230 200 290 {}
C {devices/capa.sym} 200 320 0 0 {name=Ccolumn value=5p m=1}
N 200 350 200 370 {}
C {devices/iopin.sym} 600 270 0 0 {name=p4 lab=PREF}
C {devices/res.sym} 600 300 0 0 {name=Rbuffer value=49.9k m=1}
C {devices/capa.sym} 740 300 0 0 {name=Cbuffer value=5p m=1}
N 600 270 740 270 {}
N 600 330 740 330 {}
C {devices/lab_pin.sym} 600 330 0 0 {name=l1 sig_type=std_logic lab=GND}
T {5 pF per pin is an assumed board/pad load.} 420 385 0 0 0.23 0.23 {}
T {Pad/ESD extraction, resistor TC, noise and leakage remain unmodeled.} 80 440 0 0 0.23 0.23 {}
