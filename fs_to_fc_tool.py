"""
Wrapper providing bindings between library and toolbox.
"""
# import modules
from sys import argv
from rest_utilities import FeatureService

# create feature service object instance
fl = FeatureService(argv[1])

# save the feature layer to a feature class
fl.save_to_feature_class(argv[2])