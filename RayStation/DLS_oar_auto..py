#   RayStation version: 16.0.0.847
#   Created: 11/04/2025
#   by Adam Ryczkowski
#   Name: DLS_oar_auto
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
	nCaseName = 'AC_OAR_' + datetime.now().strftime('%Y%m%d')
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
	
def oarACexecute(hexInput):
	# OARs autocontouring
	input = hex2bin(hexInput)
	
	# input [0:2] - site (111 = OARs)
	oarList = [[], [], [], ["Lens_L"], ["Lens_R"], ["Eye_L"], ["Eye_R"], ["OpticChiasm"],
		["OpticNerve_L"], ["OpticNerve_R"], ["LacrimalGland_L"], ["LacrimalGland_R"], ["NasolacrimalDuct_L"], ["NasolacrimalDuct_R"], ["Cochlea_L"], ["Cochlea_R"],
		["Pituitary"], ["Brain"], ["Brainstem"], ["SpinalCord_Full"], ["ParotidGland_L"], ["ParotidGland_R"], ["SubmandibularGland_L"], ["SubmandibularGland_R"],
		["TMJoint_L"], ["TMJoint_R"], ["Mandible"], ["OralCavity"], ["Lips"], ["TongueBase"], ["Larynx_G", "Larynx_SG"], ["ThyroidGland"],
		["CPM"], ["PCM_inf", "PCM_med", "PCM_sup"], ["Lung_L", "Lung_R"], [], [], [], [], [],
		["SpinalCord_Full"], ["Lung_L"], ["Lung_R"], ["Heart_pa_separate"], ["A_LAD"], ["Esophagus"], ["HumeralHead_L"], ["HumeralHead_R"],
		["IpsilateralBreast_L"], ["IpsilateralBreast_R"], ["ThyroidGland"], ["Trachea_1cm_sup_carina"], ["Carina"], ["Bronchus_InterM", "Bronchus_Main_L", "Bronchus_Main_R"], ["Brachial_Plexus_L"], ["Brachial_Plexus_R"],
		["Sternum"], [], [], [], [], [], [], [],
		["Kidney_L"], ["Kidney_R"], ["Stomach"], ["Liver"], ["Pancreas"], ["Spleen"], ["BowelSpc"], [],
		["Femur_Head_L"], ["Femur_Head_R"], ["Anorectum"], ["Bladder"], ["Prostate"], ["SeminalVesicles"], [], [], ]
		
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
	
	# OARs list creation
	roiList = []
	for i in range(3, len(oarList)):
		if int(input[i]): # elemination double structures
			if (i==40): # spinal cord
				if int(input[19]):
					continue
			if (i==41): # lung (L)
				if int(input[34]):
					continue
			if (i==42): # lung (R)
				if int(input[34]):
					continue
			if (i==50): # thyroid gland
				if int(input[31]):
					continue
			roiList.extend(oarList[i])
	
	# Deep Learning Segmentation
	examination = connect.get_current('Examination')
	examination.RunDeepLearningSegmentationComposite(ModelNamesAndRoisToInclude={ 'RSL DLS CT': roiList})
		
	# Post processing
	# Case renaming
	case = connect.get_current('Case')
	case.EditCaseInformation(CaseName = validCaseName(), Comments = 'OARs auto contouring, input: ' + hexInput)
	# OARs
	if ((int(input[41])+int(input[42]))==2): # lungs
		roiPluca = case.PatientModel.CreateRoi(Name='Lungs', Color='Blue', Type='Organ')
		roiPluca.CreateAlgebraGeometry(Examination=examination, Algorithm="Contours", Resolution=0.025, 
			ExpressionA={ 'Operation': "Union", 'SourceRoiNames': [oarDict["Lung_L"], oarDict["Lung_R"]], 'MarginSettings': {'Type': "Expand", 'Superior': 0, 'Inferior': 0, 'Anterior': 0, 'Posterior': 0, 'Right': 0, 'Left': 0}})
	if int(input[34]): # top of the lungs
		roiSzczytyPluc = case.PatientModel.CreateRoi(Name='Lungs', Color='Blue', Type='Organ')
		roiSzczytyPluc.CreateAlgebraGeometry(Examination=examination, Algorithm="Contours", Resolution=0.025, 
			ExpressionA={ 'Operation': "Union", 'SourceRoiNames': [oarDict["Lung_L"], oarDict["Lung_R"]], 'MarginSettings': {'Type': "Expand", 'Superior': 0, 'Inferior': 0, 'Anterior': 0, 'Posterior': 0, 'Right': 0, 'Left': 0}})
		if (int(input[41])==0):
			case.PatientModel.RegionsOfInterest[oarDict['Lung_L']].DeleteRoi()
		if (int(input[42])==0):
			case.PatientModel.RegionsOfInterest[oarDict['Lung_R']].DeleteRoi()
	if int(input[30]): # Larynx
		roiKrtan = case.PatientModel.CreateRoi(Name='Larynx', Color='Yellow', Type='Organ')
		roiKrtan.CreateAlgebraGeometry(Examination=examination, Algorithm="Contours", Resolution=0.025, 
			ExpressionA={ 'Operation': "Union", 'SourceRoiNames': [oarDict["Larynx_G"], oarDict["Larynx_SG"]], 'MarginSettings': {'Type': "Expand", 'Superior': 0, 'Inferior': 0, 'Anterior': 0, 'Posterior': 0, 'Right': 0, 'Left': 0}})
		case.PatientModel.RegionsOfInterest[oarDict['Larynx_G']].DeleteRoi()
		case.PatientModel.RegionsOfInterest[oarDict['Larynx_SG']].DeleteRoi()
		
	
	# save results
	patient = connect.get_current('Patient')
	patient.Save()
	
	# export to ARIA
	case.ScriptableDicomExport(Connection={'Title': 'ARIA'}, RtStructureSetsForExaminations=[examination.Name])
	