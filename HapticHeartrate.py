#!/usr/bin/env python
import sys, serial, argparse, csv, datetime
from dateutil import parser as dateparser
import time
import RPi.GPIO as GPIO
import time
from _thread import *


class LiveDataPoint(object):
    def __init__(self, time, data): 
        if [d & 0x80 != 0 for d in data] != [True, False, False, False, False]:
           raise ValueError("Invalid data packet.")

        self.time = time

        # 1st byte
        self.signalStrength = data[0] & 0x0f
        self.fingerOut = bool(data[0] & 0x10)
        self.droppingSpO2 = bool(data[0] & 0x20)
        self.beep = bool(data[0] & 0x40)

        # 2nd byte
        self.pulseWaveform = data[1]

        # 3rd byte
        self.barGraph = data[2] & 0x0f
        self.probeError = bool(data[2] & 0x10)
        self.searching = bool(data[2] & 0x20)
        self.pulseRate = (data[2] & 0x40) << 1

        # 4th byte
        self.pulseRate |= data[3] & 0x7f

        # 5th byte
        self.bloodSpO2 = data[4] & 0x7f

    def getBytes(self):
        result = [0]*5

        # 1st byte
        result[0] = self.signalStrength & 0x0f
        if self.fingerOut:
            result[0] |= 0x10
        if self.droppingSpO2:
            result[0] |= 0x20
        if self.beep:
            result[0] |= 0x40
        result[0] |= 0x80 # sync bit

        # 2nd byte
        result[1] = self.pulseWaveform & 0x7f

        # 3rd byte
        result[2] = self.barGraph & 0x0f
        if self.probeError:
            result[2] |= 0x10
        if self.searching:
            result[2] |= 0x20
        result[2] |= (self.pulseRate & 0x80) >> 1

        # 4th byte
        result[3] = self.pulseRate & 0x7f

        # 5th byte
        result[4] = self.bloodSpO2 & 0x7f

        return result

    def __repr__(self):
        hexBytes = ['0x{0:02X}'.format(byte) for byte in self.getBytes()]
        return "LiveDataPoint({0}, [{1}])".format(self.time.__repr__(), ', '.join(hexBytes))

    def __str__(self):
        return ", ".join(["Time = {0}",
                          "Signal Strength = {1}",
                          "Finger Out = {2}",
                          "Dropping SpO2 = {3}",
                          "Beep = {4}",
                          "Pulse waveform = {5}",
                          "Bar Graph = {6}",
                          "Probe Error = {7}",
                          "Searching = {8}",
                          "Pulse Rate = {9} bpm",
                          "SpO2 = {10}%"]).format(self.time,
                                                  self.signalStrength,
                                                  self.fingerOut,
                                                  self.droppingSpO2,
                                                  self.beep,
                                                  self.pulseWaveform,
                                                  self.barGraph,
                                                  self.probeError,
                                                  self.searching,
                                                  self.pulseRate,
                                                  self.bloodSpO2)

    @staticmethod
    def getCsvColumns():
        return ["Time", "PulseRate", "SpO2", "PulseWaveform", "BarGraph", 
                "SignalStrength", "Beep", "FingerOut", "Searching",
                "DroppingSpO2", "ProbeError"]

    def getCsvData(self):
        return [self.time, self.pulseRate, self.bloodSpO2, self.pulseWaveform,
                self.barGraph, self.signalStrength, self.beep,
                self.fingerOut, self.searching, self.droppingSpO2,
                self.probeError]

    def getDictData(self):
        ret = dict()
        for n, d in zip(self.getCsvColumns(), self.getCsvData()):
            ret[n] = d
        return ret

class RecordedDataPoint(object):
    def __init__(self, time, data):
        if data[0] & 0xfe != 0xf0 or data[1] & 0x80 == 0 or data[2] & 0x80 != 0:
           print(data)
           raise ValueError("Invalid data packet.")

        self.time = time

        # 1st byte
        #bpm
        self.pulseRate = (data[0] & 0x01) << 7

        # 2nd byte
        #bpm
        self.pulseRate |= data[1] & 0x7f

        # 3rd byte
        self.bloodSpO2 = data[2] & 0x7f

    def getBytes(self):
        result = [0]*3

        # 1st byte
        result[0] = (self.pulseRate & 0x80) >> 7
        result[0] |= 0xf0 # sync bits

        # 2nd byte
        result[1] = self.pulseRate & 0x7f
        result[1] |= 0x80

        # 3rd byte
        result[2] = self.bloodSpO2 & 0x7f

        return result

    def __repr__(self):
        hexBytes = ['0x{0:02X}'.format(byte) for byte in self.getBytes()]
        return "RecordedDataPoint({0}, [{1}])".format(self.time.__repr__(), ', '.join(hexBytes))

    def __str__(self):
        return ", ".join(["Time = {0}",
                          "Pulse Rate = {1} bpm",
                          "SpO2 = {2}%"]).format(self.time,
                                                 self.pulseRate,
                                                 self.bloodSpO2)

    @staticmethod
    def getCsvColumns():
        return ["Time", "PulseRate", "SpO2"]

    def getCsvData(self):
        return [self.time, self.pulseRate, self.bloodSpO2]

class CMS50Dplus(object):
    def __init__(self, port):
        self.port = port
        self.conn = None

    def isConnected(self):
        return type(self.conn) is serial.Serial and self.conn.isOpen()

    def connect(self):
        if self.conn is None:
            self.conn = serial.Serial(port = self.port,
                                      baudrate = 19200,
                                      parity = serial.PARITY_ODD,
                                      stopbits = serial.STOPBITS_ONE,
                                      bytesize = serial.EIGHTBITS,
                                      timeout = 5,
                                      xonxoff = 1)
        elif not self.isConnected():
            self.conn.open()

    def disconnect(self):
        if self.isConnected():
            self.conn.close()

    def getByte(self):
        char = self.conn.read()
        if len(char) == 0:
            return None
        else:
            return ord(char)
    
    def sendBytes(self, values):
        return self.conn.write(''.join([chr(value & 0xff) for value in values]))

    # Waits until the specified byte is seen or a timeout occurs
    def expectByte(self, value):
        while True:
            byte = self.getByte()
            if byte is None:
                return False
            elif byte == value:
                return True

    def getLiveData(self):
        try:
            self.connect()
            packet = [0]*5
            idx = 0
            while True:
                byte = self.getByte()
            
                if byte is None:
                    break

                if byte & 0x80:
                    if idx == 5 and packet[0] & 0x80:
                        yield LiveDataPoint(datetime.datetime.utcnow(), packet)
                    packet = [0]*5
                    idx = 0
            
                if idx < 5:
                    packet[idx] = byte
                    idx+=1
        except:
            self.disconnect()

    def getRecordedData(self, time):
        try:
            # Connect and check that we get some data.
            self.connect()
            for i in range(10):
                if self.getByte() is None:
                    raise Exception("No data stream from device!")

            self.conn.flushInput()
            self.sendBytes([0xf5, 0xf5])
            self.conn.flush()

            # Wait for preamble.
            for x in range(3):
                if (not (self.expectByte(0xf2) and 
                         self.expectByte(0x80) and 
                         self.expectByte(0x00))):
                    raise Exception("No preamble in device response!")

            # Wait for content length.
            lena = self.getByte()
            lenb = self.getByte()
            lenc = self.getByte()

            if ((lena & 0x80) == 0 or (lenb & 0x80) == 0 or (lenc & 0x80) != 0):
                raise Exception("Corrupted length in header!")

            length = (((lena & 0x7f) << 14) | ((lenb & 0x7f) << 7) | lenc) + 1

            if length % 3 != 0:
                raise Exception("Length not divisible by 3!")

            # Calculate length in hours, minutes, and seconds.
            s = length / 3
            
            h = int(s / 3600)
            s -= h * 3600

            m = int(s / 60)
            s -= m * 60

            print("Number of measurements: {0} ({1}h{2}m{3}s)".format(length / 3, h, m, s))

            # Content...
            packet = [0]*3
            for i in range(length):
                byte = self.getByte()
                if byte is None:
                    raise Exception("Timeout during download!")
                packet[i%3] = byte
                if i%3 == 2:
                    yield RecordedDataPoint(time, packet)
                    time = time + datetime.timedelta(seconds=1)
                    packet = [0]*3

        finally:
            self.sendBytes([0xf6, 0xf6, 0xf6])
            self.disconnect()

def dumpLiveData(port):
    global liveBPM, gotBPM, servoHeartRate
    oximeter = CMS50Dplus(port)
    measurements = 0
    for liveData in oximeter.getLiveData():
        # print(" bpm is ", liveData.pulseRate)
        liveBPM = liveData.pulseRate
        if not gotBPM and liveBPM != 0:
            gotBPM = True
            servoHeartRate = liveBPM
        measurements += 1

   
def getLiveData(port, framerate=None):
    oximeter = CMS50Dplus(port)
    for liveData in oximeter.getLiveData():
        if framerate is not None:
            time.sleep(1.0/framerate)
        yield liveData.getDictData()
        # yield liveData.pulseRate


def dumpRecordedData(starttime, port, filename):
    print("Saving recorded data...")
    print("Please wait as the latest session is downloaded...")
    oximeter = CMS50Dplus(port)
    measurements = 0
    with open(filename, 'w') as csvfile:
        writer = csv.writer(csvfile, quoting=csv.QUOTE_NONNUMERIC)
        writer.writerow(RecordedDataPoint.getCsvColumns())
        for recordedData in oximeter.getRecordedData(starttime):
            writer.writerow(recordedData.getCsvData())
            measurements += 1
            sys.stdout.write("\rGot {0} measurements...".format(measurements))
            sys.stdout.flush()        

def valid_datetime(s):
    try:
        return dateparser.parse(s)
    except ValueError:
        msg = "Not a valid date: '{0}'.".format(s)
        raise argparse.ArgumentTypeError(msg)

def recordHowLong():
    global howLongTimer,targetHeartRate,liveBPM
    howLongTimer = 0
    print(liveBPM,targetHeartRate)
    while liveBPM > targetHeartRate or liveBPM <= 0:
        time.sleep(1)
        howLongTimer += 1
    print("Took ",howLongTimer, "s to acheive target heart rate of",targetHeartRate)
    writeToFile(["Achieved target heart rate in:"  + str(howLongTimer)+ "s"])
    recordHowLongMaintain()
    
def recordHowLongMaintain():
    global liveBPM, targetHeartRate,maintainTimer
    maintainTimer = 0
    while liveBPM <= targetHeartRate:
        time.sleep(1)
        maintainTimer += 1
    print("Was able to maintain equal or below BPM of",targetHeartRate,"for", maintainTimer, "seconds")
    writeToFile(["Maintained for: " +str(maintainTimer) + "s"])
    maintainTimer = 0
    recordHowLong()

def setup():
    global control
    FHeartRates = [72, 73, 74, 75, 73, 73]
    MHeartRates = [68, 68, 69, 70, 69, 68]
    AvgHeartRates = [70, 71, 70, 73, 71, 71]
    targetHeartRate = 0

    control1 = input("Control? Y or N").upper()
    if control1 == "Y":
        control = True
    
    print("Please type your age.")
    age = int(input())
    print("Please select your biological sex. Type \'M\' for male and \'F\' for female.\n If you would prefer to skip, please type \'S\'.")
    sex = input().upper()
    name = input("Please enter your name or N/A")
    writeToFile([name,age,sex,"contorl = "+ str(control)])
    
    if age < 26:
        ageRange = 0
    elif age >= 26 and age < 36:
        ageRange = 1
    elif age >= 36 and age < 46:
        ageRange = 2
    elif age >= 46 and age < 56:
        ageRange = 3
    elif age >= 56 and age < 66:
        ageRange = 4
    else:
        ageRange = 5

    if sex == 'F':
        targetHeartRate = FHeartRates[ageRange]
    elif sex == 'M':
        targetHeartRate = MHeartRates[ageRange]
    else:
        targetHeartRate = AvgHeartRates[ageRange]
    print("Your target heartrate is",targetHeartRate)
    return targetHeartRate


def moveServo():
    global servo, forward
    servo.start(2.5) # Initialization
    if forward:
        servo.ChangeDutyCycle(12)
    else:
        servo.ChangeDutyCycle(2)
    
def changeServoHeartRate():
    global gotBPM, servoHeartRate, liveBPM, targetHeartRate
    if liveBPM > 50 and liveBPM <= servoHeartRate:
            if liveBPM < servoHeartRate-1:
                servoHeartRate = liveBPM -1
            else:
                servoHeartRate -= 1
    print("servoHeartRate: ", servoHeartRate)

def updateServoHeartRate():
    timer = 10
    while True:
        while timer:
            time.sleep(1)
            timer-=1
        changeServoHeartRate()
        timer = 10
    

def moveServoTimer():
    global servoHeartRate,forward, liveBPM, gotBPM
    while True:
        timer = float(60/servoHeartRate)
        while timer > 0:
            time.sleep(.1)
            timer-=.1
        moveServo() #move the servo
        forward = not forward #reset the direction of forward
        
        #recalculate the servoHeartRate is managed in another async function

# def terminalIO():
#     while True:
def recordMinAndMax():
    global liveBPM,minBPM,maxBPM,initalBPM
    while liveBPM <= 0:
        time.sleep(.1)
    initalBPM = liveBPM
    writeToFile(["InitalBPM: " +str(initalBPM)])
    minBPM = liveBPM
    maxBPM = liveBPM
    while True:
        if liveBPM < minBPM:
            minBPM = liveBPM
            writeToFile(["MinBPM: " +str(minBPM)])
        if liveBPM > maxBPM:
            maxBPM = liveBPM
            writeToFile(["MaxBPM: " +str(maxBPM)])
            
def dumpData():
    global args
    while (1):
        dumpLiveData(args.serialport)

def writeToFile(info):
    with open(CSV_NAME, 'a') as file:
        writer = csv.writer(file)
        writer.writerow(info)


if __name__ == "__main__":
    CSV_NAME = "hapticHeartRateUser" + datetime.datetime.utcnow().strftime("%d-%m-%Y_%H:%M:%S")
    
    forward = 1 #for how we move the arduino
    servoPIN = 17
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(servoPIN, GPIO.OUT)
    servo = GPIO.PWM(servoPIN, 50) # GPIO 17 for PWM with 50Hz

    parser = argparse.ArgumentParser(description="cms50dplus.py v1.2 - Contec CMS50D+ Data Downloader (c) 2015 atbrask")
    parser.add_argument("serialport", help="The device's virtual serial port.")
    parser.add_argument('-s', "--starttime", help="The start time for RECORDED mode data.", type=valid_datetime)
    howLongTimer = 0
    args = parser.parse_args()
    control = False
    maintainTimer = 0
    targetHeartRate = setup()
    servoHeartRate = targetHeartRate
    initalBPM = 0
    liveBPM = 0
    maxBPM = 0
    minBPM = float('inf')
    gotBPM = False
    if not control:
        start_new_thread(updateServoHeartRate, ())
        start_new_thread(moveServoTimer, ())
    start_new_thread(dumpData,())
    start_new_thread(recordHowLong,())
    start_new_thread(recordMinAndMax,())
    while True:
        i = input()
        if i == "q":
            if maintainTimer > 0:
                writeToFile(["Maintained for: " +str(maintainTimer) + "s"])

            quit()
    
   

   
 
   

    