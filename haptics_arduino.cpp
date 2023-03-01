#include <Servo.h>
Servo servo;
int angle = 10;
float delayTime = 15;

String input;
int age = 0;
String sex = "N";
int FHeartRates [6] = {72, 73, 74, 75, 73, 73};
int MHeartRates [6] = {68, 68, 69, 70, 69, 68};
int AvgHeartRates[6] = {70, 71, 70, 73, 71, 71};
float targetHeartRate = 0;


void setup() {
  // put your setup code here, to run once:
    Serial.begin(9600); 
    delay(2000);  
 
    Serial.println("Type your age please.");

    servo.attach(8);
    servo.write(angle);
}


void loop() {
  // put your main code here, to run repeatedly:
  if(Serial.available()){
        input = Serial.readString();
        if(input){
          input.toUpperCase();
        }
        if(input[0] == 'K'){
          println("here");
          targetHeartRate = -1;
        }
        Serial.print("You typed: " );
        Serial.println(input);
        if (age == 0) {
          age = input.toInt();
          Serial.println("Select your biological sex please. Type \'M\' for male and \'F\' for female.\n If you would prefer to skip, please type \'S\'.");
        } else {
          if (sex == "N") {
            sex = input;
          }
        }
  }

  if (age != 0 && sex != "N" && targetHeartRate == 0) {
    //calculate from lookup table
    int ageRange;
    switch (age){ 
      case 1 ... 25: 
        ageRange = 0;
        break;
      case 26 ... 35:
        ageRange = 1;
        break;
      case 36 ... 45:
        ageRange = 2;
        break;
      case 46 ... 55: 
        ageRange = 3;
        break;
      case 56 ... 65: 
        ageRange = 4;
        break;
      case 66 ... 100: 
        ageRange = 5;
        break;  
    }

    if (sex[0] == 'F') {
      targetHeartRate = FHeartRates[ageRange];
    } else if (sex[0] == 'M') {
      targetHeartRate = MHeartRates[ageRange];
    } else {
      targetHeartRate = AvgHeartRates[ageRange];
    }
    Serial.println(targetHeartRate);
  }

  if(targetHeartRate > 0){ 
      Serial.print("targetheartrate is ");
      Serial.println(targetHeartRate);
      delayTime = (targetHeartRate*1000)/60;
      Serial.print("Delay time is ");
      Serial.println(delayTime);
      // scan from 0 to 180 degrees
      for(angle = 10; angle < 180; angle++)  
      {                                  
        servo.write(angle);               
        delay(1);                   
      } 
      delay(delayTime);
      // now scan back from 180 to 0 degrees
      for(angle = 180; angle > 10; angle--)    
      {                                
        servo.write(angle);           
        delay(1);       
      }
      delay(delayTime); 
    }

}
