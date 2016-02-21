import RPi.GPIO as GPIO, time, os
import urllib2, json
import datetime
from threading import Thread
import threading
import nxppy
import copy
import math

GPIO.setmode(GPIO.BOARD)

ip2 = "http://reckonerstudios.com/restaurante/schedule.json"
ip = "http://10.4.180.158:5000/schedule"

pinSensorNivellMenjar =  36
pinServoObrirTancarMenjar = 38
pinServoOmplirMenjar = 40

GPIO.setup(pinServoOmplirMenjar, GPIO.OUT)
GPIO.setup(pinServoObrirTancarMenjar, GPIO.OUT)
GPIO.setup(pinSensorNivellMenjar, GPIO.IN)

threads = list()

lastDay = None
lastUpdate = datetime.datetime.now()

servoObrirTancar = GPIO.PWM(pinServoObrirTancarMenjar, 50)
servoOmplirMenjar = GPIO.PWM(pinServoOmplirMenjar, 50)

servoObrirTancar.start(7.5)
servoOmplirMenjar.start(7.2)

programacioDiaria = list()

def tancar():
	print "TANCAR"
	servoObrirTancar.ChangeDutyCycle(2.7)

def obrir():
	print "OBRIR"
	servoObrirTancar.ChangeDutyCycle(6)

def stop():
	servoOmplirMenjar.ChangeDutyCycle(7.2)

def omplir_menjar(amount):
	for i in range(int(math.ceil(amount/5.1))):
		print "OMPLINT"
		servoOmplirMenjar.ChangeDutyCycle(9)
		time.sleep(1.5)
		servoOmplirMenjar.ChangeDutyCycle(6)
		time.sleep(0.7)
	stop()
	print "FINALITZAT"

def RFIDManager():
	print("YEAH BABY")
	tancar()
	stopped = threading.Event()
	mifare = nxppy.Mifare()
	while not stopped.wait(0.1):
		try:
			uid = mifare.select()
			print(uid)
			if (uid == '2118140B'):
				obrir()
				time.sleep(2)
				tancar()
		except nxppy.SelectError:
			pass

def checkFood():
	if (GPIO.input(pinSensorNivellMenjar) == GPIO.HIGH):
		print "amb menjar"
	else:
		print "sense menjar"

def requestSchedule():
	stopped = threading.Event()
	print "holita1"
	while not stopped.wait(5):
		print "holita2"
		response = urllib2.urlopen(ip)
		data = json.loads(response.read())
		data = data['actions']

		#Si la array de programaciO diaria te valors, els hem de comprobar abans d'actualitzar de nou.
		if (programacioDiaria.count > 0):
			for element in programacioDiaria:
				nowTime = datetime.datetime.now()
				scheduledTime = datetime.datetime(nowTime.year, nowTime.month, nowTime.day, 0, 0, 0)
				scheduledTime += datetime.timedelta(0, int(element['time']))
				print  "COMPROBACION NOWTIME " + str(nowTime)
				print  "COMPROBACION SCHEDULEDTIME " + str(scheduledTime) 

				margin = scheduledTime + datetime.timedelta(0, 5)
				tdelta = nowTime - margin

				if (tdelta <= datetime.timedelta(seconds=5) and tdelta > datetime.timedelta(seconds=0)):
					print "in range"
					print "OMPLINT MENJAR"
					omplir_menjar(element['amount'])
					checkFood()
				print tdelta

		programacioDiaria[:] = []

		for element in data:
			print "READING"
			detail = {}
			detail['time'] = element['time']
			detail['amount'] = element['amount']
			print "TIME: " +  str(detail['time'])
			nTime = datetime.datetime.now()
			pTime = datetime.datetime(nTime.year, nTime.month, nTime.day, 0, 0, 0)
			pTime += datetime.timedelta(0, int(element['time']))

			print str(nTime) + " NOW"
			print str(pTime) + " scheduledTime"
			if (nTime > pTime):#Les programacions per hores anteriors a l'actual compten com ja fetes
				detail['executat'] = True
			else:
				detail['executat'] = False
			
			programacioDiaria.append(copy.copy(detail))

def main():
	threadSchedule = threading.Thread(target=requestSchedule)
	threads.append(threadSchedule)
	threadSchedule.start()

	threadRFID = threading.Thread(target=RFIDManager)
	threads.append(threadRFID)
	threadRFID.start()

main()




