import RPi.GPIO as GPIO
import time

servoPIN = 17
GPIO.setmode(GPIO.BCM)
GPIO.setup(servoPIN, GPIO.OUT)

print("Please type your age.")
age = input()
print("Please select your biological sex. Type \'M\' for male and \'F\' for female.\n If you would prefer to skip, please type \'S\'.")
sex = input()

FHeartRates = [72, 73, 74, 75, 73, 73]
MHeartRates = [68, 68, 69, 70, 69, 68]
AvgHeartRates = [70, 71, 70, 73, 71, 71]
targetHeartRate = 0

# currentTime;
# long startTime;

# forward = true;

# match age:
#   case 
#   # case 1...25: 
  #   ageRange = 0
  #   break
  # case 26 ... 35:
  #   ageRange = 1
  #   break
  # case 36 ... 45:
  #   ageRange = 2
  #   break
  # case 46 ... 55: 
  #   ageRange = 3
  #   break
  # case 56 ... 65: 
  #   ageRange = 4
  #   break
  # case 66 ... 100: 
  #   ageRange = 5
  #   break



p = GPIO.PWM(servoPIN, 50) # GPIO 17 for PWM with 50Hz
p.start(2.5) # Initialization
try:
  while True:
    p.ChangeDutyCycle(5)
    time.sleep(0.5)
    p.ChangeDutyCycle(7.5)
    time.sleep(0.5)
    p.ChangeDutyCycle(10)
    time.sleep(0.5)
    p.ChangeDutyCycle(12.5)
    time.sleep(0.5)
    p.ChangeDutyCycle(10)
    time.sleep(0.5)
    p.ChangeDutyCycle(7.5)
    time.sleep(0.5)
    p.ChangeDutyCycle(5)
    time.sleep(0.5)
    p.ChangeDutyCycle(2.5)
    time.sleep(0.5)
except KeyboardInterrupt:
  p.stop()
  GPIO.cleanup()
