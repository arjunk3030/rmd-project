/* Single STEP/DIR motor driver. One motor mechanically synchronizes both wings.
   Example: 200-step motor, driver physically configured for1/16 microstep.
   Verify driver current, motor torque, pinout and zero pose before powered use.
   Serial 'g' starts a slow ramp; 's' stops pulses and keeps holding torque.
   No homing or stall sensing. Hand-crank a complete cycle first.
*/
const int STEP=2, DIR=4, ENABLE_N=8;
const unsigned long STEPS_PER_CYCLE=200UL*16UL;
const float CYCLE_SECONDS=4.0f;
bool running=false,high=false;
unsigned long edgeAt=0,startedAt=0;
void setup(){
 pinMode(STEP,OUTPUT);pinMode(DIR,OUTPUT);pinMode(ENABLE_N,OUTPUT);
 digitalWrite(DIR,LOW);digitalWrite(ENABLE_N,HIGH);Serial.begin(115200);
}
void loop(){
 if(Serial.available()){
  char c=Serial.read();
  if(c=='g'){running=true;startedAt=millis();edgeAt=micros();digitalWrite(ENABLE_N,LOW);}
  if(c=='s'){running=false;digitalWrite(STEP,LOW);high=false;}
 }
 if(!running)return;
 float ramp=min(1.0f,0.1f+(millis()-startedAt)/5000.0f);
 unsigned long halfPeriod=(unsigned long)(500000.0f*CYCLE_SECONDS/STEPS_PER_CYCLE/ramp);
 unsigned long now=micros();
 if((unsigned long)(now-edgeAt)>=halfPeriod){edgeAt=now;high=!high;digitalWrite(STEP,high);}
}
