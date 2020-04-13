**aaaa

.INC param.cir
.INC 130nm.txt

********Pre-Amplifier**************
m1 2 1 0 0 nfet l=lm1 w=wm1 ad=lm1*wm1 as=lm1*wm1 pd=2*(lm1+wm1) ps=2*(lm1+wm1) 

m2 3 14 0 0 nfet l=lm1 w=wm1 ad=lm1*wm1 as=lm1*wm1 pd=2*(lm1+wm1) ps=2*(lm1+wm1)
   
m3 6 4 2 0 nfet l=lm2 w=wm2 ad=lm2*wm2 as=lm2*wm2 pd=2*(lm2+wm2) ps=2*(lm2+wm2)  

m4 5 4 3 0 nfet l=lm2 w=wm2 ad=lm2*wm2 as=lm2*wm2 pd=2*(lm2+wm2) ps=2*(lm2+wm2)

m5 9 8 6 0 nfet l=lm3 w=wm3 ad=lm3*wm3 as=lm3*wm3 pd=2*(lm3+wm3) ps=2*(lm3+wm3)
  
m6 8 9 5 0 nfet l=lm3 w=wm3 ad=lm3*wm3 as=lm3*wm3 pd=2*(lm3+wm3) ps=2*(lm3+wm3)  

m7 6 4 7 7 pfet l=lm4 w=wm4 ad=lm4*wm4 as=lm4*wm4 pd=2*(lm4+wm4) ps=2*(lm4+wm4)
  
m8 9 4 7 7 pfet l=lm5 w=wm5 ad=lm5*wm5 as=lm5*wm5 pd=2*(lm5+wm5) ps=2*(lm5+wm5)
  
m9 9 8 7 7 pfet l=lm5 w=wm5 ad=lm5*wm5 as=lm5*wm5 pd=2*(lm5+wm5) ps=2*(lm5+wm5)
  
m10 8 9 7 7 pfet l=lm5 w=wm5 ad=lm5*wm5 as=lm5*wm5 pd=2*(lm5+wm5) ps=2*(lm5+wm5)
  
m11 8 4 7 7 pfet l=lm5 w=wm5 ad=lm5*wm5 as=lm5*wm5 pd=2*(lm5+wm5) ps=2*(lm5+wm5)
  
m12 5 4 7 7 pfet l=lm4 w=wm4 ad=lm4*wm4 as=lm4*wm4 pd=2*(lm4+wm4) ps=2*(lm4+wm4)  
********************Pre-Amplifier****

*************LATCH******************************
m13 10 9 0 0 nfet l=lm6 w=wm6 ad=lm6*wm6 as=lm6*wm6 pd=2*(lm6+wm6) ps=2*(lm6+wm6) 

m14 11 8 0 0 nfet l=lm6 w=wm6 ad=lm6*wm6 as=lm6*wm6 pd=2*(lm6+wm6) ps=2*(lm6+wm6) 

m15 12 13 10 0 nfet l=lm7 w=wm7 ad=lm7*wm7 as=lm7*wm7 pd=2*(lm7+wm7) ps=2*(lm7+wm7) 

m16 13 12 11 0 nfet l=lm7 w=wm7 ad=lm7*wm7 as=lm7*wm7 pd=2*(lm7+wm7) ps=2*(lm7+wm7) 

m17 12 9 7 7 pfet l=lm8 w=wm8 ad=lm8*wm8 as=lm8*wm8 pd=2*(lm8+wm8) ps=2*(lm8+wm8) 

m18 12 13 7 7 pfet l=lm8 w=wm8 ad=lm8*wm8 as=lm8*wm8 pd=2*(lm8+wm8) ps=2*(lm8+wm8)

m19 13 12 7 7 pfet l=lm8 w=wm8 ad=lm8*wm8 as=lm8*wm8 pd=2*(lm8+wm8) ps=2*(lm8+wm8) 

m20 13 8 7 7 pfet l=lm8 w=wm8 ad=lm8*wm8 as=lm8*wm8 pd=2*(lm8+wm8) ps=2*(lm8+wm8)
**************************LATCH**********************
cxxx 13 0 0.5p
cyyy 12 0 0.5p

.PARAM AREA='wm1*lm1 + wm1*lm1 + wm2*lm2 + wm2*lm2 + wm3*lm3 + wm3*lm3 + wm4*lm4 + wm5*lm5 + wm5*lm5 + wm5*lm5 + wm5*lm5 + wm4*lm4 + wm6*lm6 + wm6*lm6 + wm7*lm7 + wm7*lm7 + wm8*lm8 + wm8*lm8 + wm8*lm8 + wm8*lm8'
Vdd 7 0 DC 1.2
.param Vref=0.6
Vreff 14 GND Vref
Vin 1 GND PWL(0 0.58 100n 0.62V)
Vclk 4 0 PULSE(0 1.2V 0 0.1p 0.1p 2ns 4ns)

.option post
.option probe

.option OPFILE=1
.TRAN 0n 100n
.OP 
.probe V(8) V(9) V(1) V(14) V(4) V(7) V(12) V(13)
.meas tran avgpower AVG power 
.MEAS RSAREA avg PAR(AREA)
.MEAS TRAN zzztemp FIND v(1) WHEN v(12)=0.6V rise=1
.MEAS TRAN offset max par('abs(zzztemp-Vref)')
.MEASURE TRAN tdlay TRIG V(12) VAL =0.1 TD =10n rise=1
+ TARG V(12) VAL =1.1        rise=1
.END