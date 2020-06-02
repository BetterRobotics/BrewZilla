
#define RXD_BUFF_SIZE    6
#define LOCAL_BUFF_SIZE  2
#define COM_LOST_TIMEOUT 30 // seconds. 

#define brn1_pin 2
#define brn2_pin 3
#define bzr_pin  4
#define pmp_pin  5
#define tmp_pin  A0

char input_data[] = {'i','i','i','i'};
int data_count = 0;
bool RXD_avali_flag = false, rx_lock = false;

int brn1=0, brn2=0, bzr=0, tmp=0, tmp_set=0, pmp=0;

double pid_timer=0, rx_timer=0, tx_timer=0, diff=0;

float integral=0., last_error=0.;
float kp=3.,ki=5.,kd=0.;


int pid(int setp, int input, int kp, int ki, int kd){
    float dt = (millis() - pid_timer)/1000.;
    pid_timer = millis();
    float error = setp - input;
    Serial.println(dt);
    integral += error;
    if(integral > 255.){integral=255.;}
    else if(integral < 0.){integral=0.;}
    float derivative = error - last_error;
    error = kp*error + (ki*dt)*integral + (kd/dt)*derivative;
    if(error<0){error=0;}
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

void decode_data(void){
  if(RXD_avali_flag){
    RXD_avali_flag = 0;
    if(input_data[1]=='h' && input_data[2]=='b' && input_data[3]=='t'){
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

void set_power(void){
  float output = 0.;
  if(tmp_set>0){
    output = pid(tmp_set, tmp, kp,ki,kd);
  }
  Serial.print("PID output: ");
  Serial.print(output);
  Serial.print("\ttmp_set: ");
  Serial.print(tmp_set);
  Serial.print("\ttmp: ");
  Serial.println(tmp);
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
  tmp = analogRead(tmp_pin);
}

void send_data(void){
  Serial.print("z,");
  Serial.print(tmp);
  Serial.println(",y");
}

void setup(void){

  Serial.begin(9600);
  pinMode(tmp_pin, INPUT);
  pinMode(brn1_pin, OUTPUT);
  pinMode(brn2_pin, OUTPUT);
  pinMode(bzr_pin, OUTPUT);
  pinMode(pmp_pin, OUTPUT);
  
  digitalWrite(pmp_pin, LOW);
  digitalWrite(brn1_pin, LOW);
  digitalWrite(brn2_pin, LOW);
  digitalWrite(bzr_pin, HIGH);
  delay(200);
  digitalWrite(bzr_pin, LOW);
  
  
}

void loop(void){
    get_serial();
    decode_data();
    set_pins();
    get_temp();
    
    if (millis()> tx_timer + 200){
        send_data();
        set_power();
        tx_timer = millis();
    }
    
    delay(20);
}



