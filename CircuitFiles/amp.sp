**aaaa
.inc 130nm.txt
.inc designparam.cir
m1 6  4  3 3 pfet1 l=lm1 w=wm1 ad=lm1*wm1 as=lm1*wm1 pd=2*(lm1+wm1) ps=2*(lm1+wm1)  
m2 7  5  3 3  pfet2 l=lm2 w=wm2 ad=lm2*wm2 as=lm2*wm2 pd=2*(lm2+wm2) ps=2*(lm2+wm2)  
m3 2  2  1 1 pfet3 l=lm3 w=wm3 ad=lm3*wm3 as=lm3*wm3 pd=2*(lm3+wm3) ps=2*(lm3+wm3)  
m4 3  2  1 1 pfet4 l=lm4 w=wm4 ad=lm4*wm4 as=lm4*wm4 pd=2*(lm4+wm4) ps=2*(lm4+wm4)  
m5 6  6  8 8 nfet1 l=lm5 w=wm5 ad=lm5*wm5 as=lm5*wm5 pd=2*(lm5+wm5) ps=2*(lm5+wm5)  
m6 7  6  8 8  nfet2 l=lm6 w=wm6 ad=lm6*wm6 as=lm6*wm6 pd=2*(lm6+wm6) ps=2*(lm6+wm6)  
m7 0 0 0 0 nfet1 l=lm3 w=wm3 ad=lm3*wm3 as=lm3*wm3 pd=2*(lm3+wm3) ps=2*(lm3+wm3)
m8 0 0 0 0 nfet1 l=lm3 w=wm3 ad=lm3*wm3 as=lm3*wm3 pd=2*(lm3+wm3) ps=2*(lm3+wm3)
Rb 2 8 Rb


E1 eng 0 7 0 1
L1 eng 5 1
Cx 5 0 1

*cl 7 0 0.5e-12


Vdd 1 0 DC 1.2
Vss 0 8 DC 0

*vnin 9 0 0
vin 4 0 Vb ac 1

.op
.PARAM AREA='2*WM1*LM1 + 2*WM2*LM2 + 2*WM3*LM3'
VX 1000 0 AREA
RX 1000 0 1K
.option fast
.option post 2
.option sim_mode = client/server
.option OPFILE=1
.op
.ac dec 100 100 10000000000
.TRAN 2n 100n 

.MEAS AC gain max PAR('db(V(7))')
.MEAS AC tmp max par('gain-3')
.MEAS AC BW when par('db(V(7))')= 0      
.MEASURE AC hreal FIND VR(7) WHEN V(7)=1
.MEASURE AC himg  FIND VI(7) WHEN V(7)=1  
.MEAS zPOWER AVG POWER 
.MEAS zSAREA avg PAR(AREA)
.END