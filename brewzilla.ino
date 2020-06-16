#define RXD_BUFF_SIZE    6
#define LOCAL_BUFF_SIZE  2
#define COM_LOST_TIMEOUT 5 // seconds.

#define brn1_pin 4
#define brn2_pin 3
#define bzr_pin  A2
#define pmp_pin  A6
#define tmp_pin  A0

#define step 100

#include "chords.h"


char input_data[] = {'i','i','i','i'};
int data_count = 0;
bool RXD_avali_flag = false, rx_lock = false, chord_flag=false;

int brn1=0, brn2=0, bzr=0, a_tmp=0, tmp=0, tmp_set=0, pmp=0;

double pid_timer=0, rx_timer=0, tx_timer=0, diff=0, bzr_timer=0;
float integral=0., last_error=0.;
float kp=12.,ki=6.,kd=4.;


int pid(int setp, int input, int kp, int ki, int kd){
    float dt = (millis() - pid_timer)/1000.;
    pid_timer = millis();
    float error = setp - input;
    integral += error;
    if(integral > 255.){integral=255.;}
    else if(integral <=0.){integral=0.;}
    float derivative = error - last_error;
    error = kp*error + (ki*dt)*integral + (kd/dt)*derivative;
    if(error<=0){error=0, integral=0;}
    if(error>255){error=255;}
    return error;
}

bool hbt_ok(void){
  diff = millis()/1000 - rx_timer;
  if(diff > COM_LOST_TIMEOUT){
    return false;
  }
  return true;
}

void get_serial(void){
  if(Serial.available() > 0){
    char ReceivedByte;
    ReceivedByte = Serial.read(); // Fetch the received byte value into the variable "ByteReceived"
    //Serial.print(ReceivedByte); // Echo the received byte back to the computer
    if( ReceivedByte == 'x' ){
      data_count = 0;
      rx_lock = true;
    }else if( ReceivedByte == 'y' && rx_lock ){
        if(data_count >= 2){
          RXD_avali_flag = true;
          data_count = 0;
          rx_lock = false;
        }else{
          data_count = 0;
          rx_lock = false;
        }
    }else if (data_count >= RXD_BUFF_SIZE + 1 ){
      rx_lock = true;
      data_count = 0;
    }
    input_data[data_count] = ReceivedByte;
    data_count++;
  }
}


void set_power(void){
  float output = 0;
  if(tmp_set>0){
    output = pid(tmp_set, tmp, kp,ki,kd);
  }
  if(output > 190){
    digitalWrite(brn1_pin, HIGH);
    digitalWrite(brn2_pin, HIGH);
  }else if(output > 50){
    digitalWrite(brn1_pin, HIGH);
    digitalWrite(brn2_pin, LOW);
  }else if(output > 0){
    digitalWrite(brn1_pin, LOW);
    digitalWrite(brn2_pin, HIGH);
  }else{
    digitalWrite(brn1_pin, LOW);
    digitalWrite(brn2_pin, LOW);
  }
}


void set_pins(void){
  digitalWrite(pmp_pin, pmp);
  digitalWrite(bzr_pin, bzr);
}

void get_temp(void){
  
  //int count = 1;
  /*
  while(count < 10){
     a_tmp += analogRead(tmp_pin);
     delay(5);
     count++;
  }
  */
  a_tmp = analogRead(tmp_pin);
  tmp = map(a_tmp, 353,900, 47, 99);
}

void send_data(void){
  Serial.print("z,");
  Serial.print(tmp);
  Serial.print(",");
  Serial.print(a_tmp);
  Serial.println(",y");
}

void play_tune(int index){


    if(index == 1){
        for (int thisNote = 0; thisNote < (sizeof(starwars_tempo)/2); thisNote++) {
            int noteDuration = 1000 / starwars_tempo[thisNote];
            tone(bzr_pin, starwars[thisNote], noteDuration);
            int pauseBetweenNotes = noteDuration * 1.30;
            delay(pauseBetweenNotes);
            noTone(bzr_pin);
        }

    }else if(index == 2){

        for (int thisNote = 0; thisNote < (sizeof(mario_tempo)/2); thisNote++) {
            int noteDuration = 1000 / mario_tempo[thisNote];
            tone(bzr_pin, mario[thisNote], noteDuration);
            int pauseBetweenNotes = noteDuration * 1.30;
            delay(pauseBetweenNotes);
            noTone(bzr_pin);
        }

    }else if(index==3){

        for (int thisNote = 0; thisNote < (sizeof(underworld_tempo)/2); thisNote++) {
            int noteDuration = 1000 / underworld_tempo[thisNote];
            tone(bzr_pin, underworld[thisNote], noteDuration);
            int pauseBetweenNotes = noteDuration * 1.30;
            delay(pauseBetweenNotes);
            noTone(bzr_pin);
        }
    }else if(index==4){

        for (int thisNote = 0; thisNote < (sizeof(alarm_1_tempo)/2); thisNote++) {
            int noteDuration = 1000 / alarm_1_tempo[thisNote];
            tone(bzr_pin, alarm_1[thisNote], noteDuration);
            int pauseBetweenNotes = noteDuration * 0.40;
            delay(pauseBetweenNotes);
            noTone(bzr_pin);
        }
    }else if(index==5){

        for (int thisNote = 0; thisNote < (sizeof(alarm_2_tempo)/2); thisNote++) {
            int noteDuration = 1000 / alarm_2_tempo[thisNote];
            tone(bzr_pin, alarm_2[thisNote], noteDuration);
            int pauseBetweenNotes = noteDuration * 1.10;
            delay(pauseBetweenNotes);
            noTone(bzr_pin);
        }
    }else if(index==6){

        for (int thisNote = 0; thisNote < (sizeof(alarm_3_tempo)/2); thisNote++) {
            int noteDuration = 1000 / alarm_3_tempo[thisNote];
            tone(bzr_pin, alarm_3[thisNote], noteDuration);
            int pauseBetweenNotes = noteDuration * 1.10;
            delay(pauseBetweenNotes);
            noTone(bzr_pin);
        }
    }

}

void buzzer(void){

    if(bzr > 0){
      play_tune(bzr);
      bzr = 0;
    }
}

void decode_data(void){
  if(RXD_avali_flag){
    RXD_avali_flag = 0;
    if(input_data[1]=='h' && input_data[2]=='b' && input_data[3]=='t'){
      if(!chord_flag){play_tune(1);chord_flag=true;}
      rx_timer = millis()/1000.0;
    }else if (hbt_ok()){
      tmp_set = input_data[1];
      bzr = input_data[2];
    }else{
      brn1 = 0;
      brn2 = 0;
      bzr =  0;
      pmp =  0;
      tmp_set=0;
    }
  }else if (!hbt_ok()){
     brn1 = 0;
     brn2 = 0;
     bzr =  0;
     pmp =  0;
     tmp_set=0;
  }
}

void setup(void){

  Serial.begin(9600);
  pinMode(tmp_pin, INPUT_PULLUP);
  pinMode(brn1_pin, OUTPUT);
  pinMode(brn2_pin, OUTPUT);
  pinMode(bzr_pin, OUTPUT);
  pinMode(pmp_pin, OUTPUT);

  digitalWrite(tmp_pin, LOW);
  digitalWrite(pmp_pin, LOW);
  digitalWrite(brn1_pin, LOW);
  digitalWrite(brn2_pin, LOW);


}

void loop(void){

    get_serial();
    decode_data();
    get_temp();
    buzzer();
    set_pins();
    set_power();

    if (millis()> tx_timer + 200){
        send_data();
        
        tx_timer = millis();
    }

    //delay(20);
}
