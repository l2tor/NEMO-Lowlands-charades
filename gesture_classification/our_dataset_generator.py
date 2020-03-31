from dataset_management.our_import import OurImport
from dataset_management.datamanager import DataManager
from feature_extraction.gesture_feature_extractor import GestureFeatureExtractor
from optparse import OptionParser

# Parse command-line options
parser = OptionParser()
parser.add_option("-i", "--input", dest="input", help="File(s) to use as input to generate a dataset")
parser.add_option("-o", "--output", dest="output", help="Output file for the generated dataset")

(options, args) = parser.parse_args()

importer = OurImport()
loaded_data = importer.load(options.input)

if loaded_data != None:
	output_mgr = DataManager()
	fe = GestureFeatureExtractor()

	# print loaded_data[0][0]
	if isinstance(loaded_data, (list,)):
		for l in loaded_data:
			output_mgr.append(fe.get_gesture_features_as_string(l))
	else:
		output_mgr.append(fe.get_gesture_features_as_string(loaded_data))
		
	output_mgr.save(options.output)