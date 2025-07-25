#   RayStation version: 16.0.0.847
#   Created: 11/04/2025
#   by Adam Ryczkowski
#   Name: autoSegmentation
#   Module: Structure definition
#   BackgroundServiceScript

import connect
import os
from datetime import datetime
from DLS_oar_auto import oarACexecute
from DLS_nodes_auto import nodesACexecute

def hex2bin(hex_string):
	bin_string = ""
	for i in range(1, len(hex_string), 3):
		bin_string += bin(int(hex_string[i:i+2], 16))[2:].zfill(8)
	return bin_string

# import path
importPath = '//192.168.32.50/StorageSCP_AutoImport/'
# check autocontouring file
patient = connect.get_current('Patient')
acFilePath = importPath + datetime.now().strftime('%Y%m%d') + '__AutoContouringRS__' + patient.PatientID + '/autoContouring.txt'
if os.path.isfile(acFilePath):
	f = open(acFilePath, 'r')
	hexInput = f.readline()
	f.close()
	# select script to perform
	if (hex2bin(hexInput)[0:3] == '111'):
		oarACexecute(hexInput)
		os.remove(acFilePath)
	if (hex2bin(hexInput)[0:3] == '010'):
		nodesACexecute(hexInput)
		os.remove(acFilePath)
