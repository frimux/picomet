#!/usr/bin/python
# -*- coding: utf-8 -*-

# New: Added single value graphs for display on www.picomet.ch
# New: Renamed graphs for local website, i.e. on TreePi20, by adding *X for eXperimental: 'TempX', 'PresX', 'HumiX'
# New: Modified mwsGraphs.py, mwsAir.html and pmAir.html accordingly
# New: Switched displayed pressure from airPres0 to airPres3 incl. min, max, tMin and tMax values as well as entry in valFile.txt
# New: 

# NOTE: This versions ONLY works with BMP280 as inside (inbox) pressure/temperature sensor (instead of BME280)
# NOTE: This and later versions will not be compatible anymore with earlier versions (32 and before !!!) !!!

# ##### NOTE: See lines 1295 & 1296 - THIS IS TO TAKE NO READING, AS SENSOR MUST BE REPLACED  ######################

# Importing libraries =======================================================================

# IMPORTANT: Current module mwsGraphs.py is REQUIRED for this program to run <<<<<<<<<<<<<<<<<<<<<<<<
import mwsGraphs

import smbus								# Needed for TCA9548A I2C multiplexer
import time
import datetime
from datetime import datetime as dtdt		# i.e.  "dtdt"  is an alias for class  "datetime.datetime"
import shutil
from math import log as logE				# natural logarithm
from math import exp						# exp(x) == e**x

import json
import RPi.GPIO as GPIO
import rrdtool

# Importing Adafruit DHT11/DHT22 library
import Adafruit_DHT

# Importing Adafruit_BME280 library
from Adafruit_BME280 import *

# Importing Adafruit_BMP280 library
import Adafruit_BMP.BMP280 as BMP280

# Importing MCP3208 module from GPIO Zero library
from gpiozero import MCP3208

# Configuring GPIO, TCA9548 (I2C multiplexer) and some sensors ============================================================================
# Setting GPIO pin numbering mode
GPIO.setmode(GPIO.BCM)	# set mode to BCM => use ports (not pins)

# SensorDHT is set to Adafruit_DHT.DHT22
# Note: Temperature resolution of DHT11 is 1 *C, that of DHT22 is 0.5 *C
sensorDHT = Adafruit_DHT.DHT22
# RDHT sensor connected to port GPIO17
portDHT = 17

# Defining TCA9548A (I2C multiplexer) I2C device parameters
# i2cBusNumber = 1					# Defined by Raspberry Pi to be 1 (revision dependant)
tcaI2cAddr = 0x70					# I2C address of TCA9548A (valid values are 0x70 .. 0x77 )

# Defining BME280 or BMP280 channel number on TCA9548A (valid values are 0 .. 7)
chanTcaBme1 =  1					# Multiplexer channel number for outside (Stevenson screen) BME280 attached to TCA9548
# chanTcaBme2 =  0					# Multiplexer channel number for inside BME280 attached to TCA9548 (NOTE: bmE280 !!)
chanTcaBmp3 =  0					# Multiplexer channel number for inside BMP280 attached to TCA9548 (NOTE: bmP280 !!)
# chanTcaTsl =  2					# Multiplexer channel number for TSL2561 attached to TCA9548 (NOT installed yet)

# Setting initial values ===================================================================================================================

# set initial values for main program loop
# ---------------------------------------------------------------------------------
loopTime = 20.0						# SETTING overall time length for main loop
effLoopTime = loopTime				# initial value for effective loop time
lNat10 = logE(10)
# ---------------------------------------------------------------------------------

# Defining and setting initial values for date and time variables
# Defining current time values as "dictionary" and setting initial values
timeCur = {}
timeCur['ho'] = dtdt.now().hour					# returning hour of day as a number between 0 .. 23 e.g. 14   (used for testing only)
timeCur['da'] = dtdt.now().day					# returning day of month as a number between 1 .. 31
timeCur['we'] = dtdt.now().isocalendar()[1]		# returning week of year as a number between 1 .. 366
timeCur['mo'] = dtdt.now().month				# returning month of year as a number between 1 .. 12
timeCur['ye'] = dtdt.now().year					# returning year

# Defining previous time values as "dictionary" and setting initial values
timePrev = {}
timePrev['ho'] = timeCur['ho']					# contains previous reading of hour as a number between 0 .. 23 e.g. 14   (used for testing only)
timePrev['da'] = timeCur['da']					# contains previous reading of day of month as a number between 1 .. 31 e.g. 8
timePrev['we'] = timeCur['we']					# contains previous reading of week
timePrev['mo'] = timeCur['mo']					# contains previous reading of month
timePrev['ye'] = timeCur['ye']					# contains previous reading of year

# Setting general values
uSup = 3.3					# uSup = supply supply voltage for MCP3208, across R0 and vane resistors in wind vane, and for GA1A12S202 [Volts]  (Nominal value = 3.3)
# uPlus = 4.66				# uPlus = supply supply voltage e.g for ACS712 (Nominal value = 5.0)		(NOT IN USE NOW)

# Air values ---------------------------------------------------------------------------------

# Initial values for temperature sensors DS18B20  Nr. 11 and 2
errorTemp = -999.99
ds18b20File0 = "/sys/bus/w1/devices/28-000007549813/w1_slave"			# DS18B20  Nr. 11 in Stevenson screen
ds18b20File2 = "/sys/bus/w1/devices/28-0416a0a151ff/w1_slave"			# DS18B20  Nr.  2 inbox (inside box in shack)
ds18b20File3 = "/sys/bus/w1/devices/28-0516737abdff/w1_slave"			# DS18B20  Nr.  3 inside shack (outside box)

# Setting Barometric values
h1 = 412.0					# altitude of Stevenson screen at Wilerweg 8, Olten, in m above sealevel
h3 = 411.0					# altitude of inside (inbox) sensor at Wilerweg 8, Olten, in m above sealevel
rho = 0.0065				# best estimate for temperature gradient in *C/m

# Defining airTemp0 from DS18B20 #11 as "dictionary" and assigning initial values
airTemp0 = {}			
airTemp0['cur'] = 0.0		# Current temperature
airTemp0['max'] = -90.0		# Maximum temperature today
airTemp0['min'] = 90.0		# Minimum temperature today
airTemp0['r01'] = 0.0		# Change rate of temperature since 1 hr ago

tAirTemp0 = {}			
tAirTemp0['max'] = time.time()		# Time of last maximum temperature today
tAirTemp0['min'] = time.time()		# Time of last minimum temperature today

# Defining airTemp1 from BME280 (outside) as "dictionary" and assigning initial values
### NOTE: DHT22 NOT USED  NOW
airTemp1 = {}			
airTemp1['cur'] = 0.0		# Current temperature
airTemp1['max'] = -90.0		# Maximum temperature today
airTemp1['min'] = 90.0		# Minimum temperature today
airTemp1['r01'] = 0.0		# Change rate of temperature since 1 hr ago

# Defining airPres0 from BME280 (outside) as "dictionary" and assigning initial values
airPres0 = {}			
airPres0['qfe'] = 900.0		# Current air pressure measured locally
airPres0['qff'] = 1000.0	# Current air pressure reduced to sealevel
airPres0['max'] = 0.0		# Maximum air pressure reduced to sealevel
airPres0['min'] = 10000.0	# Minimum air pressure reduced to sealevel
airPres0['r01'] = 0.0		# Change rate of air pressure since 1 hr ago
airPres0['r06'] = 0.0		# Change rate of air pressure since 6 hr ago
airPres0['r12'] = 0.0		# Change rate of air pressure since 12 hr ago

tAirPres0 = {}			
tAirPres0['max'] = time.time()		# Time of last maximum air pressure reduced to sealevel
tAirPres0['min'] = time.time()		# Time of last minimum air pressure reduced to sealevel

# Defining airPres3 from BMP280 (inside) as "dictionary" and assigning initial values
airPres3 = {}			
airPres3['qfe'] = 900.0		# Current air pressure measured locally
airPres3['qff'] = 1000.0	# Current air pressure reduced to sealevel
airPres3['max'] = 0.0		# Maximum air pressure reduced to sealevel
airPres3['min'] = 10000.0	# Minimum air pressure reduced to sealevel
airPres3['r01'] = 0.0		# Change rate of air pressure since 1 hr ago
airPres3['r06'] = 0.0		# Change rate of air pressure since 6 hr ago
airPres3['r12'] = 0.0		# Change rate of air pressure since 12 hr ago

tAirPres3 = {}			
tAirPres3['max'] = time.time()		# Time of last maximum air pressure reduced to sealevel
tAirPres3['min'] = time.time()		# Time of last minimum air pressure reduced to sealevel

# Defining airHumi0 from BME280 as "dictionary" and assigning initial values
airHumi0 = {}			
airHumi0['cur'] = 50.0		# Current humidity
airHumi0['max'] = 0.0		# Maximum humidity
airHumi0['min'] = 10000.0	# Minimum humidity
airHumi0['r01'] = 0.0		# Change rate of humidity since 1 hr ago

tAirHumi0 = {}			
tAirHumi0['max'] = time.time()		# Time of last maximum humidity
tAirHumi0['min'] = time.time()		# Time of last minimum humidity

# Defining airHumi1 from DHT22 as "dictionary" and assigning initial values (Not in use now)
airHumi1 = {}			
airHumi1['cur'] = 50.0		# Current humidity
airHumi1['max'] = 0.0		# Maximum humidity
airHumi1['min'] = 10000.0	# Minimum humidity
airHumi1['r01'] = 0.0		# Change rate of humidity since 1 hr ago

# Defining airDew (dew point) calculated from airHumi0 as "dictionary" and assigning initial values
airDew = {}			
airDew['cur'] = 0.0			# Current dew point
airDew['max'] = 0.0			# Maximum dew point
airDew['min'] = 10000.0		# Minimum dew point
airDew['r01'] = 0.0			# Change rate dew point since 1 hr ago

# Setting initial values for anemometer:
portAne = 5					# BMC port nr for Anemometer (OK)
durAne = 5					# [s], time duration (interval) for anemometer measurements
revAne = 0					# Set counter for anemometer revolutions to 0
# Defining airSpeed as "dictionary" and assigning initial values
airSpeed = {}			
airSpeed['cur'] = 0.0		# Current wind speed
airSpeed['av10'] = 0.0		# Moving average of wind speed within preceding 10 min
airSpeed['mg01'] = 0.0		# Maximum gust within preceding 1 hr
airSpeed['mgt'] = 0.0		# Maximum gust today
airSpeed['mg24'] = 0.0		# Maximum gust within preceding 24 hr
airSpeed['min'] = 10000.0	# Minimum wind speed today

tAirSpeed = {}			
tAirSpeed['max'] = time.time()		# Time of last maximum wind speed today
tAirSpeed['min'] = time.time()		# Time of last minimum wind speed today

# Defining input values for Vane:
chVane = 7					# Set channel of MCP3208 for readings (0 .. 7) (old 6)
fCorr = 1.04				# Correction-factor (ADC reading seems to be too low ??)
airDir = -10.0				# Set initial value for windvane direction

# Rain values ---------------------------------------------------------------------------------

# Setting initial values for Rain gauge:
portRain = 6				# BMC port nr for rain gauge (OK)
tiltRain = 0				# Set counter for rain gauge tilts to 0
mmPerTilt = 0.2794			# [mm/tilt]

# Defining rainFall as "dictionary" and assigning initial values
rainFall = {}
rainFall['acc'] = 0.0		# Amount of rainfall since start of measurement or beginning of year (what ever comes first)
rainFall['chr'] = 0.0		# Amount of rainfall during current hour
rainFall['cda'] = 0.0		# Amount of rainfall during current day
rainFall['cwe'] = 0.0		# Amount of rainfall during current week
rainFall['cmo'] = 0.0		# Amount of rainfall during current month
rainFall['cye'] = 0.0		# Amount of rainfall during current year
rainFall['phr'] = 0.0		# Amount of rainfall during preceding 60 minutes
rainFall['pda'] = 0.0		# Amount of rainfall during preceding 24 hours
rainFall['pwe'] = 0.0		# Amount of rainfall during preceding 7 days
rainFall['pmo'] = 0.0		# Amount of rainfall during preceding 30 days
rainFall['pye'] = 0.0		# Amount of rainfall during preceding 12 months

# Setting initial values for rain drop sensor
portRD = 18						# GPIO port for rain drop sensor DO is #18
GPIO.setup(portRD, GPIO.IN)		# Setting portRD as input
chRD = 5						# ADC channel for rain drop sensor AO is 5

# Defining rain time as "dictionary" and assigning initial values
rainT0 = {}			
rainT0['cda'] = 0					# Daily rain time (duration in sec) from rain drop sensor
rainT0['cwe'] = 0					# Accumulated rain time (duration in sec) from rain drop sensor since beginning of current week
rainT0['cmo'] = 0					# Accumulated rain time (duration in sec) from rain drop sensor since beginning of current month
rainT0['cye'] = 0					# Accumulated rain time (duration in sec) from rain drop sensor since beginning of current year

# System values ---------------------------------------------------------------------------------

# Defining cpuTemp of TPi20 as "dictionary" and assigning initial values
cpuTemp20 = {}			
cpuTemp20['cur'] = 0.0		# Current CPU temperature
cpuTemp20['max'] = -90.0	# Maximum CPU temperature today
cpuTemp20['min'] = 90.0		# Minimum CPU temperature today
cpuTemp20['r01'] = 0.0		# Change rate of CPU temperature since 1 hr ago

tcpuTemp20 = {}			
tcpuTemp20['max'] = time.time()		# Time of last maximum temperature today
tcpuTemp20['min'] = time.time()		# Time of last minimum temperature today

# Defining airTemp2 as "dictionary" and assigning initial values for DS18B20 Nr. 2 inside box in shack (inbox)
airTemp2 = {}			
airTemp2['cur'] = 0.0		# Current inbox temperature inside box in shack
airTemp2['max'] = -90.0		# Maximum temperature today inside box in shack
airTemp2['min'] = 90.0		# Minimum temperature today inside box in shack
airTemp2['r01'] = 0.0		# Change rate of temperature since 1 hr ago

tAirTemp2 = {}			
tAirTemp2['max'] = time.time()		# Time of last maximum temperature today
tAirTemp2['min'] = time.time()		# Time of last minimum temperature today

# Defining airTemp3 as "dictionary" and assigning initial values for DS18B20 Nr. 3 inside shack (outside box)
airTemp3 = {}			
airTemp3['cur'] = 0.0		# Current inside temperature in shack
airTemp3['max'] = -90.0		# Maximum temperature today inside shack
airTemp3['min'] = 90.0		# Minimum temperature today inside shack
airTemp3['r01'] = 0.0		# Change rate of temperature since 1 hr ago

tAirTemp3 = {}			
tAirTemp3['max'] = time.time()		# Time of last maximum temperature today
tAirTemp3['min'] = time.time()		# Time of last minimum temperature today

# Solar values ---------------------------------------------------------------------------------

# Define input values for GA1A12S202-0:
chGA0 = 0					# Set channel of MCP3208 for readings (0 .. 7)  (old 4)

# Defining solFlux0 from GA1A12S202-0 as "dictionary" and assigning initial values
solFlux0 = {}			
solFlux0['cur'] = 0.0		# Current illuminance
solFlux0['max'] = 0.0		# Maximum illuminance
solFlux0['min'] = 10000.0	# Minimum illuminance
solFlux0['r01'] = 0.0		# Change rate of illuminance since 1 hr ago

tSolFlux0 = {}			
tSolFlux0['max'] = time.time()		# Time of last maximum illuminance
tSolFlux0['min'] = time.time()		# Time of last minimum illuminance

sunT0 = 0.0					# Daily sun time (duration) from sensor 0

# Define input values for GA1A12S202-1:
chGA1 = 2					# Set channel of MCP3208 for readings (0 .. 7) (old 3)

# Defining solFlux1 from GA1A12S202-1 as "dictionary" and assigning initial values
solFlux1 = {}			
solFlux1['cur'] = 0.0		# Current Illuminance
solFlux1['max'] = 0.0		# Maximum Illuminance
solFlux1['min'] = 10000.0	# Minimum Illuminance
solFlux1['r01'] = 0.0		# Change rate of Illuminance since 1 hr ago

tSolFlux1 = {}			
tSolFlux1['max'] = time.time()		# Time of last maximum illuminance
tSolFlux1['min'] = time.time()		# Time of last minimum illuminance

# Defining sunT1 for sunshine duration 
sunT1 = {}			
sunT1['cda'] = 0					# Daily sunshine time (duration in sec) from sensor 1
sunT1['cwe'] = 0					# Accumulated sun time (duration in sec) from sensor 1 since beginning of current week
sunT1['cmo'] = 0					# Accumulated sun time (duration in sec) from sensor 1 since beginning of current month
sunT1['cye'] = 0					# Accumulated sun time (duration in sec) from sensor 1 since beginning of current year
# sunT1['cda'] = 10250				# >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>  Value ONLY for testing !!!!!!!!!!!!!!!!

# Defining input values for LDR:		(NOT USED NOW)
#chLDR = 3					# Set channel of MCP3208 for readings (0 .. 7)  (old 2)
#rOne = 10000.0				# Value of series resister in Ohms as float variable

# Defining solFlux2 from LDR as "dictionary" and assigning initial values
solFlux2 = {}			
solFlux2['cur'] = 0.0		# Current Illuminance
solFlux2['max'] = 0.0		# Maximum Illuminance
solFlux2['min'] = 10000.0	# Minimum Illuminance
solFlux2['r01'] = 0.0		# Change rate of Illuminance since 1 hr ago

# Defining solUvi from ML8511 as "dictionary" and assigning initial values
solUvi = {}			
solUvi['cur'] = 0.0			# Current UV Illuminance
solUvi['max'] = 0.0			# Maximum UV Illuminance
solUvi['min'] = 10000.0		# Minimum UV Illuminance
solUvi['r01'] = 0.0			# Change rate of UV Illuminance since 1 hr ago

tSolUvi = {}			
tSolUvi['max'] = time.time()		# Time of last maximum panel voltage
tSolUvi['min'] = time.time()		# Time of last minimum panel voltage

# Defining input values for ACS712 (Current Detection Module):			(NOT IN USE NOW) !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
# Note: Nominal supply voltage for ACS712 is uPlus = 5.0
# r1 = 33000.0				# First resistor for voltage devider in Ohms as float variable
# r2 = 68000.0				# Second resistor for voltage devider in Ohms as float variable
# chACS  = (tbd)			# Set channel of MCP3208 for readings (0 .. 7)		NOTE: THIS CHANNEL IS NOW USED FOR GA1A12S202-1	!!!!!!!!!!!!!!!!!!

# Defining solPvolt (panel current) from Voltage Detection Module as "dictionary" and assigning initial values
solPvolt = {}			
solPvolt['cur'] = 0.0		# Current panel voltage
solPvolt['max'] = 0.0		# Maximum panel voltage
solPvolt['min'] = 100.0		# Minimum panel voltage

tSolPvolt = {}			
tSolPvolt['max'] = time.time()		# Time of last maximum panel voltage
tSolPvolt['min'] = time.time()		# Time of last minimum panel voltage

# Defining solPcurr (panel current) from ACS712 as "dictionary" and assigning initial values
solPcurr = {}			
solPcurr['cur'] = 0.0		# Current panel current
solPcurr['max'] = 0.0		# Maximum panel current
solPcurr['min'] = 100.0		# Minimum panel current

tSolPcurr = {}			
tSolPcurr['max'] = time.time()		# Time of last maximum panel current
tSolPcurr['min'] = time.time()		# Time of last minimum panel current

# Defining solBvolt (battery voltage) from Voltage Detection Module as "dictionary" and assigning initial values
solBvolt = {}			
solBvolt['cur'] = 0.0		# Current battery voltage
solBvolt['max'] = 0.0		# Maximum battery voltage
solBvolt['min'] = 100.0		# Minimum battery voltage

tSolBvolt = {}			
tSolBvolt['max'] = time.time()		# Time of last maximum battery voltage
tSolBvolt['min'] = time.time()		# Time of last minimum battery voltage

# Defining solBcurr (battery current) from Current Detection Module as "dictionary" and assigning initial values
solBcurr = {}			
solBcurr['cur'] = 0.0		# Current battery current
solBcurr['max'] = 0.0		# Maximum battery current
solBcurr['min'] = 100.0		# Minimum battery current

tSolBcurr = {}			
tSolBcurr['max'] = time.time()		# Time of last maximum battery current
tSolBcurr['min'] = time.time()		# Time of last minimum battery current

# RRDtool definitions ===========================================================================================

# Setting initial values for RRDtool:
# dbStep = 6									# Time interval between PDPs for all RRD databases in seconds
dbStep = 12										# Time interval between PDPs for all RRD databases in seconds

# rrd database for air values
adbName = 'airDat'								# Databasename: airDat = air data
adbFile = adbName +'.rrd'						# Database filename

# rrd database for rain values
rdbName = 'rainDat'								# Databasename: rainDat = rain data
rdbFile = rdbName +'.rrd'						# Database filename

# rrd database for system values
ydbName = 'sysDat'								# Databasename: sysDat = system data
ydbFile = ydbName +'.rrd'						# Database filename

# rrd database for inside values
idbName = 'insDat'								# Databasename: insDat = inside data
idbFile = idbName +'.rrd'						# Database filename

# rrd database for solar values
sdbName = 'solDat'								# Databasename: solDat = solar data
sdbFile = sdbName +'.rrd'						# Database filename

# rrd database for daily values
ddbName = 'dayDat'								# Databasename: maxDat = maximum values
ddbFile = ddbName +'.rrd'						# Database filename

# rrd database for daily maximum values
xdbName = 'maxDat'								# Databasename: maxDat = maximum values
xdbFile = xdbName +'.rrd'						# Database filename

# rrd database for daily minimum values
ndbName = 'minDat'								# Databasename: minDat = minimum values
ndbFile = ndbName +'.rrd'						# Database filename

# Creating RRD database for air values, if it doesn't exist -------------------------------------------------------
try:
	with open(adbFile): pass
	print "Found air database: " + adbFile

except IOError:
	print "Creating new air data base: " + adbFile
	rrdtool.create("%s" %(adbFile),							# airDat.rrd
			"--step","%s" %(dbStep),
			"--start",'0',				
			"DS:airDatTemp0:GAUGE:2000:U:U",				# Outside temperature from DS18B20
			"DS:airDatTemp0Max:GAUGE:2000:U:U",				# Max outside temperature from DS18B20
			"DS:airDatTemp0Min:GAUGE:2000:U:U",				# Min outside temperature from DS18B20
			"DS:airDatTemp1:GAUGE:2000:U:U",				# Outside temperature from BME280 (replaces Temp of DHT22)
			"DS:airDatPres0qfe:GAUGE:2000:U:U",				# Air pressure (QFE) from BME280 (replacement of BMP180)
			"DS:airDatPres0qff:GAUGE:2000:U:U",				# Air pressure (QFF) calculated from BME280 QFE pressure
			"DS:airDatPres0Max:GAUGE:2000:U:U",				# Max air pressure (QFF) from BME280 (replacement of BMP180)
			"DS:airDatPres0Min:GAUGE:2000:U:U",				# Min air pressure (QFF) from BME280 (replacement of BMP180)
			"DS:airDatPres1qfe:GAUGE:2000:U:U",				# Air pressure (QFE) from … (RESERVE)
			"DS:airDatPres1qff:GAUGE:2000:U:U",				# Air pressure (QFF) calculated from … (RESERVE)
			"DS:airDatHumi0:GAUGE:2000:U:U",				# Humidity from BME280
			"DS:airDatHumi0Max:GAUGE:2000:U:U",				# Max humidity from BME280
			"DS:airDatHumi0Min:GAUGE:2000:U:U",				# Min humidity from BME280
			"DS:airDatHumi1:GAUGE:2000:U:U",				# Humidity from DHT22 (as control value)
			"DS:airDatDew:GAUGE:2000:U:U",					# Dew point, calculated
			"DS:airDatSpeed:GAUGE:2000:U:U",				# Airspeed from Anemometer
			"DS:airDatSpeedMax:GAUGE:2000:U:U",				# Max airspeed from Anemometer for display in graph
			"DS:airDatDir:GAUGE:2000:U:U",					# Winddirection from Windvane
			"RRA:MAX:0.5:1:15000",							# 50 hours, one value every 12 secs (if dbStep = 12 !)
			"RRA:MIN:0.5:1:15000",							# 50 hours, one value every 12 secs (if dbStep = 12 !)
			"RRA:MAX:0.5:5:21600",							# 15 days, one value every 60 secs (if dbStep = 12 !)
			"RRA:MIN:0.5:5:21600",							# 15 days, one value every 60 secs (if dbStep = 12 !)
			"RRA:AVERAGE:0.5:20:25200",						# 70 days, one value every 4 min (if dbStep = 12 !)
			"RRA:AVERAGE:0.5:50:57600",						# 400 days, one value every 10 min (if dbStep = 12 !)
				)


# Creating RRD database for rain values only, if it doesn't exist  -----------------------------------------------
try:
	with open(rdbFile): pass
	print "Found rain database: " + rdbFile

except IOError:
	print "Creating new rain data base: " + rdbFile
	rrdtool.create("%s" %(rdbFile),						# rainDat.rrd
			"--step","%s" %(dbStep),					# Note: same value as main database for all values
			"--start",'0',								# Note: same value as main database for all values
			"DS:rainDatTilt:GAUGE:2000:U:U",			# Tilts from from rain gauge
			"DS:rainDatRain:GAUGE:2000:U:U",			# Rain in mm from rain gauge: mmPerTilt = 0.2794
			"DS:rainDatYesno:GAUGE:2000:U:U",			# Raining YES or NO as digital value of rain drop sensor  i.e. two values:  0  or  1
			"DS:rainDatInt:GAUGE:2000:U:U",				# Raining intensity as analog value of rain drop sensor
			"RRA:MAX:0.5:1:15000",						# 50 hours, one value every 12 secs (if dbStep = 12 !)
			"RRA:MAX:0.5:5:21600",						# 15 days, one value every 60 secs (if dbStep = 12 !)
			"RRA:MAX:0.5:20:25200",						# 70 days, one value every 4 min (if dbStep = 12 !)
			"RRA:MAX:0.5:50:57600",						# 400 days, one value every 10 min (if dbStep = 12 !)
			"RRA:MAX:0.5:7200:400",						# 400 days, one value every day (if dbStep = 12 !)
				)


# Creating RRD database for system values, if it doesn't exist  --------------------------------------------------
try:							
	with open(ydbFile): pass						
	print "Found system database: " + ydbFile						
							
except IOError:							
	print "Creating new system data base: " + ydbFile						
	rrdtool.create("%s" %(ydbFile),							# sysDat.rrd
			"--step","%s" %(dbStep),				
			"--start",'0',				
			"DS:sysDatCPU2:GAUGE:2000:U:U",					# Temperature of RPi2 CPU
			"DS:sysDatCPU2Max:GAUGE:2000:U:U",				# Max temperature of RPi2 CPU
			"DS:sysDatCPU2Min:GAUGE:2000:U:U",				# Min temperature of RPi2 CPU
			"DS:sysDatTemp2:GAUGE:2000:U:U",				# Inside temperature from DS18B20 Nr. 2
			"DS:sysDatTemp2Max:GAUGE:2000:U:U",				# Max inside temperature from DS18B20 Nr. 2
			"DS:sysDatTemp2Min:GAUGE:2000:U:U",				# Min inside temperature from DS18B20 Nr. 2
			"RRA:MAX:0.5:1:15000",							# 50 hours, one value every 12 secs (if dbStep = 12 !)
			"RRA:MIN:0.5:1:15000",							# 50 hours, one value every 12 secs (if dbStep = 12 !)
			"RRA:MAX:0.5:5:21600",							# 15 days, one value every 60 secs (if dbStep = 12 !)
			"RRA:MIN:0.5:5:21600",							# 15 days, one value every 60 secs (if dbStep = 12 !)
			"RRA:AVERAGE:0.5:20:25200",						# 70 days, one value every 4 min (if dbStep = 12 !)
			"RRA:AVERAGE:0.5:50:57600",						# 400 days, one value every 10 min (if dbStep = 12 !)
				)			

# Creating RRD database for inside values, if it doesn't exist  --------------------------------------------------
try:							
	with open(idbFile): pass						
	print "Found inside database: " + idbFile						
							
except IOError:							
	print "Creating new inside data base: " + idbFile						
	rrdtool.create("%s" %(idbFile),							# insDat.rrd
			"--step","%s" %(dbStep),				
			"--start",'0',				
			"DS:insDatTemp3:GAUGE:2000:U:U",				# Inside temperature from DS18B20 Nr. 3
			"DS:insDatTemp3Max:GAUGE:2000:U:U",				# Max inside temperature from DS18B20 Nr. 3
			"DS:insDatTemp3Min:GAUGE:2000:U:U",				# Min inside temperature from DS18B20 Nr. 3
			"DS:insDatPres3qfe:GAUGE:2000:U:U",				# Inside pressure from BME280 on connector board
			"DS:insDatPres3qff:GAUGE:2000:U:U",				# Inside pressure from BME280 on connector board
			"DS:insDatPres3Max:GAUGE:2000:U:U",				# Max inside pressure from BME280
			"DS:insDatPres3Min:GAUGE:2000:U:U",				# Min inside pressure from BME280
			"DS:insDatVal3:GAUGE:2000:U:U",					# Inside value 3 (RESERVE)
			"DS:insDatVal3a:GAUGE:2000:U:U",				# Inside value 3a (RESERVE)
			"DS:insDatVal3b:GAUGE:2000:U:U",				# Inside value 3b (RESERVE)
			"RRA:MAX:0.5:1:15000",							# 50 hours, one value every 12 secs (if dbStep = 12 !)
			"RRA:MIN:0.5:1:15000",							# 50 hours, one value every 12 secs (if dbStep = 12 !)
			"RRA:MAX:0.5:5:21600",							# 15 days, one value every 60 secs (if dbStep = 12 !)
			"RRA:MIN:0.5:5:21600",							# 15 days, one value every 60 secs (if dbStep = 12 !)
			"RRA:AVERAGE:0.5:20:25200",						# 70 days, one value every 4 min (if dbStep = 12 !)
			"RRA:AVERAGE:0.5:50:57600",						# 400 days, one value every 10 min (if dbStep = 12 !)
				)			

# Creating RRD database for solar values, if it doesn't exist  ------------------------------------------------
try:
	with open(sdbFile): pass
	print "Found solar database: " + sdbFile

except IOError:
	print "Creating new solar data base: " + sdbFile
	rrdtool.create("%s" %(sdbFile),							# solDat.rrd
			"--step","%s" %(dbStep),
			"--start",'0',
			"DS:solDatFlux0:GAUGE:2000:U:U",				# Illuminance raw data [mV] from GA1A12S202-0 (shack)
			"DS:solDatFlux0Max:GAUGE:2000:U:U",				# Daily maximum raw data [mV] Illuminance from GA1A12S202-0 (shack) for display in graph
			"DS:solDatFlux1:GAUGE:2000:U:U",				# Illuminance raw data [mV] from GA1A12S202-1 (balcony)
			"DS:solDatFlux1Max:GAUGE:2000:U:U",				# Daily maximum raw data [mV] Illuminance from GA1A12S202-1 (balcony) for display in graph
			"DS:solDatFlux2:GAUGE:2000:U:U",				# Illuminance raw data [mV] from (tbd)      (RESERVE)
			"DS:solDatFlux2Max:GAUGE:2000:U:U",				# Daily maximum raw data [mV] Illuminance from (tbd) for display in graph      (RESERVE)
			"DS:solDatUvi:GAUGE:2000:U:U",					# UV light from ML8511
			"DS:solDatUviMax:GAUGE:2000:U:U",				# Daily maximum UV light from ML8511
			"DS:solDatPvolt:GAUGE:2000:U:U",				# Solar panel voltage
			"DS:solDatPvoltMax:GAUGE:2000:U:U",				# Daily maximum solar panel voltage
			"DS:solDatPcurr:GAUGE:2000:U:U",				# Solar panel current delivered (from ACS712)
			"DS:solDatPcurrMax:GAUGE:2000:U:U",				# Daily maximum solar panel current delivered (from ACS712)
			"DS:solDatBvolt:GAUGE:2000:U:U",				# Battery voltage (from Voltage Detection Module)
			"DS:solDatBvoltMax:GAUGE:2000:U:U",				# Daily maximum battery voltage drawn (from ACS712)
			"DS:solDatBcurr:GAUGE:2000:U:U",				# Battery current drawn (from ACS712)
			"DS:solDatBcurrMax:GAUGE:2000:U:U",				# Daily maximum battery current drawn (from ACS712)
			"RRA:MAX:0.5:1:15000",							# 50 hours, one value every 12 secs (if dbStep = 12 !)
			"RRA:MAX:0.5:5:21600",							# 15 days, one value every 60 secs (if dbStep = 12 !)
			"RRA:AVERAGE:0.5:20:25200",						# 70 days, one value every 4 min (if dbStep = 12 !)
			"RRA:AVERAGE:0.5:50:57600",						# 400 days, one value every 10 min (if dbStep = 12 !)
				)

# Creating RRD database for DAILY values, if it doesn't exist  --------------------------------------------------
try:
	with open(ddbFile): pass
	print "Found day database: " + ddbFile
							
except IOError:							
	print "Creating new day data base: " + ddbFile
	rrdtool.create("%s" %(ddbFile),							# dayDat.rrd
			"--start",'0',									# Start now
			"--step","%s" %(dbStep),				
			"DS:dayDatSunT0:GAUGE:2000:U:U",				# Daily time duration of direct sunshine (Lux values > 8000 Lux)
			"DS:dayDatSunT1:GAUGE:2000:U:U",				# Daily time duration of direct sunshine (Lux values > 8000 Lux)
			"DS:dayDatVal0:GAUGE:2000:U:U",					# Daily value of rain: Val0 == rainT0
			"DS:dayDatVal1:GAUGE:2000:U:U",					# Daily value of (tbd)      (RESERVE)
			"RRA:MAX:0.5:1:15000",							# 50 hours, one value every 12 secs (if dbStep = 12 !)
			"RRA:MAX:0.5:5:21600",							# 15 days, one value every 60 secs (if dbStep = 12 !)
			"RRA:MAX:0.5:20:25200",							# 70 days, one value every 4 min (if dbStep = 12 !)
			"RRA:MAX:0.5:50:57600",							# 400 days, one value every 10 min (if dbStep = 12 !)
			"RRA:MAX:0.5:7200:400",							# 400 days, one value every day (if dbStep = 12 !)
				)

# Creating RRD database for DAILY maximum values, if it doesn't exist  --------------------------------------------------
try:
	with open(xdbFile): pass
	print "Found maximum database: " + xdbFile
							
except IOError:							
	print "Creating new maximum data base: " + xdbFile
	rrdtool.create("%s" %(xdbFile),							# maxDat.rrd
			"--start",'0',				
			"--step","%s" %(dbStep),				
			"DS:maxDatTemp0:GAUGE:2000:U:U",				# Daily maximum temperature from DS18B20
			"DS:maxDatTTemp0:GAUGE:2000:U:U",				# Time of daily maximum temperature from DS18B21
			"DS:maxDatPres0:GAUGE:2000:U:U",				# Daily maximum pressure from BME280 (replacement of BMP180)
			"DS:maxDatTPres0:GAUGE:2000:U:U",				# Time of daily maximum pressure from BME280 (replacement of BMP180)
			"DS:maxDatHumi0:GAUGE:2000:U:U",				# Daily maximum humidity from BME280 (replacement of BMP180)
			"DS:maxDatTHumi0:GAUGE:2000:U:U",				# Time of daily maximum humidity from BME280 (replacement of BMP180)
			"DS:maxDatSpeed:GAUGE:2000:U:U",				# Daily maximum air speed from Anemometer
			"DS:maxDatTSpeed:GAUGE:2000:U:U",				# Time of daily maximum air speed from Anemometer
			"DS:maxDatFlux0:GAUGE:2000:U:U",				# Daily maximum of solar Flux0
			"DS:maxDatTFlux0:GAUGE:2000:U:U",				# Time of daily maximum of solar Flux0
			"DS:maxDatUvi:GAUGE:2000:U:U",					# Daily maximum of UV irradiation
			"DS:maxDatTUvi:GAUGE:2000:U:U",					# Time of daily maximum of UV irradiation
			"DS:maxDatPcurr:GAUGE:2000:U:U",				# Daily maximum of solar panel current
			"DS:maxDatTPcurr:GAUGE:2000:U:U",				# Time of daily maximum of solar panel current
			"DS:maxDatBvolt:GAUGE:2000:U:U",				# Daily maximum of battery voltage
			"DS:maxDatTBvolt:GAUGE:2000:U:U",				# Time of daily maximum of battery voltage
			"DS:maxDatBcurr:GAUGE:2000:U:U",				# Daily maximum of battery current
			"DS:maxDatTBcurr:GAUGE:2000:U:U",				# Time of daily maximum of battery current
			"DS:maxDatVal0:GAUGE:2000:U:U",					# Daily maximum of (tbd)      (RESERVE)
			"DS:maxDatTVal0:GAUGE:2000:U:U",				# Time of daily maximum of (tbd)      (RESERVE)
			"RRA:MAX:0.5:300:9600",							# 400 days, one value every hour (if step = 12 !)
			"RRA:MAX:0.5:7200:400",							# 400 days, one value every day
				)			

# Creating RRD database for DAILY minimum values, if it doesn't exist  ----------------------------------------
try:
	with open(ndbFile): pass
	print "Found minimum database: " + ndbFile

except IOError:
	print "Creating new minimum data base: " +ndbFile
	rrdtool.create("%s" %(ndbFile),							# minDat.rrd
			"--start",'0',
			"--step","%s" %(dbStep),				
			"DS:minDatTemp0:GAUGE:2000:U:U",				# Daily minimum temperature from DS18B20
			"DS:minDatTTemp0:GAUGE:2000:U:U",				# Time of daily minimum temperature from DS18B21
			"DS:minDatPres0:GAUGE:2000:U:U",				# Daily minimum pressure from BME280 (replacement of BMP180)
			"DS:minDatTPres0:GAUGE:2000:U:U",				# Time of daily minimum pressure from BME280 (replacement of BMP180)
			"DS:minDatHumi0:GAUGE:2000:U:U",				# Daily minimum humidity from BME280 (replacement of BMP180)
			"DS:minDatTHumi0:GAUGE:2000:U:U",				# Time of daily minimum humidity from BME280 (replacement of BMP180)
			"DS:minDatSpeed:GAUGE:2000:U:U",				# Daily minimum air speed from Anemometer
			"DS:minDatTSpeed:GAUGE:2000:U:U",				# Time of daily minimum air speed from Anemometer
			"DS:minDatFlux0:GAUGE:2000:U:U",				# Daily minimum of solar Flux0
			"DS:minDatTFlux0:GAUGE:2000:U:U",				# Time of daily minimum of solar Flux0
			"DS:minDatUvi:GAUGE:2000:U:U",					# Daily minimum of UV irradiation
			"DS:minDatTUvi:GAUGE:2000:U:U",					# Time of daily minimum of UV irradiation
			"DS:minDatPcurr:GAUGE:2000:U:U",				# Daily minimum of solar panel current
			"DS:minDatTPcurr:GAUGE:2000:U:U",				# Time of daily minimum of solar panel current
			"DS:minDatBvolt:GAUGE:2000:U:U",				# Daily minimum of battery voltage
			"DS:minDatTBvolt:GAUGE:2000:U:U",				# Time of daily minimum of battery voltage
			"DS:minDatBcurr:GAUGE:2000:U:U",				# Daily minimum of battery current
			"DS:minDatTBcurr:GAUGE:2000:U:U",				# Time of daily minimum of battery current
			"DS:minDatVal0:GAUGE:2000:U:U",					# Daily minimum of (tbd)      (RESERVE)
			"DS:minDatTVal0:GAUGE:2000:U:U",				# Time of daily minimum of (tbd)      (RESERVE)
			"RRA:MIN:0.5:300:9600",							# 400 days, one value every hour (if step = 12 !)
			"RRA:MIN:0.5:7200:400",							# 400 days, one value every day
				)			

# Defining functions ===========================================================================================================

# Defining general functions ------------------------------------------------------------------------------------------------

# Function to set multiplexer channel on TCA9548A for attached device
def setTcaChannel(i2cAddress, muxChannel):
	bus = smbus.SMBus(1)									# 1 = i2cBusNumber (given by Raspberry Pi revision)
	muxByChannel = 2**muxChannel							# Get "byte value" for channel number
	bus.write_byte(i2cAddress, muxByChannel)
	time.sleep(0.1)

# Defining functions for air values ------------------------------------------------------------------------------------------------

def readPrTe(channelTca):		# Readings from BMP280

	# Setting multiplexer channel on TCA9548A for BMP280
	setTcaChannel(tcaI2cAddr, channelTca)

	# Creating sensor instance for BMEP80 on chanTca
	sensorBMP = BMP280.BMP280()				# NOTE: MUST come AFTER setting multiplexer channel

	te = sensorBMP.read_temperature()		# NOTE: temp MUST be read before pressure !!!
	pr = sensorBMP.read_pressure()
	return pr, te

def readPrTeHu(chanTca):		# Readings from BME280

	# Setting multiplexer channel on TCA9548A for BME280
	setTcaChannel(tcaI2cAddr, chanTca)

	# Creating sensor instance for BME280 on chanTca
	sensorBME = BME280(t_mode=BME280_OSAMPLE_8, p_mode=BME280_OSAMPLE_8, h_mode=BME280_OSAMPLE_8)		# NOTE: MUST come AFTER setting multiplexer channel

	t = sensorBME.read_temperature()		# NOTE: temp MUST be read before pressure !!!
	p = sensorBME.read_pressure()
	h = sensorBME.read_humidity()
	return p, t, h

def presReduction1(presQFE, temp, alti):			# Reduces air pressure (presQFE) measured at station altitude (alti in m) to sealevel pressure (presQFF)
	# Using swissmeteo formula
	a = temp*10.0 + 2731.5
	b = alti / 30.8
	c = (a/(presQFE*10.0))*exp(((a + b)*11.5526 - 26821.0)/(a + b - 1060.0))
	presQFF = presQFE*exp(b*10.5152/(c + a + b))
	return presQFF

def presReduction2(presQFE, temp, humi, alti):			# Reduces air pressure (presQFE) measured at station altitude (alti in m) to sealevel pressure (presQFF)
	# Using formula from Doc-10_Pressure-red.pdf + Doc_3_4a_Humidity_DGroselj.pdf + self written
	fP = 1.0
	eV = (humi / 100.0) * fP * 6.112 * exp(17.62 * temp / (243.12 + temp))
	presQFF = presQFE * exp(9.80665 * alti / (287.05 *(temp + 273.15 + 0.0065 * alti / 2.0 + eV * 0.12)))
	return presQFF

def readTemperature(file):		# Reading temperature from DS18B20 1-wire temperature sensor
	tfile = open(file)
	text = tfile.read()
	tfile.close()
	lines = text.split("\n")
	if lines[0].find("YES") > 0:
		temp = float((lines[1].split(" ")[9])[2:])
		temp /= 1000
		return temp
	else:
		return errorTemp

def readHumTemp():				# Readings from DHT22
	humidity, temperature = Adafruit_DHT.read_retry(sensorDHT, portDHT)
	if humidity is None and temperature is None:
		print ('Failed to get reading. Try again!')
	if humidity >=99.85:		# Otherwise the value never exceeds 99.90% (=cosmetics!)
		humidity = 100.0
	return humidity, temperature

# Define threaded callback function for anemometer
def spinAne(channel):
	global revAne
	revAne += 1

def speedAne(rev,timeSec):
	# global revAne
	kmPerHour = rev * 1.492 * 1.609 / timeSec
	return kmPerHour

def vaneDirection(chan, uIn, fC):		# For uIn = uSup = 3.3V

	# Read the value of ADC channel 'chan' and convert to direction
	uMeas = MCP3208(channel = chan, device = 0).value * uIn

	# Apply correction-factor
	uMeas =uMeas*fC
	# Rounding to 3 digits after comma
	uMeas = int(uMeas*1000.0 + 0.5) / 1000.0
	
	if uMeas >= 0.0 and uMeas < 0.241 : 
		dirDegree = 112.5	# OstSuedOst
	elif uMeas >= 0.241 and uMeas < 0.285 :
		dirDegree = 67.5	# OstNordOst
	elif uMeas >= 0.285 and uMeas < 0.354 :
		dirDegree = 90.0	# Ost
		shutil.copy('/var/www/html/mwsImages/dir090Oc.jpg', '/var/www/html/airGra/windDir.jpg')
	elif uMeas >= 0.354 and uMeas < 0.501 :
		dirDegree = 157.5	# SuedSuedOst
	elif uMeas >= 0.501 and uMeas < 0.692 :
		dirDegree = 135.0	# SuedOst
		shutil.copy('/var/www/html/mwsImages/dir135SOc.jpg', '/var/www/html/airGra/windDir.jpg')
	elif uMeas >= 0.692 and uMeas < 0.857 :
		dirDegree = 202.5	# SSuedSuedWest
	elif uMeas >= 0.857 and uMeas < 1.117 :
		dirDegree = 180.0	# Sued
		shutil.copy('/var/www/html/mwsImages/dir180Sc.jpg', '/var/www/html/airGra/windDir.jpg')
	elif uMeas >= 1.117 and uMeas < 1.398 :
		dirDegree = 22.5	# NordNordOst
	elif uMeas >= 1.398 and uMeas < 1.709 :
		dirDegree = 45.0	# NordOst
		shutil.copy('/var/www/html/mwsImages/dir045NOc.jpg', '/var/www/html/airGra/windDir.jpg')
	elif uMeas >= 1.709 and uMeas < 1.981 :
		dirDegree = 247.5	# WestSuedWest
	elif uMeas >= 1.981 and uMeas < 2.148 :
		dirDegree = 225.0	# SuedWest
		shutil.copy('/var/www/html/mwsImages/dir225SWc.jpg', '/var/www/html/airGra/windDir.jpg')
	elif uMeas >= 2.148 and uMeas < 2.399 :
		dirDegree = 337.5	# NordNordWest
	elif uMeas >= 2.399 and uMeas < 2.600 :
		dirDegree = 0.0	# Nord
		shutil.copy('/var/www/html/mwsImages/dir000Nc.jpg', '/var/www/html/airGra/windDir.jpg')
	elif uMeas >= 2.600 and uMeas < 2.763 :
		dirDegree = 292.5	# WestNordWest
	elif uMeas >= 2.763 and uMeas < 2.953 :
		dirDegree = 315.0	# NordWest
		shutil.copy('/var/www/html/mwsImages/dir315NWc.jpg', '/var/www/html/airGra/windDir.jpg')
	else :
		dirDegree = 270.0	# West
		shutil.copy('/var/www/html/mwsImages/dir270Wc.jpg', '/var/www/html/airGra/windDir.jpg')
	
	return uMeas, dirDegree

# Defining functions for rain values ---------------------------------------------------------------------------------------

# Defining threaded callback function for Rain gauge
def rainTipped(channel):
	global tiltRain
	tiltRain += 1

# Defining function to read digital and analog values from rain drop sensor
def rainDrops(gpioPort, adcChannel):
	digitalOut = GPIO.input(gpioPort)								# Reading digital value digitalOut value via port gpioPort
	analogOut = MCP3208(channel = adcChannel, device = 0).value		# Reading analogue value analogOut value via adcChannel of ADC-0 (MCP3208)
	return digitalOut, analogOut

# Defining functions for system values -------------------------------------------------------------------------------------

def getCpuTemperature():
	tempFile = open( "/sys/class/thermal/thermal_zone0/temp" )
	cpuT = tempFile.read()
	tempFile.close()
	cpuT = float(cpuT)/1000
	return cpuT
	
# Defining functions for solar values -------------------------------------------------------------------------------------

# Defining function for reading GA1A12S202 voltage
# Inputs are: ADC channel chan and supply voltage uS
# Outputs are: uOut = GA1A12S202 output voltage
def readGA (chan, uS):
	# Read the value of ADC channel 'chan' and convert to voltage
	uOut = MCP3208(channel = chan, device = 0).value * uS			# using device = 0 (ADC on upper board)
	print ('GA1A12S202 uOut = %5d') %(uOut)
	# Calculate the output voltage value in Volts
	return uOut

# Defining function for reading LDR voltage		(NOT USED NOW)
# Inputs are: ADC channel chan, supply voltage uS and series resistor rSer (in Ohms, as float variables)
# Outputs are: voltage across LDR uOut, LDR resistance rOut 
def readLDR (chan, uS, rSer):
	# Read the value of ADC channel 'chan' and convert to voltage
	uOut = MCP3208(channel = chan, device = 0).value * uS			# using device = 0 (ADC on upper board)
	# Calculate the output resistance
	rOut = rSer*uOut/(uS - uOut)
	return uOut, rOut

# Defining function for reading ACS712 to determine solar panal current		(NOT IN USE NOW)
# Inputs are: ADC channel chan, supply voltage uS of MCP3008 (!!), and r1 and r2 (voltage devider resistors, in Ohms, as float variables)
# Outputs are: output voltage of ACS712 
def readACS (chan, uS, rUp, rLow):
	# Read the value of ADC channel 'chan' and convert to voltage
	uOut = MCP3208(channel = chan, device = 1).value * uS			# using device = 1 (ADC on lower board)
	uOut = (1.0 + rUp / rLow) * uOut			# Calculating higher voltage due to voltage devider
	return uOut

# Defining Max - and Min - functions for values read from RRD databases -------------------------------------------------------------------------------------

def prevMaxVal(dbFilename, consFunction, dsPosition, timeSpan):
# This function can be used in case program is started anew WITHIN timeSpan minutes
# This function gets the maximum value of previous floating point values from an rrd database using rrdtool.fetch method
# dbFilename must be a string representing the rrd database filename from which data are fetched
# consFunction is a string representing the consolidation function of the data source used 
# dsPosition is an integer >= 0 representing the position of the data source used 
# timeSpan is a positive integer indication the number of minutes from which the data are fetched

	# Fetches timeSpan minutes worth of data, starting timeSpan minutes ago, ending now
	getData = rrdtool.fetch("%s" %(dbFilename),"%s" %(consFunction), "-s -%smin" %(timeSpan))
	getList = [getData[2][i][dsPosition] for i in range(len(getData[2])) if getData[2][i][dsPosition] is not None]
	if len(getList) != 0:
		valBefore = max(getList)		# Getting previous max value
	else:
		valBefore = 0.0
	return valBefore

def prevMinVal(dbFilename, consFunction, dsPosition, timeSpan):
# This function can be used in case program is started anew WITHIN timeSpan minutes
# This function gets the maximum value of previous floating point values from an rrd database using rrdtool.fetch method
# dbFilename must be a string representing the rrd database filename from which data are fetched
# consFunction is a string representing the consolidation function of the data source used 
# dsPosition is an integer >= 0 representing the position of the data source used 
# timeSpan is a positive integer indication the number of minutes from which the data are fetched

	# Fetches timeSpan minutes worth of data, starting timeSpan minutes ago, ending now
	getData = rrdtool.fetch("%s" %(dbFilename),"%s" %(consFunction), "-s -%smin" %(timeSpan))
	getList = [getData[2][i][dsPosition] for i in range(len(getData[2])) if getData[2][i][dsPosition] is not None]
	if len(getList) != 0:
		valBefore = min(getList)		# Getting previous min value
	else:
		valBefore = 10000.0
	return valBefore

# End of functions definitions --------------------------------------------------------------------------------------------------------

# Setting up GPIO interrupt parameters =========== (must be set AFTER function definitions) ===========================================

# Initialising ports for Anemometer and Rain gauge:
# GPIO 'portAne' set up as input for anemometer. It is pulled up to stop false signals.
GPIO.setup(portAne, GPIO.IN, GPIO.PUD_UP)
# GPIO 'portRain' set up as input for rain gauge. It is pulled up to stop false signals.
GPIO.setup(portRain, GPIO.IN, GPIO.PUD_UP)

# Setting up interrupts:

# The GPIO.add_event_detect() line below set things up so that when a falling edge is 
# detected on port 'portAne', regardless of whatever else is happening in the program, 
# the function "spinAne" will be run: i.e. setting up interrupt !!
GPIO.add_event_detect(portAne, GPIO.FALLING, callback=spinAne)

# The GPIO.add_event_detect() line below set things up so that when a falling edge is 
# detected on port 'portRain', regardless of whatever else is happening in the program, 
# the function "rainTipped" will be run: i.e. setting up interrupt !!
GPIO.add_event_detect(portRain, GPIO.FALLING, callback=rainTipped, bouncetime=1000)

# =======================================================================================================================================
# =========== Main program ==============================================================================================================

# Taking date and time
# dateNowStr = dtdt.now().strftime('%d.%m.%Y')
# timeNowStr = dtdt.now().strftime('%H:%M:%S')

# ---------------------------------------------------------------------------------------------------------------------------------------
try:
	# Take starting time for counting revs of anemometer
	timeStAne = time.time()			# current epoch time
	
	# ------------ Getting previous values from rrd databases(incl. max and min ) in case program is stopped and later restarted -----------------------------
	
	# Getting previous tiltRain value in case program is started anew
	# Setting tiltRain to previous value, when program is started anew
	tiltRain = int(prevMaxVal(rdbFile,'MAX',0,8640))		# Getting the max of 6 days worth of tiltRain data, starting 6 days ago, ending now
#	tiltRain = int(prevMaxVal(rdbFile,'MAX',0,57600))		# Getting the max of 40 days worth of tiltRain data, starting 40 days ago, ending now

	# Getting previous current rain duration value rainT0['cda'] in case program is started anew WITHIN 60 min <------------
	# Set rainT0['cda'] to previous value, when program is started anew
	rainT0['cda'] = prevMaxVal(ddbFile,'MAX',2,120)			# Getting the max of 120 min worth of rainT0['cda'] data, starting 120 min ago, ending now

	# Getting previous rain duration values to add up to rainT0['cye'] since beginning of year in case program is started anew
	dayCwe = dtdt.now().isoweekday()											# Returns day of week as integer (1 .. 7, 1 = Monday)
	dayCmo = dtdt.now().day														# Returns day of month as integer (1 .. 31)
	dayCye = dtdt.now().timetuple()[7]											# Returns day of year as integer (1 .. 366) (both these versions work)
	# dayCye = int(dtdt.now().strftime('%j'))									# Returns day of year as integer (1 .. 366) (both these versions work)
	# eT11 = int(time.mktime( (2017, 1, 1, 23, 0, 0, 0, 0, 0) ))				# Epoch time of 1.1.2017, 23:00:00 from time tuple
	eT11 = int(time.mktime( (dtdt.now().year, 1, 1, 22, 0, 0, 0, 0, 0) ))		# Epoch time of 1.1.(Current year), 22:00:00 from time tuple (MUST be BEFORE 23:00:00h because of summertime!!)
	# rainT0['cye'] = 0															# is already set to 0 further up
	for i in range(dayCye-1):
		fTime = eT11 + i*86400													# Adding 86400 sec  =  1 day with each loop
		fData = rrdtool.fetch('%s' %(ddbFile), 'MAX', '-s %s' %(fTime), '-e %s' %(fTime))		# Fetching 1 value of data from fTime (epoch time)
		if fData[2][0][2] is not None:
			rainT0['cye'] += fData[2][0][2]										# Adding up all daily values since 1.1.(current year)
#			print "............ i =", i,", Date and time =", time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(fTime))					# Check print
#			print "fData[2][0][2] =", fData[2][0][2]					# Check print
#			print "  rainT0['cye'] =", rainT0['cye']						# Check print
			if i >= dayCye - dayCmo:
				rainT0['cmo'] += fData[2][0][2]									# Adding up all daily values since beginning of current month
#				print "  rainT0['cmo'] =", rainT0['cmo']					# Check print: Accumulated data for rainT0Month till this date at 23:00:00
			if i >= dayCye - dayCwe:
				rainT0['cwe'] += fData[2][0][2]									# Adding up all daily values since beginning of current week
#				print "  rainT0['cwe'] =", rainT0['cwe']					# Check print: Accumulated data for rainT0Month till this date at 23:00:00
	rainT0['cwe'] += rainT0['cda']												# Adding today's current daily value rainT0['cda'] to rainT0['cwe']
	rainT0['cmo'] += rainT0['cda']												# Adding today's current daily value rainT0['cda'] to rainT0['cmo']
	rainT0['cye'] += rainT0['cda']												# Adding today's current daily value rainT0['cda'] to rainT0['cye']

	# Getting previous current sun duration value sunT1['cda'] in case program is started anew WITHIN 60 min <------------
	# Set sunT1['cda'] to previous value, when program is started anew
	sunT1['cda'] = prevMaxVal(ddbFile,'MAX',1,120)			# Getting the max of 120 min worth of sunT1['cda'] data, starting 120 min ago, ending now
	
	# Getting previous sun duration values to add up to sunT1['cye'] since beginning of year in case program is started anew
#	dayCwe = dtdt.now().isoweekday()											# Returns day of week as integer (1 .. 7, 1 = Monday)					# NOTE: Values taken from previous lines
#	dayCmo = dtdt.now().day														# Returns day of month as integer (1 .. 31)								# NOTE: Values taken from previous lines
#	dayCye = dtdt.now().timetuple()[7]											# Returns day of year as integer (1 .. 366) (both these versions work)	# NOTE: Values taken from previous lines
	# dayCye = int(dtdt.now().strftime('%j'))									# Returns day of year as integer (1 .. 366) (both these versions work)
	# eT11 = int(time.mktime( (2017, 1, 1, 23, 0, 0, 0, 0, 0) ))				# Epoch time of 1.1.2017, 23:00:00 from time tuple
#	eT11 = int(time.mktime( (dtdt.now().year, 1, 1, 22, 0, 0, 0, 0, 0) ))		# Epoch time of 1.1.(Current year), 22:00:00 from time tuple (MUST be BEFORE 23:00:00h because of summertime!!)	# NOTE: Values taken from previous lines
	# sunT1['cye'] = 0															# is already set to 0 further up
	for i in range(dayCye-1):
		fTime = eT11 + i*86400													# Adding 86400 sec  =  1 day with each loop
		fData = rrdtool.fetch('%s' %(ddbFile), 'MAX', '-s %s' %(fTime), '-e %s' %(fTime))		# Fetching 1 value of data from fTime (epoch time)
		if fData[2][0][1] is not None:
			sunT1['cye'] += fData[2][0][1]										# Adding up all daily values since 1.1.(current year)
#			print "............ i =", i,", Date and time =", time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(fTime))					# Check print
#			print "fData[2][0][1] =", fData[2][0][1]					# Check print
#			print "  sunT1['cye'] =", sunT1['cye']						# Check print
			if i >= dayCye - dayCmo:
				sunT1['cmo'] += fData[2][0][1]									# Adding up all daily values since beginning of current month
#				print "  sunT1['cmo'] =", sunT1['cmo']					# Check print: Accumulated data for sunT1Month till this date at 23:00:00
			if i >= dayCye - dayCwe:
				sunT1['cwe'] += fData[2][0][1]									# Adding up all daily values since beginning of current week
#				print "  sunT1['cwe'] =", sunT1['cwe']					# Check print: Accumulated data for sunT1Month till this date at 23:00:00
	sunT1['cwe'] += sunT1['cda']												# Adding today's current daily value sunT1['cda'] to sunT1['cwe']
	sunT1['cmo'] += sunT1['cda']												# Adding today's current daily value sunT1['cda'] to sunT1['cmo']
	sunT1['cye'] += sunT1['cda']												# Adding today's current daily value sunT1['cda'] to sunT1['cye']

	# Getting previous max temp value in case program is started anew WITHIN 120 min <------------
	# Set airTemp0['max'] to previous value, when program is started anew
	# Set tAirTemp0['max'] to previous value, when program is started anew		
	airTemp0['max'] = prevMaxVal(adbFile,'MAX',1,120)		# Getting the max of 120 min worth of airTemp0['max'] data, starting 120 min ago, ending now
	tAirTemp0['max'] = prevMaxVal(xdbFile,'MAX',1,120)		# Getting the max of 120 min worth of tAirTemp0['max'] data, starting 120 min ago, ending now

	# Getting previous max pres value in case program is started anew WITHIN 120 min <------------
	# Set airPres0['max'] to previous value, when program is started anew
	# Set tAirPres0['max'] to previous value, when program is started anew		
#	airPres0['max'] = prevMaxVal(adbFile,'MAX',6,120)		# Getting the max of 120 min worth of airPres0['max'] data, starting 120 min ago, ending now
#	tAirPres0['max'] = prevMaxVal(xdbFile,'MAX',3,120)		# Getting the max of 120 min worth of tAirPres0['max'] data, starting 120 min ago, ending now

	# Getting previous max pres value in case program is started anew WITHIN 120 min <------------
	# Set airPres3['max'] to previous value, when program is started anew
	# Set tAirPres3['max'] to previous value, when program is started anew		
	airPres3['max'] = prevMaxVal(idbFile,'MAX',5,120)		# Getting the max of 120 min worth of airPres3['max'] data, starting 120 min ago, ending now
	tAirPres3['max'] = prevMaxVal(xdbFile,'MAX',3,120)		# Getting the max of 120 min worth of tAirPres3['max'] data, starting 120 min ago, ending now

	# Getting previous max humi value in case program is started anew WITHIN 120 min <------------
	# Set airHumi0['max'] to previous value, when program is started anew
	# Set tAirHumi0['max'] to previous value, when program is started anew		
	airHumi0['max'] = prevMaxVal(adbFile,'MAX',11,120)		# Getting the max of 120 min worth of airHumi0['max'] data, starting 120 min ago, ending now
	tAirHumi0['max'] = prevMaxVal(xdbFile,'MAX',5,120)		# Getting the max of 120 min worth of tAirHumi0['max'] data, starting 120 min ago, ending now

	# Getting previous max wind speed value in case program is started anew WITHIN 120 min <------------
	# Set airSpeed['mgt'] to previous value, when program is started anew
	# Set tAirSpeed['max'] to previous value, when program is started anew		
	airSpeed['mgt'] = prevMaxVal(adbFile,'MAX',16,120)		# Getting the max of 120 min worth of airSpeed['mgt'] data, starting 120 min ago, ending now
	tAirSpeed['max'] = prevMaxVal(xdbFile,'MAX',7,120)		# Getting the max of 120 min worth of tAirSpeed['max'] data, starting 120 min ago, ending now

	# Getting previous max flux value in case program is started anew WITHIN 120 min <------------
	# Set solFlux1['max'] to previous value, when program is started anew
	# Set tSolFlux1['max'] to previous value, when program is started anew		
	solFlux1['max'] = prevMaxVal(sdbFile,'MAX',3,120)		# Getting the max of 120 min worth of solFlux1['max'] data, starting 120 min ago, ending now
	tSolFlux1['max'] = prevMaxVal(xdbFile,'MAX',9,120)		# Getting the max of 120 min worth of tSolFlux1['max'] data, starting 120 min ago, ending now

	# Getting previous min temp value in case program is started anew WITHIN 120 min <------------
	# Set airTemp0['min'] to previous value, when program is started anew
	# Set tAirTemp0['min'] to previous value, when program is started anew		
	airTemp0['min'] = prevMinVal(adbFile,'MIN',2,120)		# Getting the min of 120 min worth of airTemp0['min'] data, starting 120 min ago, ending now
	tAirTemp0['min'] = prevMaxVal(ndbFile,'MIN',1,120)		# Getting the max of 120 min worth of tAirTemp0['min'] data, starting 120 min ago, ending now

	# Getting previous min pres value in case program is started anew WITHIN 120 min <------------
	# Set airPres0['min'] to previous value, when program is started anew
	# Set tAirPres0['min'] to previous value, when program is started anew		
#	airPres0['min'] = prevMinVal(adbFile,'MIN',7,120)		# Getting the min of 120 min worth of airPres0['min'] data, starting 120 min ago, ending now
#	tAirPres0['min'] = prevMaxVal(ndbFile,'MIN',3,120)		# Getting the max of 120 min worth of tAirPres0['min'] data, starting 120 min ago, ending now

	# Getting previous min pres value in case program is started anew WITHIN 120 min <------------
	# Set airPres3['min'] to previous value, when program is started anew
	# Set tAirPres3['min'] to previous value, when program is started anew		
	airPres3['min'] = prevMinVal(idbFile,'MIN',6,120)		# Getting the min of 120 min worth of airPres3['min'] data, starting 120 min ago, ending now
	tAirPres3['min'] = prevMaxVal(ndbFile,'MIN',3,120)		# Getting the max of 120 min worth of tAirPres3['min'] data, starting 120 min ago, ending now

	# Getting previous min humi value in case program is started anew WITHIN 120 min <------------
	# Set airHumi0['min'] to previous value, when program is started anew
	# Set tAirHumi0['min'] to previous value, when program is started anew		
	airHumi0['min'] = prevMinVal(adbFile,'MIN',12,120)		# Getting the min of 120 min worth of airHumi0['min'] data, starting 120 min ago, ending now
	tAirHumi0['min'] = prevMaxVal(ndbFile,'MIN',5,120)		# Getting the max of 120 min worth of tAirHumi0['min'] data, starting 120 min ago, ending now

	# Getting previous min wind speed value in case program is started anew WITHIN 120 min <------------
	# Set airSpeed['min'] to previous value, when program is started anew
	# Set tAirSpeed['min'] to previous value, when program is started anew		
	airSpeed['min'] = prevMinVal(ndbFile,'MIN',6,120)		# Getting the min of 120 min worth of airSpeed['min'] data, starting 120 min ago, ending now
	tAirSpeed['min'] = prevMaxVal(ndbFile,'MIN',7,120)		# Getting the max of 120 min worth of tAirSpeed['min'] data, starting 120 min ago, ending now

	# Getting previous min flux value in case program is started anew WITHIN 120 min <------------
	# Set solFlux1['min'] to previous value, when program is started anew
	# Set tSolFlux1['min'] to previous value, when program is started anew		
	solFlux1['min'] = prevMinVal(ndbFile,'MIN',8,120)		# Getting the min of 120 min worth of solFlux1['min'] data, starting 120 min ago, ending now
	tSolFlux1['min'] = prevMaxVal(ndbFile,'MIN',9,120)		# Getting the max of 120 min worth of tSolFlux1['min'] data, starting 120 min ago, ending now

	# ------------ Done getting previous values in case program is stopped and restarted -----------------------------

# ============ Main loop ================================================================================================================
	while True:

# ------------ Taking date and time values ------------------------------------------------------------------------------------------------

		# Setting start time of main loop
		loopStart = time.time()			# epoch time

		# Determine current day to determine end of day for max and min values
		timePrev['ho'] = timeCur['ho']				   # (end of hour only used for testing!)
		print ("> timePrev['ho'] = {0:4d}, timeCur['ho'] = {1:4d}".format(timePrev['ho'], timeCur['ho']))				   # (used for testing only)
		timePrev['da'] = timeCur['da']
		print ("> timePrev['da'] = {0:4d}, timeCur['da'] = {1:4d}".format(timePrev['da'], timeCur['da']))
		timePrev['we'] = timeCur['we']
		print ("> timePrev['we'] = {0:4d}, timeCur['we'] = {1:4d}".format(timePrev['we'], timeCur['we']))				   # (used for testing only)
		timePrev['mo'] = timeCur['mo']
		print ("> timePrev['mo'] = {0:4d}, timeCur['mo'] = {1:4d}".format(timePrev['mo'], timeCur['mo']))
		timePrev['ye'] = timeCur['ye']
		print ("> timePrev['ye'] = {0:4d}, timeCur['ye'] = {1:4d}".format(timePrev['ye'], timeCur['ye']))

		timeCur['ho'] = dtdt.now().hour					# getting current hour of day
		print ("> timePrev['ho'] = {0:4d}, timeCur['ho'] = {1:4d}".format(timePrev['ho'], timeCur['ho']))				   # (used for testing only)
		timeCur['da'] = dtdt.now().day					# getting current day of week (1 = Monday, ...,7 = Sunday)
		print ("> timePrev['da'] = {0:4d}, timeCur['da'] = {1:4d}".format(timePrev['da'], timeCur['da']))
		timeCur['we'] = dtdt.now().isocalendar()[1]		# getting current week of year
		print ("> timePrev['we'] = {0:4d}, timeCur['we'] = {1:4d}".format(timePrev['we'], timeCur['we']))				   # (used for testing only)
		timeCur['mo'] = dtdt.now().month				# getting current month of year
		print ("> timePrev['mo'] = {0:4d}, timeCur['mo'] = {1:4d}".format(timePrev['mo'], timeCur['mo']))
		timeCur['ye'] = dtdt.now().year					# getting current year
		print ("> timePrev['ye'] = {0:4d}, timeCur['ye'] = {1:4d}".format(timePrev['ye'], timeCur['ye']))

# ------------ Taking sensor readings and calculating max and min values --------------------------------------------------------------

		# Reading air values -----------------------------------------------------------------------------------------------------------

		# Reading temperature from DS18B20 Nr. 11 in Stevenson screen (Must stand before Pres measurement)
		airTemp0['cur'] = readTemperature(ds18b20File0)
		print('DS18B20-11 temperature = %3.2f') %(airTemp0['cur'])

		# Calculating max and min temperature values
		if timeCur['da'] != timePrev['da']:					# reset airTemp0['max'] to = 0.0 and airTemp0['min'] to a high value at 24:00:00h (midnight)
			airTemp0['max'] = -90.0
			airTemp0['min'] = 90.0
		if airTemp0['cur'] > airTemp0['max']:				# set new value for airTemp0['max'] if applicable
			airTemp0['max'] = airTemp0['cur']
			tAirTemp0['max'] = time.time()					# time.strftime('%H:%M', time.localtime(time.time()))
		if airTemp0['cur'] < airTemp0['min']:				# set new value for airTemp0['min'] if applicable
			airTemp0['min'] = airTemp0['cur']
			tAirTemp0['min'] = time.time()
#		airTemp0['max'] = 3.0								# [*C], FOR TESTING PURPOSES ONLY Testing Testing Testing Testing Testing Testing Testing
#		airTemp0['min'] = - 1.0								# [*C], FOR TESTING PURPOSES ONLY Testing Testing Testing Testing Testing Testing Testing

		# Reading pressure and temperature and humidity on outside BME280 (Stevenson screen i.e. outside)
		try:
			pr, airTemp1['cur'], airHumi0['cur'] = readPrTeHu(chanTcaBme1)
			airPres0['qfe'] = pr/100.0
#			airPres0['qff'] = airPres0['qfe'] * (1.0 + h1 * rho / (273.15 + airTemp0['cur']) ) ** (0.03416 / rho)	# Pressure reduced to sea level using formula using outside temperature from DS18B20
#			airPres0['qff'] = airPres0['qfe'] * (1.0 + h1 * rho / (273.15 + airTemp1['cur']) ) ** (0.03416 / rho)	# Pressure reduced to sea level using formula using outside temperature from BME280

#			airPres0['qff'] = presReduction1(airPres0['qfe'], airTemp0['cur'], h1)		# Function using swissmeteo formula
			airPres0['qff'] = presReduction2(airPres0['qfe'], airTemp0['cur'], airHumi0['cur'], h1)

		except IOError:
			pass

		# Calculating max and min pressure values
		if timeCur['da'] != timePrev['da']:					# reset airPres0['max'] to = 0.0 and airPres0['min'] to high value at 24:00:00h (midnight)
			airPres0['max'] = 0.0
			airPres0['min'] = 1050.0
		if airPres0['qff'] > airPres0['max']:				# set new value for airPres0['max'] if applicable
			airPres0['max'] = airPres0['qff']
			tAirPres0['max'] = time.time()
		if airPres0['qff'] < airPres0['min']:				# set new value for airPres0['min'] if applicable
			airPres0['min'] = airPres0['qff']
			tAirPres0['min'] = time.time()
#		airPres0['max'] = 1031.0							# [hPa], FOR TESTING PURPOSES ONLY Testing Testing Testing Testing Testing Testing Testing
#		airPres0['min'] = 1005.0							# [hPa], FOR TESTING PURPOSES ONLY Testing Testing Testing Testing Testing Testing Testing

		# Calculating max and min humidity values
		if timeCur['da'] != timePrev['da']:					# reset airHumi0['max'] to = 0.0 and airHumi0['min'] to a high value at 24:00:00h (midnight)
			airHumi0['max'] = 0.0
			airHumi0['min'] = 100.0
		if airHumi0['cur'] > airHumi0['max']:				# set new value for airHumi0['max'] if applicable
			airHumi0['max'] = airHumi0['cur']
			tAirHumi0['max'] = time.time()
		if airHumi0['cur'] < airHumi0['min']:				# set new value for airHumi0['min'] if applicable
			airHumi0['min'] = airHumi0['cur']
			tAirHumi0['min'] = time.time()
#		airHumi0['max'] = 97.0								# [%], FOR TESTING PURPOSES ONLY Testing Testing Testing Testing Testing Testing Testing
#		airHumi0['min'] = 37.0								# [%], FOR TESTING PURPOSES ONLY Testing Testing Testing Testing Testing Testing Testing

		print('BME280 pressure   = %4.2f') %(airPres0['qfe'])
		print('Sealevel pressure = %4.2f calculated with formula') %(airPres0['qff'])
		print('BME280 temperature = %3.2f') %(airTemp1['cur'])
		print('BME280 humidity = %3.2f') %(airHumi0['cur'])

		# Reading humidity and temperature on DHT22			# NOTE: Presently DHT22 humidity sensor is NOT active
#		airHumi1['cur'],airTemp1['cur'] = readHumTemp()
#		print('DHT22 temperature = %3.2f') %(airTemp1['cur'])
#		print('DHT22 humidity = %3.2f') %(airHumi1['cur'])

		# Calculating dew point airDew['cur'] from temperature airTemp0['cur'] and relative humidity airHumi0['cur']
		# Using formula given by "Sensirion Application Note Dew-point Calculation" (Sensirion_Dewpoint_Calculation_Humidity_Sensor_E.pdf)
		hDew = logE(airHumi0['cur']/100.0) + 17.62*airTemp0['cur']/(243.12 + airTemp0['cur'])
		airDew['cur'] = 243.12*hDew / (17.62 - hDew)

		# Reading anemometer for wind speed:
		# Take actual time for counting revs of anemometer
		timeAne = time.time()			# current epoch time
		# Take actual time duration for counting revs of anemometer
		timeDeAne = timeAne - timeStAne
		# If time duration exceeds preset time durAne then calculate windspeed and start new rev count, else carry on counting revs
#		if timeCur['ho'] != timePrev['ho']:					# reset airSpeed['mgt'] to = 0.0 at change of hour (used only for testing to simulate midnight)
		if timeCur['da'] != timePrev['da']:					# reset airSpeed['mgt'] to = 0.0 at 24:00:00h (midnight)
			airSpeed['mgt'] = 0.0
		if timeDeAne > durAne:
			airSpeed['cur'] = speedAne(revAne,timeDeAne)	# Get new value for airSpeed['cur']
			# Calculating max and min air speed values
			if airSpeed['cur'] > airSpeed['mgt']:			# set new value for airSpeed['mgt'] if applicable
				airSpeed['mgt'] = airSpeed['cur']
				tAirSpeed['max'] = time.time()
			print ('Windspeed: ')
			print ('> Counts ={0:3d}, time = {1:.3f} s, Speed = {2:.3f} km/h,  Max = {3:.3f} km/h at {4:.3f}'.format(revAne, timeDeAne, airSpeed['cur'], airSpeed['mgt'], tAirSpeed['max']))
			revAne = 0
			# Reset starting time for counting revs for anemometer
			timeStAne = time.time()			# current epoch time

		# Reading wind vane for wind direction:
		# Read ADC valus for vane
		uVane, dirNew = vaneDirection(chVane, uSup, fCorr)
		# Print ADC values for vane when direction has changed
		if dirNew != airDir:
			print('New wind direction: ')
			print('> uVane= {0:.3f}, dirNew = {1:3.1f}'.format(uVane, dirNew))
		airDir = dirNew
		# Pause for half a second.
		time.sleep(0.5)

		# Reading rain values -------------------------------------------------------------------------------------------

		# Reading rain gauge rrrrrrrrrrrrrrrrrrrrrrrrrrrrrr
		rainFall['acc'] = tiltRain * mmPerTilt				# accumulated rainFall since beginning of year till end of year

		print ('Rainfall: ')
		print ('> Tilts = {0:3d}, Rainfall = {1:.3f} mm'.format(tiltRain, rainFall['acc']))

		# Reading rain drop sensor values
		digitalRD, analogRD = rainDrops(portRD,chRD)			# Reading digital and analogue values DO and AO via MCP3008 ADC of rain drop sensor
		print ('> Raindrops  DO = {0:2d},  AO = {1:.4f}'.format(digitalRD, analogRD))

		# Resetting and calculating rain durations rainT0['xxx']  <<<<<<<<<<<<<<<<<<<<<<<<<<<<<
		if timeCur['da'] != timePrev['da']:
			rainT0['cda'] = 0.0								# resetting rainT0['cda'] to = 0.0 at 24:00:00h (midnight) <<<<<<<<<<<<<<<<<<<<<<<<<<<<<
		if timeCur['we'] != timePrev['we']:
			rainT0['cwe'] = 0.0								# resetting rainT0['cwe'] to = 0.0 at change of week <<<<<<<<<<<<<<<<<<<<<<<<<<<<<
		if timeCur['mo'] != timePrev['mo']:
			rainT0['cmo'] = 0.0								# resetting rainT0['cmo'] to = 0.0 at change of month <<<<<<<<<<<<<<<<<<<<<<<<<<<<<
		if timeCur['ye'] != timePrev['ye']:
			rainT0['cye'] = 0.0								# resetting srainT0['cye'] to = 0.0 at change of year <<<<<<<<<<<<<<<<<<<<<<<<<<<<<

		# Calculating rain duration
		if digitalRD <= 0:
			rainT0['cda'] += effLoopTime					# accumulating daily sunshine duration rainT0['cda']  <<<<<<<<<<<<<<<<<<<<<<<<<<<<<
			rainT0['cwe'] += effLoopTime					# accumulating weekly sunshine duration rainT0['cwe']  <<<<<<<<<<<<<<<<<<<<<<<<<<<<<
			rainT0['cmo'] += effLoopTime					# accumulating monthly sunshine duration rainT0['cmo']  <<<<<<<<<<<<<<<<<<<<<<<<<<<<<
			rainT0['cye'] += effLoopTime					# accumulating annual sunshine duration rainT0['cye']  <<<<<<<<<<<<<<<<<<<<<<<<<<<<<
		print ("> rainT0['cda'] = {0:.2f}".format(rainT0['cda']))

		# Reading system (inbox) values ----------------------------------------------------------------------------------

		# Reading CPU temperature
		cpuTemp20['cur'] = getCpuTemperature()

		# Calculating max and min CPU temp values
		if timeCur['da'] != timePrev['da']:					# resetting airSpeed['mgt'] to = 0.0 at 24:00:00h (midnight)
			cpuTemp20['max'] = -90.0
			cpuTemp20['min'] = 90.0
		if cpuTemp20['cur'] > cpuTemp20['max']:				# setting new value for cpuTemp20['max'] if applicable
			cpuTemp20['max'] = cpuTemp20['cur']
			tcpuTemp20['max'] = time.time()
		if cpuTemp20['cur'] < cpuTemp20['min']:				# setting new value for cpuTemp20['min'] if applicable
			cpuTemp20['min'] = cpuTemp20['cur']
			tcpuTemp20['min'] = time.time()
#		cpuTemp20['max'] = 24.0								# [*C], FOR TESTING PURPOSES ONLY Testing Testing Testing Testing Testing Testing Testing
#		cpuTemp20['min'] = 21.0								# [*C], FOR TESTING PURPOSES ONLY Testing Testing Testing Testing Testing Testing Testing

		print('CPU temperature = %3.2f') %(cpuTemp20['cur'])

		# Measuring temperature from DS18B20 Nr. 2 inside box (inbox) on connector print
		airTemp2['cur'] = readTemperature(ds18b20File2)

		# Calculating max and min inbox temperature values
		if timeCur['da'] != timePrev['da']:					# resetting airTemp2['max'] to = 0.0 at 24:00:00h (midnight)
			airTemp2['max'] = -90.0
			airTemp2['min'] = 90.0
		if airTemp2['cur'] > airTemp2['max']:				# setting new value for airTemp2['max'] if applicable
			airTemp2['max'] = airTemp2['cur']
			tAirTemp2['max'] = time.time()
		if airTemp2['cur'] < airTemp2['min']:				# setting new value for airTemp2['min'] if applicable
			airTemp2['min'] = airTemp2['cur']
			tAirTemp2['min'] = time.time()
#		airTemp2['max'] = 5.0								# [*C], FOR TESTING PURPOSES ONLY Testing Testing Testing Testing Testing Testing Testing
#		airTemp2['min'] = 1.0								# [*C], FOR TESTING PURPOSES ONLY Testing Testing Testing Testing Testing Testing Testing

		print('DS18B20-2 temperature = %3.2f') %(airTemp2['cur'])

		# Reading inside values ----------------------------------------------------------------------------------

		# Measuring temperature from DS18B20 Nr. 3 inside shack (outside box)
		airTemp3['cur'] = readTemperature(ds18b20File3)

		# Calculating max and min inside temperature values
		if timeCur['da'] != timePrev['da']:					# resetting airTemp3['max'] to = 0.0 at 24:00:00h (midnight)
			airTemp3['max'] = -90.0
			airTemp3['min'] = 90.0
		if airTemp3['cur'] > airTemp3['max']:				# setting new value for airTemp3['max'] if applicable
			airTemp3['max'] = airTemp3['cur']
			tAirTemp3['max'] = time.time()
		if airTemp3['cur'] < airTemp3['min']:				# setting new value for airTemp3['min'] if applicable
			airTemp3['min'] = airTemp3['cur']
			tAirTemp3['min'] = time.time()
#		airTemp3['max'] = 5.0								# [*C], FOR TESTING PURPOSES ONLY Testing Testing Testing Testing Testing Testing Testing
#		airTemp3['min'] = 1.0								# [*C], FOR TESTING PURPOSES ONLY Testing Testing Testing Testing Testing Testing Testing

		print('DS18B20-3 temperature = %3.2f') %(airTemp3['cur'])		# Check printing

		# Reading pressure and temperature on inside (inbox) BMP280 
		try:
			pr, te = readPrTe(chanTcaBmp3)
			airPres3['qfe'] = pr/100.0							# Making hPa

#			airPres3['qff'] = airPres3['qfe'] * (1.0 + h3 * rho / (273.15 + airTemp0['cur']) ) ** (0.03416 / rho)	# Pressure reduced to sea level using formula with outside temp from DS18B20 (korrekt)
#			airPres3['qff'] = airPres3['qfe'] * (1.0 + h3 * rho / (273.15 + airTemp2['cur']) ) ** (0.03416 / rho)	# Pressure reduced to sea level using formula with inbox temp from DS18B20
#			airPres3['qff'] = airPres3['qfe'] * (1.0 + h3 * rho / (273.15 + te) ) ** (0.03416 / rho)				# Pressure reduced to sea level using formula with inbox temp from BMP280
#			airPres3['qff'] = airPres3['qfe'] * (1.0 + h3 * rho / (273.15 + airTemp3['cur']) ) ** (0.03416 / rho)	# Pressure reduced to sea level using formula with inside temp from DS18B20

#			airPres3['qff'] = presReduction1(airPres3['qfe'], airTemp0['cur'], h3)		# Function using swissmeteo formula
			airPres3['qff'] = presReduction2(airPres3['qfe'], airTemp0['cur'], airHumi0['cur'], h3)

		except IOError:
			pass

		# Calculating max and min inside pressure values
		if timeCur['da'] != timePrev['da']:					# reset airPres3['max'] to = 0.0 and airPres3['min'] to high value at 24:00:00h (midnight)
			airPres3['max'] = 0.0
			airPres3['min'] = 1050.0
		if airPres3['qff'] > airPres3['max']:				# set new value for airPres3['max'] if applicable
			airPres3['max'] = airPres3['qff']
			tAirPres3['max'] = time.time()
		if airPres3['qff'] < airPres3['min']:				# set new value for airPres3['min'] if applicable
			airPres3['min'] = airPres3['qff']
			tAirPres3['min'] = time.time()

		print("Inbox temp te   = %4.2f") %(te)							# Check printing
		print("airPres3['qfe'] = %4.2f") %(airPres3['qfe'])				# Check printing
		print("airPres3['qff'] = %4.2f") %(airPres3['qff'])				# Check printing

		# Reading solar values and calculating sunshine duration -------------------------------------------------------------------

		# Reading GA1A12S202-0 for Illuminance
#		solFlux0['cur'] = readGA(chGA0, uSup)
		solFlux0['cur'] = 0.0										##### NOTE: THIS IS TO TAKE NO READING, AS SENSOR SEEMS DAMAGED  ######################
		solFlux0['cur'] = int(solFlux0['cur']*1000.0*100.0+0.5)/100.0		# Make rounded millivolts mV

		# Resetting sunT0, max and min values at midnight and calculating max and min solar flux1 values
		if timeCur['da'] != timePrev['da']:					# resetting solFlux0['max'] to = 0.0 at 24:00:00h (midnight)
			solFlux0['max'] = 0.0
			solFlux0['min'] = 100000.0
			sunT0 = 0.0										# NOT used right now
		if solFlux0['cur'] > solFlux0['max']:				# setting new value for solFlux0['max'] if applicable
			solFlux0['max'] = solFlux0['cur']
			tSolFlux0['max'] = time.time()
		if solFlux0['cur'] < solFlux0['min']:				# setting new value for solFlux0['min'] if applicable
			solFlux0['min'] = solFlux0['cur']
			tSolFlux0['min'] = time.time()

		print ("solFlux0['cur']  = %5.2f mV") %(solFlux0['cur'])
		luxGA0 = 10**( solFlux0['cur'] / 680.0)								# Make Lux:   E[Lux] = 10^(E[mV] / 680) (JUST FOR TESTING)
		print ('luxGA0           = %5.2f Lux') %(luxGA0)

		# Reading GA1A12S202-1 for Illuminance
		solFlux1['cur'] = readGA(chGA1, uSup)
		solFlux1['cur'] = int(solFlux1['cur']*1000.0*100.0+0.5)/100.0		# Make rounded millivolts mV

		# Resetting sunT1['cda'], max and min values of solFlux1 at midnight and calculating max and min solFlux1 values
		if timeCur['da'] != timePrev['da']:
			solFlux1['max'] = 0.0							# resetting solFlux1['max'] to = 0.0 at 24:00:00h (midnight)
			solFlux1['min'] = 100000.0						# resetting solFlux1['min'] to = a high value at 24:00:00h (midnight)
			sunT1['cda'] = 0.0								# resetting sunT1['cda'] to = 0.0 at 24:00:00h (midnight) <<<<<<<<<<<<<<<<<<<<<<<<<<<<<
		if solFlux1['cur'] > solFlux1['max']:				# setting new value for solFlux1['max'] if applicable
			solFlux1['max'] = solFlux1['cur']
			tSolFlux1['max'] = time.time()
		if solFlux1['cur'] < solFlux1['min']:				# setting new value for solFlux1['min'] if applicable
			solFlux1['min'] = solFlux1['cur']
			tSolFlux1['min'] = time.time()

		print ("solFlux1['cur']  = %5.2f mV") %(solFlux1['cur'])
		luxGA1 = 10**( solFlux1['cur'] / 680.0)								# Make Lux:   E[Lux] = 10^(E[mV] / 680) (JUST FOR TESTING)
		print ('luxGA1           = %5.2f Lux') %(luxGA1)

		# Resetting and calculating sunshine durations sunT1['xxx']  <<<<<<<<<<<<<<<<<<<<<<<<<<<<<
		if timeCur['we'] != timePrev['we']:
			sunT1['cwe'] = 0.0								# resetting sunT1['cwe'] to = 0.0 at change of week <<<<<<<<<<<<<<<<<<<<<<<<<<<<<
		if timeCur['mo'] != timePrev['mo']:
			sunT1['cmo'] = 0.0								# resetting sunT1['cmo'] to = 0.0 at change of month <<<<<<<<<<<<<<<<<<<<<<<<<<<<<
		if timeCur['ye'] != timePrev['ye']:
			sunT1['cye'] = 0.0								# resetting sunT1['cye'] to = 0.0 at change of year <<<<<<<<<<<<<<<<<<<<<<<<<<<<<

		# Setting threshold sunThresh in [Lux] for illuminance to measure sunshine duration depending on current month
		if timeCur['mo'] <= 2 or timeCur['mo'] >= 11:
			sunThresh = 8000.0
		elif timeCur['mo'] <= 4 or timeCur['mo'] >= 9:
			sunThresh = 8500.0
		else:
			sunThresh = 9000.0

		# Accumulating sunshine time by adding up time of each program loop if illuminance > sunThresh
		if solFlux1['cur'] > logE(sunThresh)*680.0/lNat10:		# NOTE: threshold for solFlux1 must be in mV; adding eff loop time to sunshine duration values
			sunT1['cda'] += effLoopTime							# accumulating daily sunshine duration sunT1['cda']  <<<<<<<<<<<<<<<<<<<<<<<<<<<<<
			sunT1['cwe'] += effLoopTime							# accumulating weekly sunshine duration sunT1['cwe']  <<<<<<<<<<<<<<<<<<<<<<<<<<<<<
			sunT1['cmo'] += effLoopTime							# accumulating monthly sunshine duration sunT1['cmo']  <<<<<<<<<<<<<<<<<<<<<<<<<<<<<
			sunT1['cye'] += effLoopTime							# accumulating annual sunshine duration sunT1['cye']  <<<<<<<<<<<<<<<<<<<<<<<<<<<<<
			# print ("sunT1['cda']     =          %6d min  %2d sec") %(sunT1['cda']//60.0, sunT1['cda']%60.0)		# Check printing:  Floor division and modulo (remainder)
			# print ("sunT1['cda']     = %4d hours  %2d min  %2d sec") %(sunT1['cda']//3600.0, (sunT1['cda']%3600.0)//60.0, sunT1['cda']%60.0)		# Check printing:  Floor division and modulo (remainder)
			# print ("sunT1['cwe']     =          %6d min  %2d sec") %(sunT1['cwe']//60.0, sunT1['cwe']%60.0)		# Check printing:  Floor division and modulo (remainder)
			# print ("sunT1['cwe']     = %4d hours  %2d min  %2d sec") %(sunT1['cwe']//3600.0, (sunT1['cwe']%3600.0)//60.0, sunT1['cwe']%60.0)		# Check printing:  Floor division and modulo (remainder)
			# print ("sunT1['cmo']     =          %6d min  %2d sec") %(sunT1['cmo']//60.0, sunT1['cmo']%60.0)		# Check printing:  Floor division and modulo (remainder)
			# print ("sunT1['cmo']     = %4d hours  %2d min  %2d sec") %(sunT1['cmo']//3600.0, (sunT1['cmo']%3600.0)//60.0, sunT1['cmo']%60.0)		# Check printing:  Floor division and modulo (remainder)
			# print ("sunT1['cye']     =          %6d min  %2d sec") %(sunT1['cye']//60.0, sunT1['cye']%60.0)		# Check printing:  Floor division and modulo (remainder)
			# print ("sunT1['cye']     = %4d hours  %2d min  %2d sec") %(sunT1['cye']//3600.0, (sunT1['cye']%3600.0)//60.0, sunT1['cye']%60.0)		# Check printing:  Floor division and modulo (remainder)

		# Reading LDR for Brightness		(NOT USED NOW)
#		solFlux2['cur'], rLDR = readLDR(chLDR, uSup, rOne)
#		solFlux2['cur'] = int(solFlux2['cur']*1000.0*100.0+0.5)/100.0
#		print ("solFlux2['cur'] = %5.2f mV            rLDR = %5.2f Ohm") %(solFlux2['cur'], rLDR)
		
		solFlux2['cur'] = 1.5 								#[mV], FOR TESTING PURPOSES ONLY Testing Testing Testing Testing Testing Testing Testing
		solFlux2['max'] = 1.9 								#[mV], FOR TESTING PURPOSES ONLY Testing Testing Testing Testing Testing Testing Testing

		# Reading ML8511 UV sensor
		solUvi['cur'] = 23.46								# FOR TESTING PURPOSES ONLY Testing Testing Testing Testing Testing Testing Testing
		solUvi['max'] = 32.92 								# FOR TESTING PURPOSES ONLY Testing Testing Testing Testing Testing Testing Testing
		solUvi['min'] = 0.12 								# FOR TESTING PURPOSES ONLY Testing Testing Testing Testing Testing Testing Testing

		# Reading solar panel voltage and solar panel current
		# Reading ACS712		(NOT IN USE NOW)
#		uACS = readACS (chACS, uSup, r1, r2)
# 		solPcurr['cur'] = abs(0.5*uPlus - uACS) * 14.8		# Sensitivity of ACS712 is 14.8 Amp/Volt 
# 		solPcurr['cur'] = uACS * 14.8						# FOR TESTING PURPOSES ONLY Testing Testing Testing Testing Testing Testing Testing
#		print ("uACS           = %5.2f V ") %(uACS)

 		solPvolt['cur'] = 13.43								# FOR TESTING PURPOSES ONLY Testing Testing Testing Testing Testing Testing Testing
 		solPvolt['max'] = 15.32								# FOR TESTING PURPOSES ONLY Testing Testing Testing Testing Testing Testing Testing
 		solPcurr['cur'] = 1.23								# FOR TESTING PURPOSES ONLY Testing Testing Testing Testing Testing Testing Testing
 		solPcurr['max'] = 1.78								# FOR TESTING PURPOSES ONLY Testing Testing Testing Testing Testing Testing Testing
#		print ("solPcurr['cur'] = %5.2f A ") %(solPcurr['cur'])		# Test printing
		
		# Reading battery voltage and battery current
		solBvolt['cur'] = 12.05								# FOR TESTING PURPOSES ONLY Testing Testing Testing Testing Testing Testing Testing
		solBvolt['max'] = 12.62								# FOR TESTING PURPOSES ONLY Testing Testing Testing Testing Testing Testing Testing
		solBcurr['cur'] = 0.67								# FOR TESTING PURPOSES ONLY Testing Testing Testing Testing Testing Testing Testing
		solBcurr['max'] = 1.23								# FOR TESTING PURPOSES ONLY Testing Testing Testing Testing Testing Testing Testing

# ------------ Updating rrd databases ----------------------------------------------------------------------------------------------------------------------

		# Updating air values
		rrdtool.update('%s' %(adbFile), 'N:%s:%s:%s:%s:%s:%s:%s:%s:%s:%s:%s:%s:%s:%s:%s:%s:%s:%s' %(airTemp0['cur'], airTemp0['max'], airTemp0['min'], airTemp1['cur'], airPres0['qfe'], airPres0['qff'], airPres0['max'], airPres0['min'], 'U', 'U', airHumi0['cur'], airHumi0['max'], airHumi0['min'], 'U', airDew['cur'], airSpeed['cur'], airSpeed['mgt'], airDir))

		# Updating rain values
		rrdtool.update('%s' %(rdbFile), 'N:%s:%s:%s:%s' %(tiltRain, rainFall['acc'],digitalRD, analogRD))

		# Updating system values
		rrdtool.update('%s' %(ydbFile), 'N:%s:%s:%s:%s:%s:%s' %(cpuTemp20['cur'], cpuTemp20['max'], cpuTemp20['min'], airTemp2['cur'], airTemp2['max'], airTemp2['min']))

		# Updating inside values
		rrdtool.update('%s' %(idbFile), 'N:%s:%s:%s:%s:%s:%s:%s:%s:%s:%s' %(airTemp3['cur'], airTemp3['max'], airTemp3['min'], airPres3['qfe'], airPres3['qff'], airPres3['max'], airPres3['min'], 'U', 'U', 'U'))

		# Updating solar values
#		rrdtool.update('%s' %(sdbFile), 'N:%s:%s:%s:%s:%s:%s:%s:%s:%s:%s:%s:%s:%s:%s:%s:%s' %(solFlux0['cur'], solFlux0['max'], solFlux1['cur'], solFlux1['max'], 'U', 'U', 'U', 'U', 'U', 'U', 'U', 'U', 'U', 'U', 'U', 'U'))
		rrdtool.update('%s' %(sdbFile), 'N:%s:%s:%s:%s:%s:%s:%s:%s:%s:%s:%s:%s:%s:%s:%s:%s' %('U', 'U', solFlux1['cur'], solFlux1['max'], 'U', 'U', 'U', 'U', 'U', 'U', 'U', 'U', 'U', 'U', 'U', 'U'))			##### NOTE: GA1A12S202-0 NOT CONNECTED  ######################

		# Updating day values
		rrdtool.update('%s' %(ddbFile), 'N:%s:%s:%s:%s' %('U', sunT1['cda'], rainT0['cda'], 'U'))

		# Updating maximum values
#		rrdtool.update('%s' %(xdbFile), 'N:%s:%s:%s:%s:%s:%s:%s:%s:%s:%s:%s:%s:%s:%s:%s:%s:%s:%s:%s:%s' %(airTemp0['max'], tAirTemp0['max'], airPres0['max'], tAirPres0['max'], airHumi0['max'], tAirHumi0['max'], airSpeed['mgt'], tAirSpeed['max'], solFlux1['max'], tSolFlux1['max'], 'U', 'U', 'U', 'U', 'U', 'U', 'U', 'U', 'U', 'U'))
		rrdtool.update('%s' %(xdbFile), 'N:%s:%s:%s:%s:%s:%s:%s:%s:%s:%s:%s:%s:%s:%s:%s:%s:%s:%s:%s:%s' %(airTemp0['max'], tAirTemp0['max'], airPres3['max'], tAirPres3['max'], airHumi0['max'], tAirHumi0['max'], airSpeed['mgt'], tAirSpeed['max'], solFlux1['max'], tSolFlux1['max'], 'U', 'U', 'U', 'U', 'U', 'U', 'U', 'U', 'U', 'U'))

		# Updating minimum values
#		rrdtool.update('%s' %(ndbFile), 'N:%s:%s:%s:%s:%s:%s:%s:%s:%s:%s:%s:%s:%s:%s:%s:%s:%s:%s:%s:%s' %(airTemp0['min'], tAirTemp0['min'], airPres0['min'], tAirPres0['min'], airHumi0['min'], tAirHumi0['min'], airSpeed['min'], tAirSpeed['min'], solFlux1['min'], tSolFlux1['min'], 'U', 'U', 'U', 'U', 'U', 'U', 'U', 'U', 'U', 'U'))
		rrdtool.update('%s' %(ndbFile), 'N:%s:%s:%s:%s:%s:%s:%s:%s:%s:%s:%s:%s:%s:%s:%s:%s:%s:%s:%s:%s' %(airTemp0['min'], tAirTemp0['min'], airPres3['min'], tAirPres3['min'], airHumi0['min'], tAirHumi0['min'], airSpeed['min'], tAirSpeed['min'], solFlux1['min'], tSolFlux1['min'], 'U', 'U', 'U', 'U', 'U', 'U', 'U', 'U', 'U', 'U'))

# ------------ Fetching data from rrd databases --------------------------------------------------------------------------------------------------------------

		# Fetching from air values aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa
		cr01Air = rrdtool.fetch("%s" %(adbFile), 'MAX', '-s -1h', '-e -1h')					# Fetching 1 value of data from 1 hr ago
		cr06Air = rrdtool.fetch("%s" %(adbFile), 'MAX', '-s -6h', '-e -6h')					# Fetching 1 value of data from 6 hrs ago
		cr12Air = rrdtool.fetch("%s" %(adbFile), 'MAX', '-s -12h', '-e -12h')				# Fetching 1 value of data from 12 hrs ago
		set10Air = rrdtool.fetch("%s" %(adbFile), 'MAX', '-s -10min')						# Fetching 1 set of data since 10 min ago

#		print "cr01Air =", cr01Air		# Check-print fetched data
#		print "cr06Air =", cr06Air		# Check-print fetched data
#		print "cr12Air =", cr12Air		# Check-print fetched data
#		print "set10Air =", set10Air		# Check-print fetched data

		# Fetching from rain gauge tilt values rrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrr
		# Getting minutes since start of current period: hour, day, week, month, year , using "minSinceStartOfPeriod()" function from module mwsGraphs

		minChr, minCda, minCwe, minCmo, minCye = mwsGraphs.minSinceStartOfPeriod()

#		print "minChr =", minChr			# Check-print data
#		print "minCda =", minCda			# Check-print data
#		print "minCwe =", minCwe			# Check-print data
#		print "minCmo =", minCmo			# Check-print data
#		print "minCye =", minCye			# Check-print data

		# Fetching values from start of current period
		tiltChr = rrdtool.fetch('%s' %(rdbFile), 'MAX', '-s -%smin' %(minChr+1), '-e -%smin' %(minChr+1))			# Fetches 1 value of tilt data from last change of hour
		tiltCda = rrdtool.fetch('%s' %(rdbFile), 'MAX', '-s -%smin' %(minCda+1), '-e -%smin' %(minCda+1))			# Fetches 1 value of tilt data from last change of day
		tiltCwe = rrdtool.fetch('%s' %(rdbFile), 'MAX', '-s -%smin' %(minCwe+1), '-e -%smin' %(minCwe+1))			# Fetches 1 value of tilt data from last change of week
		tiltCmo = rrdtool.fetch('%s' %(rdbFile), 'MAX', '-s -%smin' %(minCmo+1), '-e -%smin' %(minCmo+1))			# Fetches 1 value of tilt data from last change of month
		tiltCye = rrdtool.fetch('%s' %(rdbFile), 'MAX', '-s -%smin' %(minCye+1), '-e -%smin' %(minCye+1))			# Fetches 1 value of tilt data from last change of year

#		print "tiltChr =", tiltChr			# Check-print fetched data
#		print "tiltCda =", tiltCda			# Check-print fetched data
#		print "tiltCwe =", tiltCwe			# Check-print fetched data
#		print "tiltCmo =", tiltCmo			# Check-print fetched data
#		print "tiltCye =", tiltCye			# Check-print fetched data

		# Fetching values from start of preceding period
		tiltPhr = rrdtool.fetch("%s" %(rdbFile), 'MAX', '-s -60min', '-e -60min')			# Fetches 1 value of tilt data from  1 hour ago
		tiltP2hr = rrdtool.fetch("%s" %(rdbFile), 'MAX', '-s -120min', '-e -120min')			# Fetches 1 value of tilt data from  1 hour ago
		tiltPda = rrdtool.fetch("%s" %(rdbFile), 'MAX', '-s -24h', '-e -24h')				# Fetches 1 value of tilt data from 24 hours ago
		tiltPwe = rrdtool.fetch("%s" %(rdbFile), 'MAX', '-s -7d', '-e -7d')					# Fetches 1 value of tilt data from 7 full days ago
		tiltPmo = rrdtool.fetch("%s" %(rdbFile), 'MAX', '-s -30d', '-e -30d')				# Fetches 1 value of tilt data from 30 full days ago
		tiltPye = rrdtool.fetch("%s" %(rdbFile), 'MAX', '-s -12mon', '-e -12mon')			# Fetches 1 value of tilt data from 12 full months ago

#		print "tiltPhr =", tiltPhr			# Check-print fetched data
#		print "tiltP2hr =", tiltP2hr		# Check-print fetched data
#		print "tiltPda =", tiltPda			# Check-print fetched data
#		print "tiltPwe =", tiltPwe			# Check-print fetched data
#		print "tiltPmo =", tiltPmo			# Check-print fetched data
#		print "tiltPye =", tiltPye			# Check-print fetched data

		# Done fetching from rain gauge tilt values rrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrr
		
		# Fetching from system values
		cr01Sys = rrdtool.fetch("%s" %(ydbFile), 'MAX', '-s -1h', '-e -1h')				# Fetches 1 value of data from 1 hr ago

		# Fetching from inside values iiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiii
		cr01Ins = rrdtool.fetch("%s" %(idbFile), 'MAX', '-s -1h', '-e -1h')					# Fetching 1 value of data from 1 hr ago
		cr06Ins = rrdtool.fetch("%s" %(idbFile), 'MAX', '-s -6h', '-e -6h')					# Fetching 1 value of data from 6 hrs ago
		cr12Ins = rrdtool.fetch("%s" %(idbFile), 'MAX', '-s -12h', '-e -12h')				# Fetching 1 value of data from 12 hrs ago

		# Fetching from day values
		set10Day = rrdtool.fetch("%s" %(ddbFile), 'MAX', '-s -10hours')						# Fetches 1 set of data since 10 hours ago
#		print "set10Day =", set10Day			# Check-print fetched day data

		# Fetching from max values
		set10Max = rrdtool.fetch("%s" %(xdbFile), 'MAX', '-s -10hours')						# Fetches 1 set of data since 10 hours ago
#		print "set10Max =", set10Max			# Check-print fetched max data

		# Fetching from min values
		set10Min = rrdtool.fetch("%s" %(ndbFile), 'MIN', '-s -10hours')						# Fetches 1 set of data since 10 hours ago
#		print "set10Min =", set10Min			# Check-print fetched max data

# ------------ Calculating values from fetched data ------------------------------------------------------------------------------------------------------------------------

		# Calculating various air values from fetched air values
		if cr01Air[2][0][0] is not None:
			airTemp0['r01'] = airTemp0['cur'] - cr01Air[2][0][0]			# Change rate of DS18B20 Nr. 11 (Stevenson screen) temperature since 1 hr ago			chchchchchchchchchchchchch
		if cr01Air[2][0][3] is not None:
			airTemp1['r01'] = airTemp1['cur'] - cr01Air[2][0][3]			# Change rate of BME280 temperature since 1 hr ago (may not be needed)
		if cr01Air[2][0][5] is not None:
			airPres0['r01'] = airPres0['qff'] - cr01Air[2][0][5]			# Change rate of BME280 sealevel air pressure since 1 hr ago
		if cr01Air[2][0][10] is not None:
			airHumi0['r01'] = airHumi0['cur'] - cr01Air[2][0][10]			# Change rate of BME280 air humidity since 1 hr ago

		if cr06Air[2][0][5] is not None:
			airPres0['r06'] = airPres0['qff'] - cr06Air[2][0][5]			# Change rate of BME280 sealevel air pressure since 6 hr ago
		if cr12Air[2][0][5] is not None:
			airPres0['r12'] = airPres0['qff'] - cr12Air[2][0][5]			# Change rate of BME280 sealevel air pressure since 12 hr ago
		
		# Creating List for calculating average wind speed using list comprehension
		av10SpeedList = [set10Air[2][i][15] for i in range(len(set10Air[2])) if set10Air[2][i][15] is not None]
		
		av10SpeedLen = len(av10SpeedList)		# NOTE: The length of the created list may be different to the len(set10Air[2]) !
		if av10SpeedLen != 0:
			airSpeed['av10'] = sum(av10SpeedList)/av10SpeedLen
			
		# Calculating rain values from fetched rain gauge tilt values

		# First setting all tilt values for subtraction to 0 in case fetched values are == None
		
		# Tilt values for subtraction
		sTiltChr = 0
		sTiltCda = 0
		sTiltCwe = 0
		sTiltCmo = 0
		sTiltCye = 0
		sTiltPhr = 0
		sTiltP2hr = 0
		sTiltPda = 0
		sTiltPwe = 0
		sTiltPmo = 0
		sTiltPye = 0

		# Calculating values for current periods
		if tiltChr[2][0][0] is not None:
			sTiltChr = tiltChr[2][0][0]
		if tiltCda[2][0][0] is not None:
			sTiltCda = tiltCda[2][0][0]
		if tiltCwe[2][0][0] is not None:
			sTiltCwe = tiltCwe[2][0][0]
		if tiltCmo[2][0][0] is not None:
			sTiltCmo = tiltCmo[2][0][0]
		if tiltCye[2][0][0] is not None:
			sTiltCye = tiltCye[2][0][0]

#		print "sTiltChr =", sTiltChr		# Check-print subtraction value
#		print "sTiltCda =", sTiltCda		# Check-print subtraction value
#		print "sTiltCwe =", sTiltCwe		# Check-print subtraction value
#		print "sTiltCmo =", sTiltCmo		# Check-print subtraction value
#		print "sTiltCye =", sTiltCye		# Check-print subtraction value

		# Calculating values for preceding periods
		if tiltPhr[2][0][0] is not None:
			sTiltPhr = tiltPhr[2][0][0]
		if tiltP2hr[2][0][0] is not None:
			sTiltP2hr = tiltP2hr[2][0][0]
		if tiltPda[2][0][0] is not None:
			sTiltPda = tiltPda[2][0][0]
		if tiltPwe[2][0][0] is not None:
			sTiltPwe = tiltPwe[2][0][0]
		if tiltPmo[2][0][0] is not None:
			sTiltPmo = tiltPmo[2][0][0]
		if tiltPye[2][0][0] is not None:
			sTiltPye = tiltPye[2][0][0]

		rainFall['chr'] = rainFall['acc'] - sTiltChr*mmPerTilt		# Rainfall during current hour
		rainFall['cda'] = rainFall['acc'] - sTiltCda*mmPerTilt		# Rainfall during current day
		rainFall['cwe'] = rainFall['acc'] - sTiltCwe*mmPerTilt		# Rainfall during current week
		rainFall['cmo'] = rainFall['acc'] - sTiltCmo*mmPerTilt		# Rainfall during current month
		rainFall['cye'] = rainFall['acc'] - sTiltCye*mmPerTilt		# Rainfall during current year
		rainFall['phr'] = rainFall['acc'] - sTiltPhr*mmPerTilt		# Rainfall during preceding 60 minutes
		rainFall['pda'] = rainFall['acc'] - sTiltPda*mmPerTilt		# Rainfall during preceding 24 hours
		rainFall['pwe'] = rainFall['acc'] - sTiltPwe*mmPerTilt		# Rainfall during preceding 7 days
		rainFall['pmo'] = rainFall['acc'] - sTiltPmo*mmPerTilt		# Rainfall during preceding 30 days
		rainFall['pye'] = rainFall['acc'] - sTiltPye*mmPerTilt		# Rainfall during preceding 12 months

#		print "rainFall['acc'] =", rainFall['acc']			# Check-print rainFall values
#		print "rainFall['chr'] =", rainFall['chr']			# Check-print rainFall values
#		print "rainFall['cda'] =", rainFall['cda']			# Check-print rainFall values
#		print "rainFall['cwe'] =", rainFall['cwe']			# Check-print rainFall values
#		print "rainFall['cmo'] =", rainFall['cmo']			# Check-print rainFall values
#		print "rainFall['cye'] =", rainFall['cye']			# Check-print rainFall values			
#		print "rainFall['phr'] =", rainFall['phr']			# Check-print rainFall values
#		print "rainFall['pda'] =", rainFall['pda']			# Check-print rainFall values
#		print "rainFall['pwe'] =", rainFall['pwe']			# Check-print rainFall values
#		print "rainFall['pmo'] =", rainFall['pmo']			# Check-print rainFall values
#		print "rainFall['pye'] =", rainFall['pye']			# Check-print rainFall values			
		
		# Calculating various system values from fetched system values (NOT USED YET FOR DISPLAY)
		if cr01Sys[2][0][0] is not None:
			cpuTemp20['r01'] = cpuTemp20['cur'] - cr01Sys[2][0][0]			# Change rate of CPU temperature since 1 hr ago (may not be needed)		FALSCH FALSCH FALSCH
		if cr01Sys[2][0][3] is not None:
			airTemp2['r01'] = airTemp2['cur'] - cr01Sys[2][0][3]			# Change rate of DS18B20 Nr. 2 (inside) temperature since 1 hr ago (may not be needed)	# BME280 (replacement of BMP180)

		# Calculating various inside values from fetched inside values
		if cr01Ins[2][0][4] is not None:
			airPres3['r01'] = airPres3['qff'] - cr01Ins[2][0][4]			# Change rate of BMP280 sealevel air pressure since 1 hr ago
		if cr06Ins[2][0][4] is not None:
			airPres3['r06'] = airPres3['qff'] - cr06Ins[2][0][4]			# Change rate of BMP280 sealevel air pressure since 6 hr ago
		if cr12Ins[2][0][4] is not None:
			airPres3['r12'] = airPres3['qff'] - cr12Ins[2][0][4]			# Change rate of BMP80 sealevel air pressure since 12 hr ago

# ------------ Creating and writing selected values to JSON File for displaying and updating on web page ------------------------------------------------------------

		# Create air JSON file (if none exists)

		# Create formatted string variables for air values
		tempCurS = "%4.1f" % airTemp0['cur']				# Creating formatted string, with 1 decimal
		tempR01S = "%4.1f" % airTemp0['r01']				# Creating formatted string, with 1 decimal

#		presQfeS = "%4.1f" % airPres0['qfe']				# Creating formatted string, with 1 decimal
#		presQffS = "%4.1f" % airPres0['qff']				# Creating formatted string, with 1 decimal
#		presR01S = "%4.1f" % airPres0['r01']				# Creating formatted string, with 1 decimal
#		presR06S = "%4.1f" % airPres0['r06']				# Creating formatted string, with 1 decimal
#		presR12S = "%4.1f" % airPres0['r12']				# Creating formatted string, with 1 decimal
		presQfeS = "%4.1f" % airPres3['qfe']				# Creating formatted string, with 1 decimal
		presQffS = "%4.1f" % airPres3['qff']				# Creating formatted string, with 1 decimal
		presR01S = "%4.1f" % airPres3['r01']				# Creating formatted string, with 1 decimal
		presR06S = "%4.1f" % airPres3['r06']				# Creating formatted string, with 1 decimal
		presR12S = "%4.1f" % airPres3['r12']				# Creating formatted string, with 1 decimal

		humiCurS = "%4.1f" % airHumi0['cur']				# Creating formatted string, with 1 decimal
		humiR01S = "%4.1f" % airHumi0['r01']				# Creating formatted string, with 1 decimal
		dewCurS = "%4.1f" % airDew['cur']					# Creating formatted string, with 1 decimal
		speedCurS = "%4.1f" % airSpeed['cur']				# Creating formatted string, with 1 decimal
		speedAv10S = "%4.1f" % airSpeed['av10']				# Creating formatted string, with 1 decimal
		dirS = "%4.1f" % airDir								# Creating formatted string, with 1 decimal

		# Create dictionary to write to air JSON file
		airDataJ01 = {'tempCur': tempCurS, 'tempR01': tempR01S, 'presQfe': presQfeS, 'presQff': presQffS, 'presR01': presR01S, 'presR06': presR06S, 'presR12': presR12S, 'humiCur': humiCurS, 'humiR01': humiR01S, 'dewCur': dewCurS, 'speedCur': speedCurS, 'speedAv10': speedAv10S, 'dir': dirS}
		print "airDataJ01 = %s" %(airDataJ01)				# Check-print dataOut dictionary

		# Writing initial value of air JSON data string
		x = open ('/var/www/html/airFileJ01.json', 'w')
		x.write ("airDataJ01 = '")
		x.close()

		# Writing data to air JSON file
		with open('/var/www/html/airFileJ01.json', 'a') as f:
			json.dump(airDataJ01, f)

		# Closing JSON data string with a single quote (air JSON file)
		x = open ('/var/www/html/airFileJ01.json', 'a')
		x.write ("'")
		x.close()
		# Done creating air JSON file ------------------------------------------------

		# Create rain JSON file (if none exists)

		# Create formatted string variables for rain values
		rainChrS = "%4.1f" % rainFall['chr']				# Creating formatted string, with 1 decimal
		rainCdaS = "%4.1f" % rainFall['cda']				# Creating formatted string, with 1 decimal
		rainCweS = "%4.1f" % rainFall['cwe']				# Creating formatted string, with 1 decimal
		rainCmoS = "%4.1f" % rainFall['cmo']				# Creating formatted string, with 1 decimal
		rainCyeS = "%4.1f" % rainFall['cye']				# Creating formatted string, with 1 decimal
		
		if digitalRD <= 0 :
			rainYesNo = 'Yes'
		else:
			rainYesNo = 'No'

		# Create dictionary to write to rain JSON file
#		rainDataJ01 = {'rainChr': rainChrS, 'rainCda': rainCdaS, 'rainCwe': rainCweS, 'rainCmo': rainCmoS, 'rainCye': rainCyeS}
		rainDataJ01 = {'rainChr': rainChrS, 'rainCda': rainCdaS, 'rainCwe': rainCweS, 'rainCmo': rainCmoS, 'rainCye': rainCyeS, 'raining': rainYesNo}
		print "rainDataJ01 = %s" %(rainDataJ01)				# Check-print dataOut dictionary

		# Writing initial value of rain JSON data string
		x = open ('/var/www/html/rainFileJ01.json', 'w')
		x.write ("rainDataJ01 = '")
		x.close()

		# Writing data to rain JSON file
		with open('/var/www/html/rainFileJ01.json', 'a') as f:
			json.dump(rainDataJ01, f)

		# Closing JSON data string with a single quote (rain JSON file)
		x = open ('/var/www/html/rainFileJ01.json', 'a')
		x.write ("'")
		x.close()
		# Done creating rain JSON file ------------------------------------------------

		# Create system JSON file (if none exists)

		# Create formatted string variables for system values
		cpuT2CurS = "%4.1f" % cpuTemp20['cur']				# Creating formatted string, with 1 decimal
		cpuT2MaxS = "%4.1f" % cpuTemp20['max']				# Creating formatted string, with 1 decimal
		cpuT2MinS = "%4.1f" % cpuTemp20['min']				# Creating formatted string, with 1 decimal
		airT2CurS = "%4.1f" % airTemp2['cur']				# Creating formatted string, with 1 decimal
		airT2MaxS = "%4.1f" % airTemp2['max']				# Creating formatted string, with 1 decimal
		airT2MinS = "%4.1f" % airTemp2['min']				# Creating formatted string, with 1 decimal

		# Create dictionary to write to system JSON file
		sysDataJ01 = {'cpuT2Cur': cpuT2CurS, 'cpuT2Max': cpuT2MaxS, 'cpuT2Min': cpuT2MinS, 'airT2Cur': airT2CurS, 'airT2Max': airT2MaxS, 'airT2Min': airT2MinS}
		print "sysDataJ01 = %s" %(sysDataJ01)				# Check-print dataOut dictionary
		# Writing initial value of system JSON data string
		x = open ('/var/www/html/sysFileJ01.json', 'w')
		x.write ("sysDataJ01 = '")
		x.close()

		# Writing data to system JSON file
		with open('/var/www/html/sysFileJ01.json', 'a') as f:
			json.dump(sysDataJ01, f)

		# Closing JSON data string with a single quote (system JSON file)
		x = open ('/var/www/html/sysFileJ01.json', 'a')
		x.write ("'")
		x.close()
		# Done creating system JSON file ------------------------------------------------

		# Create solar JSON file (if none exists)

		# Create formatted string variables for solar values
		fluxCurS = "%5.1f" % 10**(solFlux1['cur'] / 680)			# Creating formatted string for Lux value:   E[Lux] = 10^(E[mV] / 680) , with 1 decimal
		fluxR01S = "%5.1f" % 10**(solFlux1['r01'] / 680)			# Creating formatted string for Lux value:   E[Lux] = 10^(E[mV] / 680) , with 1 decimal
		uviCurS = "%4.1f" % solUvi['cur']							# Creating formatted string, with 1 decimal
		uviR01S = "%4.1f" % solUvi['r01']							# Creating formatted string, with 1 decimal

		pVoltCurS = "%4.2f" % solPvolt['cur']						# Creating formatted string, with 2 decimals
		pCurrCurS = "%4.2f" % solPcurr['cur']						# Creating formatted string, with 2 decimals
		bVoltCurS = "%4.2f" % solBvolt['cur']						# Creating formatted string, with 2 decimals
		bCurrCurS = "%4.2f" % solBcurr['cur']						# Creating formatted string, with 2 decimals

		sunT1CdaHouS = "%4d" % (sunT1['cda']//3600.0)				# Creating formatted string for sunshine time hours
		sunT1CdaMinS = "%2d" % ((sunT1['cda']%3600.0)//60.0)		# Creating formatted string for sunshine time minutes
		sunT1CdaSecS = "%2d" % (sunT1['cda']%60.0)					# Creating formatted string for sunshine time remaining seconds
		sunT1CweHouS = "%4d" % (sunT1['cwe']//3600.0)				# Creating formatted string for sunshine time hours
		sunT1CweMinS = "%2d" % ((sunT1['cwe']%3600.0)//60.0)		# Creating formatted string for sunshine time minutes
		sunT1CweSecS = "%2d" % (sunT1['cwe']%60.0)					# Creating formatted string for sunshine time remaining seconds
		sunT1CmoHouS = "%4d" % (sunT1['cmo']//3600.0)				# Creating formatted string for sunshine time hours
		sunT1CmoMinS = "%2d" % ((sunT1['cmo']%3600.0)//60.0)		# Creating formatted string for sunshine time minutes
		sunT1CmoSecS = "%2d" % (sunT1['cmo']%60.0)					# Creating formatted string for sunshine time remaining seconds
		sunT1CyeHouS = "%4d" % (sunT1['cye']//3600.0)				# Creating formatted string for sunshine time hours
		sunT1CyeMinS = "%2d" % ((sunT1['cye']%3600.0)//60.0)		# Creating formatted string for sunshine time minutes
		sunT1CyeSecS = "%2d" % (sunT1['cye']%60.0)					# Creating formatted string for sunshine time remaining seconds

		# Create dictionary to write to solar JSON file
#		solDataJ01 = {'fluxCur': fluxCurS, 'fluxR01': fluxR01S, 'uviCur': uviCurS, 'uviR01': uviR01S, 'pVoltCur': pVoltCurS, 'pCurrCur': pCurrCurS, 'bVoltCur': bVoltCurS, 'bCurrCur': bCurrCurS, 'sunT1Min': sunT1MinS, 'sunT1Sec': sunT1SecS}
# 		solDataJ01 = {'fluxCur': fluxCurS, 'fluxR01': fluxR01S, 'uviCur': uviCurS, 'uviR01': uviR01S, 'pVoltCur': pVoltCurS, 'pCurrCur': pCurrCurS, 'bVoltCur': bVoltCurS, 'bCurrCur': bCurrCurS, 'sunT1CdaMin': sunT1CdaMinS, 'sunT1CdaSec': sunT1CdaSecS, 'sunT1CweMin': sunT1CweMinS, 'sunT1CweSec': sunT1CweSecS, 'sunT1CmoMin': sunT1CmoMinS, 'sunT1CmoSec': sunT1CmoSecS, 'sunT1CyeMin': sunT1CyeMinS, 'sunT1CyeSec': sunT1CyeSecS}
		solDataJ01 = {'fluxCur': fluxCurS, 'fluxR01': fluxR01S, 'uviCur': uviCurS, 'uviR01': uviR01S, 'pVoltCur': pVoltCurS, 'pCurrCur': pCurrCurS, 'bVoltCur': bVoltCurS, 'bCurrCur': bCurrCurS, 'sunT1CdaHou': sunT1CdaHouS, 'sunT1CdaMin': sunT1CdaMinS, 'sunT1CdaSec': sunT1CdaSecS, 'sunT1CweHou': sunT1CweHouS, 'sunT1CweMin': sunT1CweMinS, 'sunT1CweSec': sunT1CweSecS, 'sunT1CmoHou': sunT1CmoHouS, 'sunT1CmoMin': sunT1CmoMinS, 'sunT1CmoSec': sunT1CmoSecS, 'sunT1CyeHou': sunT1CyeHouS, 'sunT1CyeMin': sunT1CyeMinS, 'sunT1CyeSec': sunT1CyeSecS}
		print "solDataJ01 = %s" %(solDataJ01)						# Check-print dataOut dictionary

		# Writing initial value of solar JSON data string
		x = open ('/var/www/html/solFileJ01.json', 'w')
		x.write ("solDataJ01 = '")
		x.close()

		# Writing data to solar JSON file
		with open('/var/www/html/solFileJ01.json', 'a') as f:
			json.dump(solDataJ01, f)

		# Closing JSON data string with a single quote (solar JSON file)
		x = open ('/var/www/html/solFileJ01.json', 'a')
		x.write ("'")
		x.close()
		# Done creating solar JSON file ------------------------------------------------

		# Create maximum values JSON file (if none exists)

		# Create formatted string variables for maximum values
		tempMaxS = "%4.1f" % airTemp0['max']						# Creating formatted string, with 1 decimal
		tTempMaxS = time.strftime('%H:%M', time.localtime(tAirTemp0['max']))

#		presMaxS = "%4.1f" % airPres0['max']						# Creating formatted string, with 1 decimal : airPres0
#		tPresMaxS = time.strftime('%H:%M', time.localtime(tAirPres0['max']))
		presMaxS = "%4.1f" % airPres3['max']						# Creating formatted string, with 1 decimal : airPres3
		tPresMaxS = time.strftime('%H:%M', time.localtime(tAirPres3['max']))

		humiMaxS = "%4.1f" % airHumi0['max']						# Creating formatted string, with 1 decimal
		tHumiMaxS = time.strftime('%H:%M', time.localtime(tAirHumi0['max']))
		speedMaxS = "%4.1f" % airSpeed['mgt']						# Creating formatted string, with 1 decimal
		tSpeedMaxS = time.strftime('%H:%M', time.localtime(tAirSpeed['max']))
		fluxMaxS = "%5.1f" % 10**(solFlux1['max'] / 680.0)			# Creating formatted string for Lux value:   E[Lux] = 10^(E[mV] / 680) , with 1 decimal
		tFluxMaxS = time.strftime('%H:%M', time.localtime(tSolFlux1['max']))
		uviMaxS = "%4.1f" % solUvi['max']							# Creating formatted string, with 1 decimal
		tUviMaxS = time.strftime('%H:%M', time.localtime(tSolUvi['max']))
		pVoltMaxS = "%4.1f" % solPvolt['max']						# Creating formatted string, with 1 decimal
		tPvoltMaxS = time.strftime('%H:%M', time.localtime(tSolPvolt['max']))
		pCurrMaxS = "%4.1f" % solPcurr['max']						# Creating formatted string, with 1 decimal
		tPcurrMaxS = time.strftime('%H:%M', time.localtime(tSolPcurr['max']))
		bVoltMaxS = "%4.1f" % solBvolt['max']						# Creating formatted string, with 1 decimal
		tBvoltMaxS = time.strftime('%H:%M', time.localtime(tSolBvolt['max']))
		bCurrMaxS = "%4.1f" % solBcurr['max']						# Creating formatted string, with 1 decimal
		tBcurrMaxS = time.strftime('%H:%M', time.localtime(tSolBcurr['max']))

		# Create dictionary to write to maximum values JSON file
		maxDataJ01 = {'tempMax': tempMaxS, 'tTempMax': tTempMaxS, 'presMax': presMaxS, 'tPresMax': tPresMaxS, 'humiMax': humiMaxS, 'tHumiMax': tHumiMaxS, 'speedMax': speedMaxS, 'tSpeedMax': tSpeedMaxS, 'fluxMax': fluxMaxS, 'tFluxMax': tFluxMaxS, 'uviMax': uviMaxS, 'tUviMax': tUviMaxS, 'pVoltMax': pVoltMaxS, 'tPvoltMax': tPvoltMaxS, 'pCurrMax': pCurrMaxS, 'tPcurrMax': tPcurrMaxS, 'bVoltMax': bVoltMaxS, 'tBvoltMax': tBvoltMaxS, 'bCurrMax': bCurrMaxS, 'tBcurrMax': tBcurrMaxS}
		print "maxDataJ01 = %s" %(maxDataJ01)						# Check-print dataOut dictionary

		# Writing initial value of maximum values JSON data string
		x = open ('/var/www/html/maxFileJ01.json', 'w')
		x.write ("maxDataJ01 = '")
		x.close()

		# Writing data to maximum JSON file
		with open('/var/www/html/maxFileJ01.json', 'a') as f:
			json.dump(maxDataJ01, f)

		# Closing JSON data string with a single quote (maximum JSON file)
		x = open ('/var/www/html/maxFileJ01.json', 'a')
		x.write ("'")
		x.close()
		# Done creating maximum values JSON file ------------------------------------------------

		# Create minimum values JSON file (if none exists)

		# Create formatted string variables for minimum values
		tempMinS = "%4.1f" % airTemp0['min']						# Creating formatted string, with 1 decimal
		tTempMinS = time.strftime('%H:%M', time.localtime(tAirTemp0['min']))

#		presMinS = "%4.1f" % airPres0['min']						# Creating formatted string, with 1 decimal : airPres0
#		tPresMinS = time.strftime('%H:%M', time.localtime(tAirPres0['min']))
		presMinS = "%4.1f" % airPres3['min']						# Creating formatted string, with 1 decimal : airPres3
		tPresMinS = time.strftime('%H:%M', time.localtime(tAirPres3['min']))

		humiMinS = "%4.1f" % airHumi0['min']						# Creating formatted string, with 1 decimal
		tHumiMinS = time.strftime('%H:%M', time.localtime(tAirHumi0['min']))
		speedMinS = "%4.1f" % airSpeed['min']						# Creating formatted string, with 1 decimal
		tSpeedMinS = time.strftime('%H:%M', time.localtime(tAirSpeed['min']))
		fluxMinS = "%5.1f" % 10**(solFlux1['min'] / 680.0)			# Creating formatted string for Lux value:   E[Lux] = 10^(E[mV] / 680) , with 1 decimal
		tFluxMinS = time.strftime('%H:%M', time.localtime(tSolFlux1['min']))
		uviMinS = "%4.1f" % solUvi['min']							# Creating formatted string, with 1 decimal
		tUviMinS = time.strftime('%H:%M', time.localtime(tSolUvi['min']))
		pVoltMinS = "%4.1f" % solPvolt['min']						# Creating formatted string, with 1 decimal
		tPvoltMinS = time.strftime('%H:%M', time.localtime(tSolPvolt['min']))
		pCurrMinS = "%4.1f" % solPcurr['min']						# Creating formatted string, with 1 decimal
		tPcurrMinS = time.strftime('%H:%M', time.localtime(tSolPcurr['min']))
		bVoltMinS = "%4.1f" % solBvolt['min']						# Creating formatted string, with 1 decimal
		tBvoltMinS = time.strftime('%H:%M', time.localtime(tSolBvolt['min']))
		bCurrMinS = "%4.1f" % solBcurr['min']						# Creating formatted string, with 1 decimal
		tBcurrMinS = time.strftime('%H:%M', time.localtime(tSolBcurr['min']))

		# Create dictionary to write to minimum values JSON file
		minDataJ01 = {'tempMin': tempMinS, 'tTempMin': tTempMinS, 'presMin': presMinS, 'tPresMin': tPresMinS, 'humiMin': humiMinS, 'tHumiMin': tHumiMinS, 'speedMin': speedMinS, 'tSpeedMin': tSpeedMinS, 'fluxMin': fluxMinS, 'tFluxMin': tFluxMinS, 'uviMin': uviMinS, 'tUviMin': tUviMinS, 'pVoltMin': pVoltMinS, 'tPvoltMin': tPvoltMinS, 'pCurrMin': pCurrMinS, 'tPcurrMin': tPcurrMinS, 'bVoltMin': bVoltMinS, 'tBvoltMin': tBvoltMinS, 'bCurrMin': bCurrMinS, 'tBcurrMin': tBcurrMinS}
		print "minDataJ01 = %s" %(minDataJ01)						# Check-print dataOut dictionary

		# Writing initial value of minimum values JSON data string
		x = open ('/var/www/html/minFileJ01.json', 'w')
		x.write ("minDataJ01 = '")
		x.close()

		# Writing data to minimum JSON file
		with open('/var/www/html/minFileJ01.json', 'a') as f:
			json.dump(minDataJ01, f)

		# Closing JSON data string with a single quote (minimum JSON file)
		x = open ('/var/www/html/minFileJ01.json', 'a')
		x.write ("'")
		x.close()
		# Done creating minimum values JSON file ---------------------------------------------------------

# ----------- Opening or creating valFile.txt and writing selected values as strings ----------------------------------------------------------------------
# ----------- NOTE: The contents of valFile.txt are used to display on ZeroSeg

		# creating or opening File "valFile.txt" for writing
		xFile = open('/media/dShare2/valFile.txt','w')							# NOTE: Always replacing previous value with new value

#		# Writing current temperature and humidity to valFile.txt as formatted strings:
#		xFile.write("%3.1f/%3.0f" % (airTemp0['cur'], airHumi0['cur']))			# NOTE: Air temperature must be with 1 decimal place, then "/" as delimiter, then air  humidity with 0 decimal place.

		# Writing current temperature, humidity and pressure (QFF) to valFile.txt as formatted strings:
		# NOTE: Air temperature must be with 1 decimal place, then "/" as delimiter, then air humidity with 0 decimal place, then "!" as delimiter, then air pressure with 1 decimal place
#		xFile.write("%3.1f/%3.0f!%4.1f" % (airTemp0['cur'], airHumi0['cur'], airPres0['qff']))
		xFile.write("%3.1f/%3.0f!%4.1f" % (airTemp0['cur'], airHumi0['cur'], airPres3['qff']))
		xFile.close()

		# Check printing contents of text file:				# FOR TESTING ONLY
#		xFile = open('/media/dShare2/valFile.txt','r')
#		print "valFile reads: %s" % xFile.read()			# Reading current temperature from txt file as string
#		xFile.close()

# ------------ Creating graphs -----------------------------------------------------------------------------------------------------------------------------
		print "Creating graphs gggggggggggggggggggggg"

		# Creating different air graphs
		# Possible values for grValue are: 'TempX', 'Temp', 'PresX', 'Pres', 'HumiX', 'Humi', 'Dew', 'Speed', 'Dir'

		# Defining input variable varValue (a value that can be used for various purposes) depending on graType
		for grValue in ['TempX', 'Temp', 'PresX', 'Pres', 'HumiX', 'Humi', 'Dew', 'Speed', 'Dir']:
			if grValue == 'TempX' or grValue == 'Temp':
				varValue = airTemp0['cur']
			elif grValue == 'PresX':
				varValue = airPres0['qff']
			elif grValue == 'Pres':
				varValue = airPres3['qff']
			elif grValue == 'HumiX' or grValue == 'Humi':
				varValue = airHumi0['cur']
			elif grValue == 'Dew':
				varValue = airDew['cur']
			elif grValue == 'Speed':
				varValue = int(airSpeed['cur']*100.0+0.5)/100.0
			elif grValue == 'Dir':
				varValue = airDir

			# Creating 4 different air graphs depending on value to be displayed
			for grType in ['2Hourly', 'Daily', 'Weekly', 'Monthly']:
				mwsGraphs.airGraph(grValue, grType, varValue)

		print "Air graphs created"

		# creating rain graphs	rrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrr
		# Creating 10 different rain graphs depending on timespan since start of period
		# Defining sTilt valus i.e. number of tilts to subtract from yearly tilt value which is stored in data base
#		startTime = '-1min' 		# defines start time of graph as a STRING of negative time offset from now in minutes (this is a dummy value)
#		for grType in ['Chour', 'Cday', 'Cweek', 'Cmonth', 'Cyear', 'Phour', 'Pday', 'Pweek', 'Pmonth', 'Pyear']:
#		for grType in ['Chour', 'Cday', 'Cweek', 'Cmonth', 'Cyear', 'P2hours', 'Pday', 'Pweek', 'Pmonth', 'Pyear']:
		for grType in ['Chour', 'Cday', 'Cweek', 'Cmonth', 'P2hours', 'Pday', 'Pweek', 'Pmonth']:
			if grType == 'Chour':
				sTilt = sTiltChr
			elif grType == 'Cday':
				sTilt = sTiltCda
			elif grType == 'Cweek':
				sTilt = sTiltCwe
			elif grType == 'Cmonth':
				sTilt = sTiltCmo
			elif grType == 'Cyear':
				sTilt = sTiltCye
			elif grType == 'Phour':
				sTilt = sTiltPhr
			elif grType == 'P2hours':
				sTilt = sTiltP2hr
			elif grType == 'Pday':
				sTilt = sTiltPda
			elif grType == 'Pweek':
				sTilt = sTiltPwe
			elif grType == 'Pmonth':
				sTilt = sTiltPmo
			elif grType == 'Pyear':
				sTilt = sTiltPye

			# Creating 10 different rainfall graphs
			mwsGraphs.rainGraph('Rain', grType, sTilt)

		# creating 4 different rain drop graphs depending on value to be displayed
		varValue = analogRD
		for grType in ['2Hourly', 'Cday', 'Weekly', 'Monthly']:
			mwsGraphs.dropsGraph('Drops', grType, varValue)

		print "Rain graphs created"

		# creating system graphs	yyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyy
		# Possible values for grVal are: 'Sys'

		# Defining input variable varValue (a value that can be used for various purposes) depending on graType
		for grValue in ['Sys']:
			if grValue == 'Sys':
				varValue = cpuTemp20['cur']

			# creating 4 different system graphs depending on value to be displayed
			for grType in ['2Hourly', 'Daily', 'Weekly', 'Monthly']:
				mwsGraphs.sysGraph(grValue, grType, varValue)

		print "System graphs created"

		# creating solar graphs	ssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssss
		# Possible values for grVal are: 'Flux', 'LuxX', 'Lux', 'Uvi', 'Pcurr', 'Bvolt'

		# Defining input variable varValue (a value that can be used for various purposes) depending on graType
		for grValue in ['Flux', 'LuxX', 'Lux']:
			if grValue == 'Flux' or grValue == 'LuxX' or grValue == 'Lux' :
#				varValue = solFlux0['cur']
				varValue = sunThresh			# Take threshold Lux value 'sunThresh' (to measure sunshine duration) as varValue for comment on graph
#			elif grValue == 'Uvi':
#				varValue = solUvi['cur']
#			elif grValue == 'Pcurr':
#				varValue = solPcurr['cur']
#			elif grValue == 'Bvolt':
#				varValue = solBvolt['cur']

			# creating 4 different solar graphs depending on value to be displayed
			for grType in ['2Hourly', 'Daily', 'Weekly', 'Monthly']:
				mwsGraphs.solGraph(grValue, grType, varValue)

		print "Solar graphs created"
		
		# creating day graph	ddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddd

		# Defining input variable varValue (a value that can be used for various purposes) depending on graType
#		for grValue in ['SunT1', 'Val0', 'Dayval']:
		for grValue in ['SunT1', 'RainT0', 'Dayval']:
			# Defining input variable varValue (a value that can be used for various purposes) depending on graType
#			if grValue == 'SunT1' or grValue == 'Val0':
			if grValue == 'SunT1' or grValue == 'RainT0':
				varValue = sunT1['cda']			# Take threshold Lux value 'sunThresh' (to measure sunshine duration) as varValue for comment on graph
			else:
				varValue = digitalRD

			# creating 3 different day graphs
			for grType in ['2Hourly', 'Cday', 'Weekly', 'Monthly', 'Yearly']:
				mwsGraphs.dayGraph(grValue, grType, varValue)
		
		print "Day graph created"

		# creating max graphs	xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

		# Defining input variable varValue (a value that can be used for various purposes) depending on graType
		# grValue = 'Temp0'
		varValue = airTemp0['max']
		for grValue in ['Temp0', 'Pres0', 'Humi0', 'Speed', 'Flux0']:

			# creating 3 different max graphs
			for grType in ['Weekly', 'Monthly', 'Yearly']:
				mwsGraphs.maxGraph(grValue, grType, varValue)
		
		print "Max graph created"

		# creating min graphs	nnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnn

		# Defining input variable varValue (a value that can be used for various purposes) depending on graType
		# grValue = 'Temp0'
#		varValue = airTemp0['min']
#		for grValue in ['Temp0', 'Pres0', 'Humi0']:

			# creating 3 different min graphs
#			for grType in ['Weekly', 'Monthly', 'Yearly']:
#				mwsGraphs.minGraph(grValue, grType, varValue)
		
#		print "Min graph created"

# ------------ End of graph creation --------------------------------------------------------------------------------------------

# ------------ Moving weatherPics and graphs created by TPi0 camera -------------------------------------------------------------

		shutil.copy('/media/wShare2/WeatherImages/weatherPic1.jpg', '/var/www/html/mwsImages/weatherImg1.jpg')
		shutil.copy('/media/wShare2/WeatherImages/weatherPic2.jpg', '/var/www/html/mwsImages/weatherImg2.jpg')

		shutil.copy('/media/wShare2/CamGra/camDatSysTempHourly.png', '/var/www/html/camGraphs/camDatSysTempHourly.png')
		shutil.copy('/media/wShare2/CamGra/camDatSysTempDaily.png', '/var/www/html/camGraphs/camDatSysTempDaily.png')
		shutil.copy('/media/wShare2/CamGra/camDatSysTempWeekly.png', '/var/www/html/camGraphs/camDatSysTempWeekly.png')
		shutil.copy('/media/wShare2/CamGra/camDatSysTempMonthly.png', '/var/www/html/camGraphs/camDatSysTempMonthly.png')

# ------------ Calculating waiting time till start of next loop ---------------------------------------------------
		waitTime = loopTime - (time.time() - loopStart)		# time for one loop = loopTime sec
		if waitTime > 0:									# Argument for time.sleep() must be >= 0
			time.sleep(waitTime)

		effLoopTime = time.time() - loopStart
		print('\nWait time = %3.2f   Eff. loop time =  %3.2f\n') %(waitTime, effLoopTime)	# (FOR TESTING ONLY)
		print "--------------------------------------------------------"

# ------------ End of main loop --------------------------------------------------------------------------------------------------
# ------------------------------------------------------------------------------------------------------------------------------

# Catching exceptions ==========================================================================================================
except KeyboardInterrupt:
	print('\nProgram terminated by keyboard interrupt: Ctrl-C')

# except:
#	print('Other error or exception occurred!')

finally:
	GPIO.cleanup()			# clean up GPIO on exit  
