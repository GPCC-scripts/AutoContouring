#   RayStation version: 16.0.0.847
#   Created: 29/04/2025
#   by Adam Ryczkowski
#   Name: DLS_nodes_auto
#   Module: Structure definition
#   BackgroundServiceScript

import connect
import os
from datetime import datetime

def hex2bin(hex_string):
	bin_string = ""
	for i in range(1, len(hex_string), 3):
		bin_string += bin(int(hex_string[i:i+2], 16))[2:].zfill(8)
	return bin_string
	
def validCaseName():
	patient = connect.get_current('Patient')
	i = 0
	isValid = False
	nCaseName = 'AC_nodes_' + datetime.now().strftime('%Y%m%d')
	while not isValid:
		isValid = True
		for case in patient.Cases:
			if case.CaseName == nCaseName:
				isValid = False
				i = i+1
				if i > 1:
					nCaseName = nCaseName[:nCaseName.find('_', -4)] + '_' + str(i)
				else:
					nCaseName = nCaseName + '_1'
	return nCaseName
	
def nodesACexecute(hexInput):
	# nodes autocontouring
	input = hex2bin(hexInput)
	
	# input [0:2] - site (010 = nodes)
	nodeList = [[], [], [], ["LN_1A"], ["LN_1B_L"], ["LN_1B_R"], ["LN_2_L"], ["LN_2_R"],
		["LN_3_L"], ["LN_3_R"], ["LN_4A_L"], ["LN_4A_R"], ["LN_4B_L"], ["LN_4B_R"], ["LN_5AB_L"], ["LN_5AB_R"],
		["LN_5C_L"], ["LN_5C_R"], ["LN_6A"], ["LN_6B"], ["LN_7A_L"], ["LN_7A_R"], ["LN_7B_L"], ["LN_7B_R"],
		["LN_Ax_L1_L"], ["LN_Ax_L1_R"], ["LN_Ax_L2_L"], ["LN_Ax_L2_R"], ["LN_Ax_L3_L"], ["LN_Ax_L3_R"], ["LN_Ax_L4_L"], ["LN_Ax_L4_R"],
		["LN_Ax_Pectoral_L"], ["LN_Ax_Pectoral_R"], ["LN_IMN_L"], ["LN_IMN_R"], ["IpsilateralBreast_L"], ["IpsilateralBreast_R"], [], []]
	
	# OARs alias dictonary
	db = connect.get_current("MachineLearningDB")
	info = db.QueryMachineLearningModelInfo()
	for i in info:
		if (i["Name"] == "RSL DLS CT"):
			info = i
			break
	settings = info["Settings"]
	roiNameAlias = settings[settings.find("RoiNameAlias"):]
	roiNameAlias = roiNameAlias.split("{",1)[1]
	roiNameAlias = roiNameAlias.split("}",1)[0]
	oarDict = {}
	while (roiNameAlias.find(",") > 0):
		(key, roiNameAlias) = roiNameAlias.split(":",1)
		(value, roiNameAlias) = roiNameAlias.split(",",1)
		key = key.split('"',2)[1]
		value = value.split('"',2)[1]
		oarDict[key] = value
	(key, roiNameAlias) = roiNameAlias.split(":",1)
	key = key.split('"',2)[1]
	value = roiNameAlias.split('"',2)[1]
	oarDict[key] = value	
	
	# nodes list creation
	roiList = []
	for i in range(3, len(nodeList)):
		if int(input[i]):
			roiList.extend(nodeList[i])
	
	# Deep Learning Segmentation
	examination = connect.get_current('Examination')
	examination.RunDeepLearningSegmentationComposite(ModelNamesAndRoisToInclude={ 'RSL DLS CT': roiList})
		
	# Post processing
	# Case renaming
	case = connect.get_current('Case')
	case.EditCaseInformation(CaseName = validCaseName(), Comments = 'Nodes auto contouring, input: ' + hexInput)
	# case.PatientModel.ToggleExcludeFromExport(ExcludeFromExport=True, RegionOfInterests=["External"], PointsOfInterests=[])
	if int(input[36]):
		case.PatientModel.RegionsOfInterest[oarDict['IpsilateralBreast_L']].Color = 'Red'
		case.PatientModel.RegionsOfInterest[oarDict['IpsilateralBreast_L']].Type = 'CTV'
		case.PatientModel.RegionsOfInterest[oarDict['IpsilateralBreast_L']].Name = 'CTV ' + oarDict['IpsilateralBreast_L']
	if int(input[37]):
		case.PatientModel.RegionsOfInterest[oarDict['IpsilateralBreast_R']].Color = 'Red'
		case.PatientModel.RegionsOfInterest[oarDict['IpsilateralBreast_R']].Type = 'CTV'
		case.PatientModel.RegionsOfInterest[oarDict['IpsilateralBreast_R']].Name = 'CTV ' + oarDict['IpsilateralBreast_R']
		
	
	# save results
	patient = connect.get_current('Patient')
	patient.Save()
	
	# export to ARIA
	case.ScriptableDicomExport(Connection={'Title': 'ARIA'}, RtStructureSetsForExaminations=[examination.Name])
	