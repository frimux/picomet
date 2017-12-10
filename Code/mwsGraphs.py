#!/usr/bin/python
# -*- coding: utf-8 -*-

# MODULE for rrd Graphs for getPmDataXY.py
# REQUIRED for programs getPmData35.py and later !

import rrdtool
from datetime import datetime as dtdt		# i.e.  "dtdt"  is an alias for class  "datetime.datetime"

# EXPLAINING all gPar keys and values:
# Defining gPar (i.e. graph parameters) for rrdGraph function as "dictionary" and assign initial values
# gPar = {}													# Not a global variable! It's declared in each graph function separately, except rrdGraph itself
# gPar['grVl'] = "Temp"										# Value to be plotted like "Temp", etc.
# gPar['grTp'] = "Hourly"									# Graph type e.g. "Hourly", etc.
# gPar['vrVl'] = 18.3										# Can  be used for various values optionally needed in the graphs
# gPar['dbNm0'] = "solDat"									# First  RRD database name e.g. "airDat", etc. => dbFile0 = gPar['dbNm0'] + ".rrd"
# gPar['dbNm1'] = "insDat"									# Second RRD database name e.g. "insDat", etc. => dbFile1 = gPar['dbNm1'] + ".rrd"
# gPar['grPa'] = "/var/www/html/solGra/"					# Path to folder where graph ist stored e.g. '/var/www/html/solGra/'
# gPar['rpnX0'] = '10,LOG,*,680,/,EXP'						# RPN Expression, e.g. '10,LOG,*,680,/,EXP'  (values and operators separated by commas, no leading comma in expression!)
# gPar['rpnX1'] = '10,LOG,*,680,/,EXP'						# RPN Expression, e.g. '1,*'  (values and operators separated by commas, no leading comma in expression!)
# gPar['grAd'] = "Preceding 24 hours"						# Added title info e.g. "Preceding 24 hours"
# gPar['stTm'] = "-2hours"									# Starting time of graph creation e.g. "-2hours", etc. NOTE: Graphs always end NOW.
# gPar['cFnc'] = "AVERAGE"									# Consolidation function, e.g. "AVERAGE" or "MAX" MUST match gPar['cFnc'] of corresponding data base
# gPar['nmLn'] = 2											# Number of lines / areas to be plotted: 1 , 2 (or 0 for special graph)
# gPar['grTi'] = "Outside temperature 2m above ground"		# Graph title e.g. "Outside temperature 2m above ground"
# gPar['ds0'] = "Flux0"										# Name of data source (DS) of used data base e.g. 'solDatFlux0'
# gPar['ds1'] = "Flux1"										# Name of data source (DS) of used data base e.g. 'solDatFlux1'
# gPar['lnNm0'] = "Outside (DS18B20) Temperature"			# Name of this line e.g. "Outside (DS18B20) Temperature"
# gPar['lnNm1'] = "Outside (BME280) Temperature"			# Name of this line e.g. "Outside (BME280) Temperature"
# gPar['gTxt0'] = "Current outside (DS18B20) Temperature"	# Text for GPRINT function e.g. "Current outside (DS18B20) Temperature"
# gPar['gTxt1'] = "Current outside (BME280) Temperature"	# Text for GPRINT function e.g. "Current outside (BME280) Temperature"
# gPar['yUni'] = "km/h"										# Unit of y axis e.g. "km/h"
# gPar['cTxt'] = "This is a comment"						# Comment text e.g. "This is a comment" NOTE: If empty, there is no comment
# gPar['lCl0'] = "CDCD00"									# Line colour e.g. "CDCD00"
# gPar['lCl1'] = "00FFFF"									# Line colour e.g. "00FFFF"
# gPar['aCl0'] = "FF0000"									# Area colour e.g. "FF0000"  or "" i.e.empty for NO area fill colour
# gPar['aCl1'] = "87CEFF"									# Area colour e.g. "87CEFF"
## gPar['grWi'] = 600							NOT USED			# Graph width in pixels e.g. 600 (is common to all graphs)

# Function for creating air graphs aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa

def airGraph(grVal, grType, varVal):
	# Possible values for grVal currently are: 'TempX', 'Temp', 'PresX', 'Pres', 'HumiX', 'Humi', 'Dew', 'Speed', 'Dir'
	# Possible values for grType are: 'Hourly', '2Hourly', 'Daily', 'Weekly', 'Monthly'
	# varVal must be a float or integer variable
	strVarVal = "%4.2f" % varVal				# Can be used to enter into a text string

	gPar = {}									# Declaring gPar as local dictionary

	# Common graph parameters for all air graphs
	gPar['grVl'] = grVal
	gPar['grTp'] = grType
	gPar['vrVl'] = varVal						# CAUTION NOT YET defined
	gPar['dbNm0'] = "airDat"					# NOTE: All airGraphs have the same RRD database name e.g. "airDat", etc. => dbFile0 = gPar['dbNm0'] + ".rrd"
	gPar['dbNm1'] = "airDat"					# NOTE: All airGraphs have the same RRD database name e.g. "airDat", etc. => dbFile0 = gPar['dbNm0'] + ".rrd"
#	gPar['grPa'] = "/var/www/html/testGra/"		# NOTE: All airGraphs have the same path to folder where graph ist stored e.g. '/var/www/html/testGra/'
	gPar['grPa'] = "/var/www/html/airGra/"		# NOTE: All airGraphs have the same path to folder where graph ist stored e.g. '/var/www/html/airGra/'
	gPar['rpnX0'] = '1,*'						# RPN Expression to change original value for display: '1,*' leaves original values unchanged
	gPar['rpnX1'] = '1,*'						# RPN Expression to change original value for display: '1,*' leaves original values unchanged

	# Creating 4 separate graphs

	# Defining graph parameters using function "graphTypeParameters" and creating graphs
	gPar['grAd'], gPar['stTm'], gPar['cFnc'] = graphTypeParameters(grType)
		
	# Values for graphs with 2 lines (w/o comment)
	if grVal == 'TempX':
		gPar['nmLn'] = 2			# number of lines per graph
		gPar['grTi'] = 'Outside temperature (2m above ground)'
		gPar['ds0'] = 'Temp0'
		gPar['ds1'] = 'Temp1'
		gPar['lnNm0'] = 'Outside (DS18B20) air temperature'
		gPar['lnNm1'] = 'Outside (BME280) air temperature'
		gPar['gTxt0'] = 'Current outside (DS18B20) air temp'
		gPar['gTxt1'] = 'Current outside (BME280) air temp'
		gPar['yUni'] = '*C'			# unit string for y-axis label
		gPar['cTxt'] = ""			# If empty, i.e. = "", no comment will be printed on graph
		gPar['lCl0'] = '8B008B'		# setting Temp0 line colour dark magenta
		gPar['lCl1'] = '008B00'		# setting Temp1 line colour dark green
		gPar['aCl0'] = 'FF00FF'		# setting Temp0 area colour magenta
		gPar['aCl1'] = '00FF00'		# setting Temp1 area colour green

	elif grVal == 'Temp':
		gPar['nmLn'] = 1			# number of lines per graph
		gPar['grTi'] = 'Outside temperature (2m above ground)'
		gPar['ds0'] = 'Temp0'
		gPar['lnNm0'] = 'Outside (DS18B20) air temperature'
		gPar['gTxt0'] = 'Current outside air temperature'
		gPar['yUni'] = '*C'			# unit string for y-axis label
		gPar['cTxt'] = ""			# If empty, i.e. = "", no comment will be printed on graph
		gPar['lCl0'] = '8B008B'		# setting Temp0 line colour dark magenta
		gPar['aCl0'] = 'FF00FF'		# setting Temp0 area colour magenta

	elif grVal == 'PresX':						# NOTE: Switched data bases on Dec 1, 2017
		gPar['nmLn'] = 2						# number of lines per graph
		gPar['grTi'] = 'Air pressure'
#		gPar['dbNm0'] = "airDat"				# Switched data bases on Dec 1, 2017
#		gPar['dbNm1'] = "insDat"
		gPar['dbNm0'] = "insDat"				# NOTE: THIS GIVES GRAPH FILES (*.png) A DIFFERENT NAME !!!!!
		gPar['dbNm1'] = "airDat"				# NOTE: rrdDatabase1 is different to rrdDatabase0 for airPressure graphs
#		gPar['ds0'] = 'Pres0qff'				# QFF value from airPres0: Outside pressure
#		gPar['ds1'] = 'Pres3qff'				# QFF value from airPres3: Inside pressure
		gPar['ds0'] = 'Pres3qff'				# QFF value from airPres3: Inside pressure
		gPar['ds1'] = 'Pres0qff'				# QFF value from airPres0: Outside pressure
#		gPar['lnNm0'] = 'Outside SeaLevel(QFF) pres'
#		gPar['lnNm1'] = 'Inside SeaLevel(QFF) pres'
		gPar['lnNm0'] = 'Inside SeaLevel(QFF) pres'
		gPar['lnNm1'] = 'Outside SeaLevel(QFF) pres'
#		gPar['gTxt0'] = 'Current outside QFF pressure'
#		gPar['gTxt1'] = 'Current inside QFF pressure'
		gPar['gTxt0'] = 'Current inside QFF pressure'
		gPar['gTxt1'] = 'Current outside QFF pressure'
		gPar['yUni'] = 'hPa'					# unit string for y-axis label
		gPar['cTxt'] = ""						# If empty, i.e. = "", no comment will be printed on graph
		gPar['lCl0'] = '8B0000'					# setting Temp0 line colour dark red
		gPar['lCl1'] = '008B8B'					# setting Temp1 line colour dark cyan
		gPar['aCl0'] = 'FF0000'					# setting Temp0 area colour red
		gPar['aCl1'] = '00FFFF'					# setting Temp1 area colour cyan

	elif grVal == 'Pres':						# NOTE: Switched data bases on Dec 1, 2017
		gPar['nmLn'] = 1						# number of lines per graph
		gPar['grTi'] = 'Air pressure'
		gPar['dbNm0'] = "insDat"				# NOTE: THIS GIVES GRAPH FILES (*.png) A DIFFERENT NAME !!!!!
		gPar['ds0'] = 'Pres3qff'				# QFF value from airPres3: Inside pressure
		gPar['lnNm0'] = 'SeaLevel(QFF) pressure'
		gPar['gTxt0'] = 'Current QFF pressure'
		gPar['yUni'] = 'hPa'					# unit string for y-axis label
		gPar['cTxt'] = ""						# If empty, i.e. = "", no comment will be printed on graph
		gPar['lCl0'] = '8B0000'					# setting Temp0 line colour dark red
		gPar['aCl0'] = 'FF0000'					# setting Temp0 area colour red

	elif grVal == 'HumiX':
		gPar['nmLn'] = 2			# number of lines per graph
		gPar['grTi'] = 'Relative humidity'
		gPar['ds0'] = 'Humi0'
		gPar['ds1'] = 'Humi1'
		gPar['lnNm0'] = 'Rel. (BME280) humidity'
		gPar['lnNm1'] = 'Rel. (DHT22) humidity'
		gPar['gTxt0'] = 'Current rel. (BME280) humidity'
		gPar['gTxt1'] = 'Current rel. (DHT22) humidity'
		gPar['yUni'] = '%'			# unit string for y-axis label
		gPar['cTxt'] = ""			# If empty, i.e. = "", no comment will be printed on graph
		gPar['lCl0'] = '00008B'		# setting Temp0 line colour dark blue
		gPar['lCl1'] = '8B8B00'		# setting Temp1 line colour dark yellow
		gPar['aCl0'] = '0000FF'		# setting Temp0 area colour blue
		gPar['aCl1'] = 'FFFF00'		# setting Temp1 area colour yellow

	elif grVal == 'Humi':
		gPar['nmLn'] = 1			# number of lines per graph
		gPar['grTi'] = 'Relative humidity'
		gPar['ds0'] = 'Humi0'
		gPar['lnNm0'] = 'Rel. (BME280) humidity'
		gPar['gTxt0'] = 'Current relative humidity'
		gPar['yUni'] = '%'			# unit string for y-axis label
		gPar['cTxt'] = ""			# If empty, i.e. = "", no comment will be printed on graph
		gPar['lCl0'] = '00008B'		# setting Temp0 line colour dark blue
		gPar['aCl0'] = '0000FF'		# setting Temp0 area colour blue

	elif grVal == 'Dew':
		gPar['nmLn'] = 1				# number of lines per graph
		gPar['grTi'] = 'Dew point'
		gPar['ds0'] = grVal
		gPar['lnNm0'] = 'Dew point calculated from BME280 temp & humi'
		gPar['gTxt0'] = 'Current Dew point'
		gPar['yUni'] = '*C'				# unit string for y-axis label
		gPar['lCl0'] = '00CD00'			# setting line colour: green
		gPar['aCl0'] = ""				# setting area colour empty
			
	elif grVal == 'Speed':
		gPar['nmLn'] = 2				# number of lines per graph
		gPar['grTi'] = 'Wind speed'
		gPar['ds0'] = 'Speed'
		gPar['ds1'] = 'SpeedMax'
		gPar['lnNm0'] = 'Cur wind speed'
		gPar['lnNm1'] = 'Max wind speed'
		gPar['gTxt0'] = 'Current wind speed'
		gPar['gTxt1'] = "Today's max wind speed"
		gPar['yUni'] = 'km/h'			# unit string for y-axis label
		gPar['cTxt'] = ""				# If empty, i.e. = "", no comment will be printed on graph
		gPar['lCl0'] = 'CDCD00'			# setting cur Speed line colour dark yellow
		gPar['lCl1'] = '0000FF'			# setting max Speed line colour blue
		gPar['aCl0'] = 'FFFF00'			# setting cur Speed area colour yellow
		gPar['aCl1'] = '87CEFF'			# setting max Speed area colour skyblue1

	elif grVal == 'Dir':
		gPar['nmLn'] = 1				# number of lines per graph
		gPar['grTi'] = 'Wind direction'
		gPar['ds0'] = grVal
		gPar['lnNm0'] = gPar['grTi']
		gPar['gTxt0'] = gPar['lnNm0']
		gPar['yUni'] = 'deg'			# unit string for y-axis label
		gPar['lCl0'] = 'B03060'			# setting line colour
		gPar['aCl0'] = ""				# setting area colour empty

		if varVal == 0.0:
			strVarVal = 'N'
		elif varVal == 45.0:
			strVarVal = 'NO'
		elif varVal == 90.0:
			strVarVal = 'O'
		elif varVal == 135.0:
			strVarVal = 'SO'
		elif varVal == 180.0:
			strVarVal = 'S'
		elif varVal == 225.0:
			strVarVal = 'SW'
		elif varVal == 270.0:
			strVarVal = 'W'
		elif varVal == 315.0:
			strVarVal = 'NW'
		else:
			strVarVal = 'No valid Dir'

	else:
		print ('No valid input for graph value')

	# Calling rrdGraph function
	rrdGraph(gPar)

# End of airGraphs function definition aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa

# Function for creating rain graphs rrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrr

def rainGraph(grVal, grType, varVal):			# NOTE: reqires additional input variable "subTilt"
	# Possible values for grVal are: 'Rain'
	# Possible values for grType are: 'Chour', 'Cday', 'Cweek', 'Cmonth', 'Cyear', 'Phour', 'Pday', 'Pweek', 'Pmonth', 'Pyear'
	# varVal must be a float or integer variable
	subTilt = varVal							# Here "varVal" is used for variable subTilt (number of tilts to subtract for a certaion time span) and used in gPar['rpnX0']

	# Constants needed to calculate rain vulues
	mmPerTilt = 0.2794									# [mm/tilt] 0 constant given by rain sensor

	gPar = {}											# Declaring gPar as local dictionary

	# Common graph parameters for all rainGraphs
	gPar['grVl'] = grVal								# grValue
	gPar['grTp'] = grType
	gPar['vrVl'] = varVal								# CAUTION NOT YET defined
	gPar['ds0'] = 'Tilt'
	gPar['dbNm0'] = "rainDat"							# NOTE: All rainGraphs have the same RRD database name e.g. "rainDat", etc. => dbFile0 = gPar['dbNm0'] + ".rrd"
	gPar['dbNm1'] = "rainDat"							# NOTE: All rainGraphs have the same RRD database name e.g. "rainDat", etc. => dbFile0 = gPar['dbNm0'] + ".rrd"
#	gPar['grPa'] = "/var/www/html/testGra/"				# NOTE: All rainGraphs have the same path to folder where graph ist stored e.g. '/var/www/html/testGra/'
	gPar['grPa'] = "/var/www/html/rainGra/"				# NOTE: All rainGraphs have the same path to folder where graph ist stored e.g. '/var/www/html/rainGra/'
	gPar['rpnX0'] = '%s,-,%s,*' %(subTilt, mmPerTilt)	# RPN Expression to change original value for display
	gPar['rpnX1'] = '1,*'								# RPN Expression to change original value for display: '1,*' leaves original values unchanged
	###	Originally "CDEF:%s=Tilt,%s,-,%s,*" %(grVal, subTilt, mmPerTilt)	# Rain=Tilt,subTilt,-,0.2794,*	i.e. "rainFall = (tiltRain - subTilt)*mmPerTilt"

	# Creating 10 separate graphs

	# Defining graph parameters using function "graphTypeParameters" and creating graphs
	gPar['grAd'], gPar['stTm'], gPar['cFnc'] = graphTypeParameters(grType)
	
	# More common graph parameters for all rainGraphs
	gPar['nmLn'] = 1							# number of lines per graph
	gPar['cFnc'] = "MAX"						# Setting CF (consolidation function)
	gPar['grTi'] = 'Rainfall'
	gPar['lnNm0'] = "Rainfall"
	gPar['gTxt0'] = "Amount of rainfall"
	gPar['yUni'] = 'mm'							# unit string for y-axis label
	gPar['lCl0'] = 'B03060'						# setting line colour

	# Calling rrdGraph function
	rrdGraph(gPar)
# End of rainGraphs function definition rrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrr

# Function for creating drops graphs yyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyy

def dropsGraph(grVal, grType, varVal):
	# Possible values for grVal are: 'Sys'
	# Possible values for grType are: 'Hourly', '2Hourly', 'Daily', 'Weekly', 'Monthly'
	# varVal must be a float or integer variable
	strVarVal = "%4.2f" % varVal				# Can be used to enter into a text string

	gPar = {}									# Declaring gPar as dictionary

	# Common graph parameters for all dropsGraphs
	gPar['grVl'] = grVal
	gPar['grTp'] = grType
	gPar['vrVl'] = varVal						# CAUTION NOT YET defined
	gPar['dbNm0'] = "rainDat"					# NOTE: All sysGraphs have the same RRD database name e.g. "airDat", etc. => dbFile0 = gPar['dbNm0'] + ".rrd"
	gPar['dbNm1'] = "rainDat"					# NOTE: All sysGraphs have the same RRD database name e.g. "airDat", etc. => dbFile0 = gPar['dbNm0'] + ".rrd"
#	gPar['grPa'] = "/var/www/html/testGra/"		# NOTE: All sysGraphs have the same path to folder where graph ist stored e.g. '/var/www/html/testGra/'
	gPar['grPa'] = "/var/www/html/rainGra/"		# NOTE: All sysGraphs have the same path to folder where graph ist stored e.g. '/var/www/html/sysGra/'
	gPar['rpnX0'] = '1,-,ABS'					# RPN Expression to change original value for display: '1,*' leaves original values unchanged
	gPar['rpnX1'] = '1,-,ABS'					# RPN Expression to change original value for display: '1,*' leaves original values unchanged

	# Creating 4 separate graphs

	# Defining graph parameters using function "graphTypeParameters" and creating graphs
	gPar['grAd'], gPar['stTm'], gPar['cFnc'] = graphTypeParameters(grType)
		
	# Values for graphs with 2 lines (w/o comment)
	if grVal == 'Drops':
		gPar['nmLn'] = 2						# number of lines per graph
		gPar['cFnc'] = "MAX"
		gPar['grTi'] = 'Raining and rain intensity'
		gPar['ds0'] = 'Yesno'
		gPar['ds1'] = 'Int'
		gPar['lnNm0'] = 'Raining? (1.0 = Yes / 0.0 = No)'				# IMPORTANT: Absolutely NO colons ":" in text variables!!
		gPar['lnNm1'] = 'Rain intensity (Scale 0.0 .. 1.0)'
		gPar['gTxt0'] = 'Currently raining'		# IMPORTANT: Absolutely NO colons ":" in text variables!!
		gPar['gTxt1'] = 'Current intensity'		# IMPORTANT: Absolutely NO colons ":" in text variables!!
		gPar['yUni'] = ""						# unit string for y-axis label
		gPar['cTxt'] = ""						# If empty, i.e. = "", no comment will be printed on graph
		gPar['lCl0'] = '8B0000'					# setting CPU Temp line colour dark red
		gPar['lCl1'] = '0000FF'					# setting inside Temp line colour blue
		gPar['aCl0'] = 'FF4500'					# setting CPU Temp area colour orange red
		gPar['aCl1'] = '00BBFF'					# setting inside Temp area colour light blue

	else:
		print ('No valid input for graph value')


		# Calling rrdGraph function
	rrdGraph(gPar)
# End of dropsGraphs function definition yyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyy

# Function for creating system graphs yyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyy

def sysGraph(grVal, grType, varVal):
	# Possible values for grVal are: 'Sys'
	# Possible values for grType are: 'Hourly', '2Hourly', 'Daily', 'Weekly', 'Monthly'
	# varVal must be a float or integer variable
	strVarVal = "%4.2f" % varVal				# Can be used to enter into a text string

	gPar = {}									# Declaring gPar as dictionary

	# Common graph parameters for all sysGraphs
	gPar['grVl'] = grVal
	gPar['grTp'] = grType
	gPar['vrVl'] = varVal						# CAUTION NOT YET defined
	gPar['dbNm0'] = "sysDat"					# NOTE: All sysGraphs have the same RRD database name e.g. "airDat", etc. => dbFile0 = gPar['dbNm0'] + ".rrd"
	gPar['dbNm1'] = "sysDat"					# NOTE: All sysGraphs have the same RRD database name e.g. "airDat", etc. => dbFile0 = gPar['dbNm0'] + ".rrd"
#	gPar['grPa'] = "/var/www/html/testGra/"		# NOTE: All sysGraphs have the same path to folder where graph ist stored e.g. '/var/www/html/testGra/'
	gPar['grPa'] = "/var/www/html/sysGra/"		# NOTE: All sysGraphs have the same path to folder where graph ist stored e.g. '/var/www/html/sysGra/'
	gPar['rpnX0'] = '1,*'						# RPN Expression to change original value for display: '1,*' leaves original values unchanged
	gPar['rpnX1'] = '1,*'						# RPN Expression to change original value for display: '1,*' leaves original values unchanged

	# Creating 4 separate graphs

	# Defining graph parameters using function "graphTypeParameters" and creating graphs
	gPar['grAd'], gPar['stTm'], gPar['cFnc'] = graphTypeParameters(grType)
		
	# Values for graphs with 2 lines (w/o comment)
	if grVal == 'Sys':
		gPar['nmLn'] = 2						# number of lines per graph
		gPar['grTi'] = 'RPi 2 CPU and inbox temperature'
		gPar['ds0'] = 'CPU2'
		gPar['ds1'] = 'Temp2'
		gPar['lnNm0'] = 'RPi 2 CPU temperature'
		gPar['lnNm1'] = 'Inbox (DS18B20-2) air temperature'
		gPar['gTxt0'] = 'Current RPi 2 CPU temperature'
		gPar['gTxt1'] = 'Current inbox (DS18B20-2) air temperature'
		gPar['yUni'] = '*C'						# unit string for y-axis label
		gPar['cTxt'] = ""						# If empty, i.e. = "", no comment will be printed on graph
		gPar['lCl0'] = '8B0000'					# setting CPU Temp line colour dark red
		gPar['lCl1'] = '0000FF'					# setting inside Temp line colour blue
		gPar['aCl0'] = 'FF4500'					# setting CPU Temp area colour orange red
		gPar['aCl1'] = '00BBFF'					# setting inside Temp area colour light blue

	else:
		print ('No valid input for graph value')

	# Calling rrdGraph function
	rrdGraph(gPar)
# End of sysGraphs function definition yyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyy

# Function for creating sol graphs sssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssss

def solGraph(grVal, grType, varVal):
	# Possible values for grVal currently are: 'Flux', 'LuxX', 'Lux'
	# Possible values for grType are: 'Hourly',  '2Hourly', 'Daily', 'Weekly', 'Monthly'
	# varVal must be a float or integer variable
	# Setting values common to all solGraphs
	strVarVal = "%4.0f" % varVal				# Here "varVal" is used only in "Lux" graph for threshold Lux value 'sunThresh' to measure sunshine duration

	gPar = {}									# Declaring gPar as local dictionary

	# Common graph parameters for all solGraphs
	gPar['grVl'] = grVal
	gPar['grTp'] = grType
	gPar['vrVl'] = varVal						# CAUTION NOT YET defined
	gPar['dbNm0'] = "solDat"					# NOTE: All solGraphs have the same RRD database name e.g. "airDat", etc. => dbFile0 = gPar['dbNm0'] + ".rrd"
	gPar['dbNm1'] = "solDat"					# NOTE: All solGraphs have the same RRD database name e.g. "airDat", etc. => dbFile0 = gPar['dbNm0'] + ".rrd"
#	gPar['grPa'] = "/var/www/html/testGra/"		# NOTE: All solGraphs have the same path to folder where graph ist stored e.g. '/var/www/html/testGra/'
	gPar['grPa'] = "/var/www/html/solGra/"		# NOTE: All solGraphs have the same path to folder where graph ist stored e.g. '/var/www/html/solGra/'
	gPar['rpnX0'] = '1,*'						# RPN Expression to change original value for display: '1,*' leaves original values unchanged
	gPar['rpnX1'] = '1,*'						# RPN Expression to change original value for display: '1,*' leaves original values unchanged

	# Creating 4 separate graphs

	# Defining graph parameters using function "graphTypeParameters" and creating graphs
	gPar['grAd'], gPar['stTm'], gPar['cFnc'] = graphTypeParameters(grType)
		
	# Values for graphs with 2 lines plus areas (w/o comment)
	if grVal == 'Flux':
		gPar['nmLn'] = 2									# number of lines per graph
		gPar['grTi'] = 'Solar illuminance (GA1A12S202-0 and GA1A12S202-1, raw data)'
		gPar['ds0'] = 'Flux0'
		gPar['ds1'] = 'Flux1'
#		gPar['lnNm0'] = 'Illuminance from GA1A12S202-0'
		gPar['lnNm0'] = 'GA1A12S202-0 not connected'
		gPar['lnNm1'] = 'Illuminance from GA1A12S202-1'
#		gPar['gTxt0'] = 'Current Illuminance (GA1..-0)'
		gPar['gTxt0'] = 'GA1A12S202-0 not connected'
		gPar['gTxt1'] = 'Current Illuminance at solar panel)'
		gPar['yUni'] = 'mV'									# unit string for y-axis label
		gPar['cTxt'] = ""									# If empty, i.e. = "", no comment will be printed on graph
		gPar['lCl0'] = '8B0000'								# setting GA1A12S202-0 line colour dark red
		gPar['lCl1'] = '8B7500'								# setting GA1A12S202-1 line colour dark gold4
		gPar['aCl0'] = 'FF6347'								# setting GA1A12S202-0 area colour tomato red
		gPar['aCl1'] = 'FFD700'								# setting GA1A12S202-1 area colour gold

	# Values for graphs with 2 lines plus areas (with comment for hourly values only)
	elif grVal == 'LuxX':
		gPar['nmLn'] = 2									# "number of lines per graph" --- NOTE: This is a special 2-value graph with calculated Lux values
		gPar['grTi'] = 'Solar illuminance (GA1A12S202-0 and GA1A12S202-1, [Lux])'
		gPar['ds0'] = 'Flux0'
		gPar['ds1'] = 'Flux1'
#		gPar['rpnX0'] = '10,LOG,*,680,/,EXP'				# Make Lux values from Flux values
		gPar['rpnX0'] = '1,*'								##### NOTE: GA1A12S202-0 not connected => No LUX values
		gPar['rpnX1'] = '10,LOG,*,680,/,EXP'				# Make Lux values from Flux values
#		gPar['lnNm0'] = 'Illuminance from GA1A12S202-0'
		gPar['lnNm0'] = 'GA1A12S202-0 not connected'
		gPar['lnNm1'] = 'Illuminance from GA1A12S202-1'
#		gPar['gTxt0'] = 'Current Illuminance (GA1..-0)'
		gPar['gTxt0'] = 'GA1..-0 not connected'
		gPar['gTxt1'] = 'Current Illuminance at solar panel'
		gPar['yUni'] = 'Lux'								# unit string for y-axis label
		if grType == 'Hourly' or grType == '2Hourly':
			gPar['cTxt'] = "       NOTE\: Current threshold for sunshine duration is "+strVarVal+" Lux from GA1A12S202-1"
		else:
			gPar['cTxt'] = ""								# If empty, i.e. = "", no comment will be printed on graph
		gPar['lCl0'] = '8B0000'								# setting GA1A12S202-0 line colour dark red
		gPar['lCl1'] = '8B7500'								# setting GA1A12S202-1 line colour dark gold4
		gPar['aCl0'] = 'FF6347'								# setting GA1A12S202-0 area colour tomato red
		gPar['aCl1'] = 'FFD700'								# setting GA1A12S202-1 area colour gold

	elif grVal == 'Lux':
		gPar['nmLn'] = 1									# "number of lines per graph" --- NOTE: This is a special 2-value graph with calculated Lux values
		gPar['grTi'] = 'Solar illuminance'
		gPar['ds0'] = 'Flux1'
		gPar['rpnX0'] = '10,LOG,*,680,/,EXP'				# Make Lux values from Flux values
		gPar['lnNm0'] = 'Illuminance from GA1A12S202-1'
		gPar['gTxt0'] = 'Current Illuminance at solar panel'
		gPar['yUni'] = 'Lux'								# unit string for y-axis label
		if grType == 'Hourly' or grType == '2Hourly':
			gPar['cTxt'] = "       NOTE\: Current threshold for sunshine duration is "+strVarVal+" Lux from GA1A12S202-1"
		else:
			gPar['cTxt'] = ""								# If empty, i.e. = "", no comment will be printed on graph
		gPar['lCl0'] = '8B7500'								# setting GA1A12S202-1 line colour dark gold4
		gPar['aCl0'] = 'FFD700'								# setting GA1A12S202-1 area colour gold

	# Values for graphs with 1 line (w/o comment)
	elif grVal == 'Uvi':
		gPar['nmLn'] = 1									# number of lines per graph
		gPar['grTi'] = 'Ultraviolet radiation'
		gPar['ds0'] = grVal
		gPar['lnNm0'] = 'UV radiation from ML8511'
		gPar['gTxt0'] = 'Current UV radiation from ML8511'
		gPar['yUni'] = 'W/m2'								# unit string for y-axis label
		gPar['lCl0'] = '00CD00'								# setting line colour: dark green
		gPar['aCl0'] = ""									# setting area colour empty

	else:
		print ('No valid input for graph value')

	# Calling rrdGraph function
	rrdGraph(gPar)
# End of solGraph function definition sssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssssss

# Function for creating day graphs dddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddd

def dayGraph(grVal, grType, varVal):
	# Possible values for grVal are: 'SunT0', 'SunT1', 'RainT0', 'Val1'
	# Possible values for grType are: 'Weekly', 'Monthly', 'Yearly'
	# varVal must be a float or integer variable
	strVarVal = "%4.2f" % varVal							# Can be used to enter into a text string (NOT used!)

	gPar = {}												# Declaring gPar as local dictionary

	# Common graph parameters for all day graphs
	gPar['grVl'] = grVal
	gPar['grTp'] = grType
	gPar['vrVl'] = varVal									# CAUTION NOT YET defined
	gPar['dbNm0'] = "dayDat"								# NOTE: All dayGraphs have the same RRD database name e.g. "dayDat", etc. => dbFile0 = gPar['dbNm0'] + ".rrd"
	gPar['dbNm1'] = "dayDat"								# NOTE: All dayGraphs have the same RRD database name e.g. "dayDat", etc. => dbFile0 = gPar['dbNm0'] + ".rrd"
#	gPar['grPa'] = "/var/www/html/testGra/"					# NOTE: All dayGraphs have the same path to folder where graph ist stored e.g. '/var/www/html/testGra/'
	gPar['grPa'] = "/var/www/html/dayGra/"					# NOTE: All dayGraphs have the same path to folder where graph ist stored e.g. '/var/www/html/dayGra/'
	gPar['rpnX0'] = '3600,/'								# RPN Expression to change original value for display: '3600,/' converts secs into hours
	gPar['rpnX1'] = '3600,/'								# RPN Expression to change original value for display: '1,*' leaves original values unchanged

	# Creating 3 separate graphs 'Weekly', 'Monthly', 'Yearly'

	# Defining graph parameters using function "graphTypeParameters" and creating graphs
	gPar['grAd'], gPar['stTm'], gPar['cFnc'] = graphTypeParameters(grType)

	# More common graph parameters for all day graphs
	gPar['cFnc'] = "MAX"
	gPar['ds0'] = grVal

	# Values for graphs with 1 line (w/o comment)
	if grVal == 'SunT0' or grVal == 'SunT1':
		gPar['nmLn'] = 1									# number of lines per graph
		gPar['grTi'] = 'Sunshine duration'
		gPar['lnNm0'] = 'Sunshine duration'
		gPar['gTxt0'] = 'Sunshine duration'
		gPar['yUni'] = 'hours'								# unit string for y-axis label
		gPar['lCl0'] = 'CDAD00'								# setting line colour: gold3
		gPar['aCl0'] = ""									# setting area colour empty
			
	elif grVal == 'RainT0' or grVal == 'Val1':
		gPar['grVl'] = 'RainT0'
		gPar['nmLn'] = 1									# number of lines per graph
		gPar['grTi'] = 'Rain duration'
		gPar['lnNm0'] = 'Rain duration'
		gPar['gTxt0'] = 'Rain duration'
		gPar['yUni'] = 'hours'								# unit string for y-axis label
		gPar['lCl0'] = '0000CD'								# setting line colour dark blue
		gPar['aCl0'] = ""									# setting area colour empty
			
	elif grVal == 'Dayval':
		gPar['nmLn'] = 2									# number of lines per graph
		gPar['grTi'] = 'Sunshine and rain duration'
		gPar['ds0'] = 'SunT1'
		gPar['ds1'] = 'RainT0'
		gPar['lnNm0'] = 'Sunshine duration'
		gPar['lnNm1'] = 'Rain duration'
		gPar['gTxt0'] = 'Current sunshine duration'
		gPar['gTxt1'] = 'Current rain duration'
		gPar['yUni'] = "hours"								# unit string for y-axis label
		gPar['cTxt'] = ""									# If empty, i.e. = "", no comment will be printed on graph
		gPar['lCl0'] = '8B7500'								# setting sunshine duration line colour gold4
		gPar['lCl1'] = '0000FF'								# setting rain duration line colour blue
		gPar['aCl0'] = 'FFD700'								# setting sunshine duration area colour gold
		gPar['aCl1'] = '00BBFF'								# setting rain duration area colour light blue

	else:
		print ('No valid input for graph value')

	# Calling rrdGraph function
	rrdGraph(gPar)
# End of day graphs function definition ddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddd

# Function for creating max graphs xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

def maxGraph(grVal, grType, varVal):
	### Possible values for grVal are: 'Temp0', 'Pres0', 'Humi0', 'Speed', 'Flux0', 'Uvi', 'Pcurr', 'Bvolt', 'Bcurr'		NOT implemented yet
	# Possible values for grVal are: 'Temp0', 'Pres0', 'Humi0', 'Speed', 'Flux0'
	# Possible values for grType are: 'Weekly', 'Monthly', 'Yearly'
	# varVal must be a float or integer variable
	strVarVal = "%4.2f" % varVal				# Can be used to enter into a text string (NOT used!)

	gPar = {}									# Declaring gPar as local dictionary

	# Common graph parameters for all maxGraphs
	gPar['grVl'] = grVal						# 'Temp0', etc.
	gPar['grTp'] = grType						# 'Hourly', etc.
	gPar['vrVl'] = varVal						# CAUTION NOT YET defined - NOT used
	gPar['dbNm0'] = "maxDat"					# NOTE: All maxGraphs have the same RRD database name e.g. "maxDat", etc. => dbFile0 = gPar['dbNm0'] + ".rrd"
	gPar['dbNm1'] = "maxDat"					# NOTE: All maxGraphs have the same RRD database name e.g. "maxDat", etc. => dbFile0 = gPar['dbNm0'] + ".rrd"
#	gPar['grPa'] = "/var/www/html/testGra/"		# NOTE: All maxGraphs have the same path to folder where graph ist stored e.g. '/var/www/html/testGra/'
	gPar['grPa'] = "/var/www/html/maxGra/"		# NOTE: All maxGraphs have the same path to folder where graph ist stored e.g. '/var/www/html/maxGra/'
	gPar['rpnX1'] = '1,*'						# RPN Expression to change original value for display: '1,*' leaves original values unchanged

	# Creating 3 separate graphs 'Weekly', 'Monthly', 'Yearly'

	# Defining graph parameters using function "graphTypeParameters" and creating graphs
	gPar['grAd'], gPar['stTm'], gPar['cFnc'] = graphTypeParameters(grType)

	# More common graph parameters for all maxGraphs
	gPar['cFnc'] = "MAX"
	gPar['ds0'] = grVal							# MUST correxpond to rrd database!
	
	# Values for graphs with 1 line
	if grVal == 'Temp0':
		gPar['rpnX0'] = '1,*'					# RPN Expression to change original value for display: '1,*' leaves original values unchanged
		gPar['nmLn'] = 1						# number of lines per graph
		gPar['grTi'] = 'Maximum temperature'
		gPar['lnNm0'] = 'Maximum temperature'
		gPar['gTxt0'] = 'Maximum temperature'
		gPar['yUni'] = '*C'						# unit string for y-axis label
		gPar['lCl0'] = 'CD0000'					# setting line colour: dark red
		gPar['aCl0'] = ""						# setting area colour empty
			
	elif grVal == 'Pres0':
		gPar['rpnX0'] = '1,*'					# RPN Expression to change original value for display: '1,*' leaves original values unchanged
		gPar['nmLn'] = 1						# number of lines per graph
		gPar['grTi'] = 'Maximum air pressure'
		gPar['lnNm0'] = 'Maximum air pressure'
		gPar['gTxt0'] = 'Maximum air pressure'
		gPar['yUni'] = 'hPa'					# unit string for y-axis label
		gPar['lCl0'] = '00CD00'					# setting line colour dark green
		gPar['aCl0'] = ""						# setting area colour empty
			
	elif grVal == 'Humi0':
		gPar['rpnX0'] = '1,*'					# RPN Expression to change original value for display: '1,*' leaves original values unchanged
		gPar['nmLn'] = 1						# number of lines per graph
		gPar['grTi'] = 'Maximum humidity'
		gPar['lnNm0'] = 'Maximum humidity'
		gPar['gTxt0'] = 'Maximum humidity'
		gPar['yUni'] = '%'						# unit string for y-axis label
		gPar['lCl0'] = '0000CD'					# setting line colour dark blue
		gPar['aCl0'] = ""						# setting area colour empty
			
	elif grVal == 'Speed':
		gPar['rpnX0'] = '1,*'					# RPN Expression to change original value for display: '1,*' leaves original values unchanged
		gPar['nmLn'] = 1						# number of lines per graph
		gPar['grTi'] = 'Maximum wind speed'
		gPar['lnNm0'] = 'Maximum wind speed'
		gPar['gTxt0'] = 'Maximum wind speed'
		gPar['yUni'] = 'km/h'					# unit string for y-axis label
		gPar['lCl0'] = 'CD00CD'					# setting line colour dark magenta
		gPar['aCl0'] = ""						# setting area colour empty
			
	elif grVal == 'Flux0':
		gPar['rpnX0'] = '10,LOG,*,680,/,EXP'	# Make Lux values from Flux values
		gPar['nmLn'] = 1						# number of lines per graph
		gPar['grTi'] = 'Maximum illuminance'
		gPar['lnNm0'] = 'Maximum illuminance'
		gPar['gTxt0'] = 'Maximum illuminance'
		gPar['yUni'] = 'Lux'					# unit string for y-axis label
		gPar['lCl0'] = 'CDCD00'					# setting line colour yellow
		gPar['aCl0'] = ""						# setting area colour empty

	else:
		print ('No valid input for graph value')

	# Calling rrdGraph function
	rrdGraph(gPar)
# End of max graphs function definition xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

def minGraph(grVal, grType, varVal):
	### Possible values for grVal are: 'Temp0', 'Pres0', 'Humi0', 'Speed', 'Flux0', 'Uvi', 'Pcurr', 'Bvolt', 'Bcurr'		NOT implemented yet
	# Possible values for grVal are: 'Temp0', 'Pres0', 'Humi0'
	# Possible values for grType are: 'Weekly', 'Monthly', 'Yearly'
	# varVal must be a float or integer variable
	strVarVal = "%4.2f" % varVal				# Can be used to enter into a text string (NOT used!)

	gPar = {}									# Declaring gPar as local dictionary

	# Common graph parameters for all maxGraphs
	gPar['grVl'] = grVal						# 'Temp0', etc.
	gPar['grTp'] = grType						# 'Hourly', etc.
	gPar['vrVl'] = varVal						# CAUTION NOT YET defined - NOT used
	gPar['dbNm0'] = "minDat"					# NOTE: All minGraphs have the same RRD database name e.g. "minDat", etc. => dbFile0 = gPar['dbNm0'] + ".rrd"
	gPar['dbNm1'] = "minDat"					# NOTE: All minGraphs have the same RRD database name e.g. "minDat", etc. => dbFile0 = gPar['dbNm0'] + ".rrd"
#	gPar['grPa'] = "/var/www/html/testGra/"		# NOTE: All minGraphs have the same path to folder where graph ist stored e.g. '/var/www/html/testGra/'
	gPar['grPa'] = "/var/www/html/minGra/"		# NOTE: All minGraphs have the same path to folder where graph ist stored e.g. '/var/www/html/maxGra/'
	gPar['rpnX1'] = '1,*'						# RPN Expression to change original value for display: '1,*' leaves original values unchanged

	# Creating 3 separate graphs 'Weekly', 'Monthly', 'Yearly'

	# Defining graph parameters using function "graphTypeParameters" and creating graphs
	gPar['grAd'], gPar['stTm'], gPar['cFnc'] = graphTypeParameters(grType)

	# More common graph parameters for all maxGraphs
	gPar['cFnc'] = "MIN"
	gPar['ds0'] = grVal							# MUST correxpond to rrd database!
	
	# Values for graphs with 1 line
	if grVal == 'Temp0':
		gPar['rpnX0'] = '1,*'					# RPN Expression to change original value for display: '1,*' leaves original values unchanged
		gPar['nmLn'] = 1						# number of lines per graph
		gPar['grTi'] = 'Minimum temperature'
		gPar['lnNm0'] = 'Minimum temperature'
		gPar['gTxt0'] = 'Minimum temperature'
		gPar['yUni'] = '*C'						# unit string for y-axis label
		gPar['lCl0'] = 'CD0000'					# setting line colour: dark red
		gPar['aCl0'] = ""						# setting area colour empty
			
	elif grVal == 'Pres0':
		gPar['rpnX0'] = '1,*'					# RPN Expression to change original value for display: '1,*' leaves original values unchanged
		gPar['nmLn'] = 1						# number of lines per graph
		gPar['grTi'] = 'Minimum air pressure'
		gPar['lnNm0'] = 'Minimum air pressure'
		gPar['gTxt0'] = 'Minimum air pressure'
		gPar['yUni'] = 'hPa'					# unit string for y-axis label
		gPar['lCl0'] = '00CD00'					# setting line colour dark green
		gPar['aCl0'] = ""						# setting area colour empty
			
	elif grVal == 'Humi0':
		gPar['rpnX0'] = '1,*'					# RPN Expression to change original value for display: '1,*' leaves original values unchanged
		gPar['nmLn'] = 1						# number of lines per graph
		gPar['grTi'] = 'Minimum humidity'
		gPar['lnNm0'] = 'Minimum humidity'
		gPar['gTxt0'] = 'Minimum humidity'
		gPar['yUni'] = '%'						# unit string for y-axis label
		gPar['lCl0'] = '0000CD'					# setting line colour dark blue
		gPar['aCl0'] = ""						# setting area colour empty
			
	else:
		print ('No valid input for graph value')

	# Calling rrdGraph function
	rrdGraph(gPar)
# End of min graphs function definition xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

# Function for getting minutes since start of current period: hour, day, week, month, year mmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmm

def minSinceStartOfPeriod():
	# Function returning minutes since start of current period: hour, day, week, month, year
	minStHour = dtdt.now().minute								# Minutes since start of current hour
	minStDay = dtdt.now().hour*60 + minStHour					# Minutes since start of current day
	minStWeek = dtdt.now().weekday()*24*60 + minStDay			# Minutes since start of current week
	minStMonth = (dtdt.now().day-1)*24*60 + minStDay			# Minutes since start of current month
	minStYear = (dtdt.now().month-1)*30*24*60 + minStMonth		# Minutes since start of current year
	
	return minStHour, minStDay, minStWeek, minStMonth, minStYear

# End of minSinceStartOfPeriod function definition mmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmm

# Function for returning graphType (i.e. time span) dependent parameters tttttttttttttttttttttttttttttttttttttttttttttttttttttttttttttttttttttttttttttttttttttttttt

def graphTypeParameters(graphType):
	# Function returning graph parameters depending on time span of graph i.e. graphType: 'Hourly', '2Hourly', 'Daily', 'Weekly', 'Monthly', 'Yearly', 'Phour'
	# Function returning graph parameters depending on time span of graph i.e. graphType: 'Phour', 'P2hours', 'Pday', 'Pweek', 'Pmonth', 'Pyear', 'Chour', 'C2hours', 'Cday', 'Cweek', 'Cmonth', 'Cyear'

	if graphType == 'Hourly':
		graphTitleAd = 'Preceding hour'		# Added text to title text
		startTime = '-1hour'				# Starting time for graph creation
		consFunc = "MAX"					# Consolidation function

	elif graphType == '2Hourly':
		graphTitleAd = 'Preceding 2 hours'	# Added text to title text
		startTime = '-2hours'				# Starting time for graph creation
		consFunc = "MAX"					# Consolidation function

	elif graphType == 'Daily':
		graphTitleAd = 'Preceding 24 hours'
		startTime = '-1day'
		consFunc = "MAX"

	elif graphType == 'Weekly':
		graphTitleAd = 'Preceding 7 days'
		startTime = '-1week'
		consFunc = "AVERAGE"

	elif graphType == 'Monthly':
		graphTitleAd = 'Preceding 30 days'
		startTime = '-1month'
		consFunc = "AVERAGE"

	elif graphType == 'Yearly':
		graphTitleAd = 'Preceding 12 months'
		startTime = '-1year'
		consFunc = "AVERAGE"
	
	elif graphType == 'Phour':
		graphTitleAd = 'Preceding hour'		# Added text to title text
		startTime = '-1hour'				# Starting time for graph creation
		consFunc = "MAX"					# Consolidation function

	elif graphType == 'P2hours':
		graphTitleAd = 'Preceding 2 hours'	# Added text to title text
		startTime = '-2hours'				# Starting time for graph creation
		consFunc = "MAX"					# Consolidation function

	elif graphType == 'Pday':
		graphTitleAd = 'Preceding 24 hours'
		startTime = '-1day'
		consFunc = "MAX"

	elif graphType == 'Pweek':
		graphTitleAd = 'Preceding 7 days'
		startTime = '-1week'
		consFunc = "MAX"

	elif graphType == 'Pmonth':
		graphTitleAd = 'Preceding 30 days'
		startTime = '-1month'
		consFunc = "MAX"

	elif graphType == 'Pyear':
		graphTitleAd = 'Preceding 12 months'
		startTime = '-1year'
		consFunc = "MAX"
	
	else:
		# The following graphType values require calculation for minutes since start of current time period
		# Getting minutes since start of current period:  hour, day, week, month, year , using minSinceStartOfPeriod() function

		minChr, minCda, minCwe, minCmo, minCye = minSinceStartOfPeriod()

		if graphType == 'Chour':				# Current hour
			graphTitleAd = 'Current hour'		# Added text to title text
			startTime = '-'+str(minChr)+'min'
			consFunc = "MAX"
		elif graphType == 'Cday':				# Current day
			graphTitleAd = 'Current day'		# Added text to title text
			startTime = '-'+str(minCda)+'min'
			consFunc = "MAX"
		elif graphType == 'Cweek':				# Current week
			graphTitleAd = 'Current week'		# Added text to title text
			startTime = '-'+str(minCwe)+'min'
			consFunc = "MAX"
		elif graphType == 'Cmonth':				# Current month
			graphTitleAd = 'Current month'		# Added text to title text
			startTime = '-'+str(minCmo)+'min'
			consFunc = "MAX"
		elif graphType == 'Cyear':				# Current year
			graphTitleAd = 'Current year'		# Added text to title text
			startTime = '-'+str(minCye)+'min'
			consFunc = "MAX"
		else:
			print "No valid input for graphType (time span)", graphType

	# This function returns: graphTitleAd = Text after graphTitle, startTime = time at which graph starts (NOTE: all graphs end now), 
	# and consFunc = consolitation function used for this graph
#	return (graphTitleAd, startTime, consFunc)	# Returns a tuple
	return graphTitleAd, startTime, consFunc	# Returns thre values

# End of Function for returning time span dependent parameters tttttttttttttttttttttttttttttttttttttttttttttttttttttttttttttttttttttttttttttttttttttttttt

# Function for creating rrd graphs rrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrr
def rrdGraph(gPa):
	# NOTE: gPa is a dictionary: the only valid value is the gPar dictionary created in all different graph functions  xyzGraph(...)
	# Common values for all rrdGraphs
	grWidth = 600						# value for graph width in nr of pixels (integer number): default = 400
	# grHeight = 100					# value for graph height in nr of pixels (integer number): default = 100
#	print "Length of gPa = ", len(gPa)	# Check printing
#	print 'gPa = ',gPa					# Check printing

	# Setting local values used for both 1 line and 2 line graphs
	dbFile0 = gPa['dbNm0'] + ".rrd"
	dbFile1 = gPa['dbNm1'] + ".rrd"
	if gPa['yUni'] != '%':
		pUni0 = gPa['yUni']				# unit string for value in GPRINT
		pUni1 = gPa['yUni']				# unit string for value in GPRINT
	else:
		pUni0 = '%%'					# unit string for value in GPRINT
		pUni1 = '%%'					# unit string for value in GPRINT

	# Graph with 1 displayed CALCULATED value: STANDARD 1 LINE GRAPH W/O AREA FILL COLOUR
	if gPa['nmLn'] == 1 and gPa['grVl'] != "Rain" and gPa['aCl0'] == "":
		rrdtool.graph("%s%s%s%s.png" %(gPa['grPa'],gPa['dbNm0'],gPa['grVl'],gPa['grTp']),	# /var/www/html/solGra/solDatUviHourly.png
			"--start", "%s" %(gPa['stTm']),
			"--title=%s: %s" %(gPa['grTi'], gPa['grAd']),
			"--vertical-label=%s" %(gPa['yUni']),
			"-w %d" %(grWidth),
#			"-u 1.0",									# NOT good for standard graphs!		# y-scaling goes at least up to 1.0
#			"-l 0.0",									# NOT good for standard graphs!		# y-scaling always starts at 0.0 or lower
			"--alt-autoscale",
			"--alt-y-grid",
			"DEF:oriVal=%s:%s%s:%s" %(dbFile0, gPa['dbNm0'], gPa['ds0'], gPa['cFnc']),		# e.g. Uvi=solDat.rrd:solDatUvi:MAX
			"CDEF:calcVal=oriVal,%s" %(gPa['rpnX0']),										# Execute RPN Expression gPa['rpnX0'], e.g. '3600,/' to make hours from seconds
			"LINE2:calcVal#%s:%s" %(gPa['lCl0'], gPa['lnNm0']),								# e.g. calcVal#B03060:Sunshine duration
			"GPRINT:calcVal:LAST:%s = %%2.1lf %s" %(gPa['gTxt0'], pUni0),					# e.g. calcVal:LAST:Sunshine duration = (value) min, with 1 decimal
					)

	# Graph with 1 displayed CALCULATED value: STANDARD 1 LINE GRAPH WITH AREA FILL COLOUR W/O comment
	elif gPa['nmLn'] == 1 and gPa['grVl'] != "Rain" and gPa['aCl0'] != "" and gPa['cTxt'] == "":
		rrdtool.graph("%s%s%s%s.png" %(gPa['grPa'],gPa['dbNm0'],gPa['grVl'],gPa['grTp']),	# /var/www/html/solGra/solDatUviHourly.png
			"--start", "%s" %(gPa['stTm']),
			"--title=%s: %s" %(gPa['grTi'], gPa['grAd']),
			"--vertical-label=%s" %(gPa['yUni']),
			"-w %d" %(grWidth),
#			"-u 1.0",									# NOT good for standard graphs!		# y-scaling goes at least up to 1.0
#			"-l 0.0",									# NOT good for standard graphs!		# y-scaling always starts at 0.0 or lower
			"--alt-autoscale",
			"--alt-y-grid",
			"DEF:oriVal=%s:%s%s:%s" %(dbFile0, gPa['dbNm0'], gPa['ds0'], gPa['cFnc']),		# e.g. Uvi=solDat.rrd:solDatUvi:MAX
			"CDEF:calcVal=oriVal,%s" %(gPa['rpnX0']),										# Execute RPN Expression gPa['rpnX0'], e.g. '3600,/' to make hours from seconds
			"VDEF:lastVal=calcVal,LAST",													# getting last values of set calcVal (using RPN)
			"HRULE:lastVal#%s" %('777777'),
			"AREA:calcVal#%s:%s" %(gPa['aCl0'], gPa['lnNm0']),					
			"LINE1:calcVal#%s" %(gPa['lCl0']),												# e.g. calcVal#B03060:Sunshine duration
			"GPRINT:calcVal:LAST:%s = %%2.1lf %s" %(gPa['gTxt0'], pUni0),					# e.g. calcVal:LAST:Sunshine duration = (value) min, with 1 decimal
					)

	# Graph with 1 displayed CALCULATED value: STANDARD 1 LINE GRAPH WITH AREA FILL COLOUR with comment
	elif gPa['nmLn'] == 1 and gPa['grVl'] != "Rain" and gPa['aCl0'] != "" and gPa['cTxt'] != "":
		rrdtool.graph("%s%s%s%s.png" %(gPa['grPa'],gPa['dbNm0'],gPa['grVl'],gPa['grTp']),	# /var/www/html/solGra/solDatUviHourly.png
			"--start", "%s" %(gPa['stTm']),
			"--title=%s: %s" %(gPa['grTi'], gPa['grAd']),
			"--vertical-label=%s" %(gPa['yUni']),
			"-w %d" %(grWidth),
#			"-u 1.0",									# NOT good for standard graphs!		# y-scaling goes at least up to 1.0
#			"-l 0.0",									# NOT good for standard graphs!		# y-scaling always starts at 0.0 or lower
			"--alt-autoscale",
			"--alt-y-grid",
			"DEF:oriVal=%s:%s%s:%s" %(dbFile0, gPa['dbNm0'], gPa['ds0'], gPa['cFnc']),		# e.g. Uvi=solDat.rrd:solDatUvi:MAX
			"CDEF:calcVal=oriVal,%s" %(gPa['rpnX0']),										# Execute RPN Expression gPa['rpnX0'], e.g. '3600,/' to make hours from seconds
			"VDEF:lastVal=calcVal,LAST",													# getting last values of set calcVal (using RPN)
			"HRULE:lastVal#%s" %('777777'),
			"AREA:calcVal#%s:%s" %(gPa['aCl0'], gPa['lnNm0']),					
			"LINE1:calcVal#%s" %(gPa['lCl0']),												# e.g. calcVal#B03060:Sunshine duration
			"GPRINT:calcVal:LAST:%s = %%2.1lf %s" %(gPa['gTxt0'], pUni0),					# e.g. calcVal:LAST:Sunshine duration = (value) min, with 1 decimal
			"COMMENT:%s" %(gPa['cTxt'])														# difference for graphs with comments!
					)

	# RAIN graph with 1 displayed CALCULATED value: special graph parameters for rainGraphs
	elif gPa['nmLn'] == 1 and gPa['grVl'] == "Rain":										# For calculated values
		rrdtool.graph("%s%s%s%s.png" %(gPa['grPa'],gPa['dbNm0'],gPa['grVl'],gPa['grTp']),	# /var/www/html/rainGra/rainDatRainPhour.png
			"--start", "%s" %(gPa['stTm']),													# -1hour
			"--title=%s: %s" %(gPa['grTi'], gPa['grAd']),									# Rainfall: preceding 2 hours
			"--vertical-label=%s" %(gPa['yUni']),
			"-w %d" %(grWidth),																# 600
			"-u 1.0",									# Needed only for rainGraphs!		# y-scaling goes at least up to 1.0 => special and only for rain graphs
			"-l 0.0",									# Needed only for rainGraphs!		# y-scaling always starts at 0.0 or lower => special for rain graphs
			"--alt-autoscale",
			"--alt-y-grid",
			"DEF:oriVal=%s:%s%s:%s" %(dbFile0, gPa['dbNm0'], gPa['ds0'], gPa['cFnc']),		# Rain=rainDat.rrd:rainDatTilt:MAX
			"CDEF:calcVal=oriVal,%s" %(gPa['rpnX0']),										# calcVal=Rain,subTilt,-,0.2794,*	i.e. "rainFall = (tiltRain - subTilt)*mmPerTilt"  {using RPN}
			"LINE2:calcVal#%s:%s" %(gPa['lCl0'], gPa['lnNm0']),								# calcVal#B03060:Rainfall
			"GPRINT:calcVal:LAST:%s = %%2.1lf %s" %(gPa['gTxt0'], pUni0),					# calcVal:LAST:Today's rainfall = (value) mm, with 1 decimal
					)

	# Graph with 2 displayed CALCULATED values W/O comment
	elif gPa['nmLn'] >= 2 and gPa['cTxt'] == "":											# For calculated values

		# Setting local values used for 2 line graphs only
#		lnColx = gPa['lCl0']																# setting overlap line colour
		arColx = gPa['aCl0']																# setting overlap area colour

		rrdtool.graph("%s%s%s%s.png" %(gPa['grPa'],gPa['dbNm0'],gPa['grVl'],gPa['grTp']),	# /var/www/html/solGra/solDatLuxHourly.png
			"--start", "%s" %(gPa['stTm']),
			"--title=%s: %s" %(gPa['grTi'], gPa['grAd']),
			"--vertical-label=%s" %(gPa['yUni']),
			"-w %d" %(grWidth),
			"--alt-autoscale",
			"--alt-y-grid",
			"DEF:oriVal0=%s:%s%s:%s" %(dbFile0, gPa['dbNm0'], gPa['ds0'], gPa['cFnc']),		# Note: DEF:Lux0=solDat.rrd:solDatFlux0:MAX
			"DEF:oriVal1=%s:%s%s:%s" %(dbFile1, gPa['dbNm1'], gPa['ds1'], gPa['cFnc']),		# Note: DEF:Lux1=solDat.rrd:solDatFlux1:MAX
			"CDEF:calcVal0=oriVal0,%s" %(gPa['rpnX0']),										# Execute RPN Expression gPa['rpnX0']
			"CDEF:calcVal1=oriVal1,%s" %(gPa['rpnX1']),										# Execute RPN Expression gPa['rpnX1']
			"VDEF:lastVal=calcVal0,LAST",													# getting last values of set calcVal0 (using RPN)
			"CDEF:overlap=calcVal0,ABS,calcVal1,ABS,LE,calcVal0,UNKN,IF",					# Calculating overlap value (using RPN); UNKN => now area colour drawn
			"HRULE:lastVal#%s" %('777777'),
			"AREA:calcVal0#%s:%s" %(gPa['aCl0'], gPa['lnNm0']),					
			"AREA:calcVal1#%s:%s\c" %(gPa['aCl1'], gPa['lnNm1']),					
			"AREA:overlap#%s" %(arColx),
			"LINE1:calcVal0#%s" %(gPa['lCl0']),					
			"LINE1:calcVal1#%s" %(gPa['lCl1']),					
			"GPRINT:calcVal0:LAST:%s = %%2.1lf %s"  %(gPa['gTxt0'], pUni0),					# With 1 decimal
			"GPRINT:calcVal1:LAST:%s = %%2.1lf %s"  %(gPa['gTxt1'], pUni1),					# With 1 decimal
					)

	# Graph with 2 displayed CALCULATED values WITH comment
	elif gPa['nmLn'] >=2 and gPa['cTxt'] != "":												# For calculated values

		# Setting local values used for 2 line graphs only
#		lnColx = gPa['lCl0']			# setting overlap line colour
		arColx = gPa['aCl0']			# setting overlap area colour

		rrdtool.graph("%s%s%s%s.png" %(gPa['grPa'],gPa['dbNm0'],gPa['grVl'],gPa['grTp']),	# /var/www/html/solGra/solDatLuxHourly.png
			"--start", "%s" %(gPa['stTm']),
			"--title=%s: %s" %(gPa['grTi'], gPa['grAd']),
			"--vertical-label=%s" %(gPa['yUni']),
			"-w %d" %(grWidth),
			"--alt-autoscale",
			"--alt-y-grid",
			"DEF:oriVal0=%s:%s%s:%s" %(dbFile0, gPa['dbNm0'], gPa['ds0'], gPa['cFnc']),		# Note: DEF:Lux0=solDat.rrd:solDatFlux0:MAX
			"DEF:oriVal1=%s:%s%s:%s" %(dbFile1, gPa['dbNm1'], gPa['ds1'], gPa['cFnc']),		# Note: DEF:Lux1=solDat.rrd:solDatFlux1:MAX
			"CDEF:calcVal0=oriVal0,%s" %(gPa['rpnX0']),										# Execute RPN Expression gPa['rpnX0']
			"CDEF:calcVal1=oriVal1,%s" %(gPa['rpnX1']),										# Execute RPN Expression gPa['rpnX1']
			"VDEF:lastVal=calcVal0,LAST",													# getting last values of set calcVal0 (using RPN)
			"CDEF:overlap=calcVal0,ABS,calcVal1,ABS,LE,calcVal0,UNKN,IF",					# Calculating overlap value (using RPN); UNKN => now area colour drawn 
			"HRULE:lastVal#%s" %('777777'),
			"AREA:calcVal0#%s:%s" %(gPa['aCl0'], gPa['lnNm0']),					
			"AREA:calcVal1#%s:%s\c" %(gPa['aCl1'], gPa['lnNm1']),					
			"AREA:overlap#%s" %(arColx),
			"LINE1:calcVal0#%s" %(gPa['lCl0']),					
			"LINE1:calcVal1#%s" %(gPa['lCl1']),					
			"GPRINT:calcVal0:LAST:%s = %%2.1lf %s"  %(gPa['gTxt0'], pUni0),					# With 1 decimal
			"GPRINT:calcVal1:LAST:%s = %%2.1lf %s"  %(gPa['gTxt1'], pUni1),					# With 1 decimal
			"COMMENT:%s" %(gPa['cTxt'])														# difference for graphs with comments!
					)

	else:
		print ('No valid input for graph creation')
# End of rrd graphs function definition  rrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrr
