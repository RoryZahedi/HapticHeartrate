  #include <Servo.h>
  #include <Wire.h>
  #include "MAX30105.h"

  #include "heartRate.h"

  MAX30105 particleSensor;

  const byte RATE_SIZE = 4; //Increase this for more averaging. 4 is good.
  byte rates[RATE_SIZE]; //Array of heart rates
  byte rateSpot = 0;
  long lastBeat = 0; //Time at which the last beat occurred

  float beatsPerMinute;
  int beatAvg;

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

  long currentTime;
  long startTime;

  bool forward = true;


  void setup() {
    // put your setup code here, to run once:
      Serial.begin(115200); 
        // Initialize sensor
      if (!particleSensor.begin(Wire, I2C_SPEED_FAST)) //Use default I2C port, 400kHz speed
      {
        Serial.println("MAX30105 was not found. Please check wiring/power. ");
        while (1);
      }
      Serial.println("Place your index finger on the sensor with steady pressure.");

      particleSensor.setup(); //Configure sensor with default settings
      particleSensor.setPulseAmplitudeRed(0x0A); //Turn Red LED to low to indicate sensor is running
      particleSensor.setPulseAmplitudeGreen(0); //Turn off Green LED

      delay(2000);  
  
      Serial.println("Type your age please.");

      servo.attach(8);
      servo.write(angle);

      startTime = millis();
      currentTime = millis();
  }


  void loop() {
    // put your main code here, to run repeatedly:
    if(Serial.available()){
          input = Serial.readString();
          if(input){
            input.toUpperCase();
          }
          if(input[0] == 'K'){
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

    if (age != 0 && sex != "N" && targetHeartRate != 0) {
      long irValue = particleSensor.getIR();
      Serial.print("IR Value: ");
      Serial.println(irValue);
      if (checkForBeat(irValue) == true)
      {
        //We sensed a beat!
        long delta = millis() - lastBeat;
        lastBeat = millis();
        beatsPerMinute = 60 / (delta / 1000.0);
        // Serial.print("BPM: ");
        // Serial.println(beatsPerMinute);
        if (beatsPerMinute < 255 && beatsPerMinute > 20) //its in normal range
        {
          rates[rateSpot++] = (byte)beatsPerMinute; //Store this reading in the array
          rateSpot %= RATE_SIZE;

          //Take average of readings
          beatAvg = 0;
          for (byte x = 0 ; x < RATE_SIZE ; x++)
            beatAvg += rates[x];
          beatAvg /= RATE_SIZE;
        }
      }
      if (irValue < 50000)
        Serial.println("No finger?");
        
      Serial.print("beatAvg: ");
      Serial.println(beatAvg);
    }


    if(targetHeartRate > 0){ 
        delayTime = (targetHeartRate*1000)/60;
        // scan from 0 to 180 degrees
        currentTime = millis();
        if (currentTime - startTime >= delayTime) {
          if (forward) {
            for(angle = 10; angle < 180; angle++)  
            {                                  
              servo.write(angle);               
              delay(1);                   
            } 
            forward = false;
          } else {
            // now scan back from 180 to 0 degrees
            for(angle = 180; angle > 10; angle--)    
            {                                
              servo.write(angle);           
              delay(1);       
            }
            forward = true;
          }
          startTime = millis();
        }
      }

  }
