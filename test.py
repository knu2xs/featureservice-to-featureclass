"""
Unit testing.
"""
# import modules
import unittest
import rest_utilities as rest
import os.path
import arcpy


class TestFeatureLayerBNSF(unittest.TestCase):

    fl_url = 'http://fragis.frasafety.net/fragis/rest/services/Class1s/MapServer/0'  # BNSF@FRA

    def setUp(self):
        self.fl = rest.FeatureService(self.fl_url)

    def test_get_max_batch(self):
        max_batch = self.fl.properties['maxRecordCount']
        self.assertEqual(max_batch, 1000)

    def test_get_fid_list(self):
        fid_list = self.fl.get_fid_list()
        self.assertEqual(len(fid_list), 16923)

    def test_get_feature_list(self):
        feature_list = self.fl._get_feature_list([101, 102, 103, 104])
        self.assertEqual(len(feature_list), 4)

    def test_save_feature_class(self):
        output_fc_path = os.path.join(os.path.dirname(__file__), 'resources', 'scratch.gdb', 'rail_bnsf')
        if arcpy.Exists(output_fc_path):
            arcpy.Delete_management(output_fc_path)
        self.fl.save_to_feature_class(output_fc_path)
        self.assertTrue(int(arcpy.GetCount_management(output_fc_path)[0]))


class TestFeatureLayerStates(unittest.TestCase):

    fl_url = 'http://services.arcgis.com/P3ePLMYs2RVChkJx/arcgis/rest/services/USA_States_Generalized/FeatureServer/0'

    def setUp(self):
        self.fl = rest.FeatureService(self.fl_url)

    def test_get_max_batch(self):
        max_batch = self.fl.properties['maxRecordCount']
        self.assertEqual(max_batch, 2000)

    def test_get_fid_list(self):
        fid_list = self.fl.get_fid_list()
        self.assertEqual(len(fid_list), 51)

    def test_get_feature_list(self):
        feature_list = self.fl._get_feature_list([33, 34, 35, 36])
        self.assertEqual(len(feature_list), 4)

    def test_save_feature_class(self):
        output_fc_path = os.path.join(os.path.dirname(__file__), 'resources', 'scratch.gdb', 'us_states')
        if arcpy.Exists(output_fc_path):
            arcpy.Delete_management(output_fc_path)
        fc = self.fl.save_to_feature_class(output_fc_path)[0]
        self.assertTrue(int(arcpy.GetCount_management(output_fc_path)[0]))


class TestFeatureLayerLiberiaGeonames(unittest.TestCase):

    fl_url = 'https://services1.arcgis.com/cc7nIINtrZ67dyVJ/arcgis/rest/services/Liberia_Geonames_Points/FeatureServer/0'

    def setUp(self):
        self.fl = rest.FeatureService(self.fl_url)

    def test_get_max_batch(self):
        max_batch = self.fl.properties['maxRecordCount']
        self.assertEqual(max_batch, 1000)

    def test_get_fid_list(self):
        fid_list = self.fl.get_fid_list()
        self.assertEqual(len(fid_list), 6983)

    def test_get_feature_list(self):
        feature_list = self.fl._get_feature_list([101, 102, 103, 104])
        self.assertEqual(len(feature_list), 4)

    def test_save_feature_class(self):
        output_fc_path = os.path.join(os.path.dirname(__file__), 'resources', 'scratch.gdb', 'liberia_geonames')
        if arcpy.Exists(output_fc_path):
            arcpy.Delete_management(output_fc_path)
        self.fl.save_to_feature_class(output_fc_path)
        self.assertTrue(int(arcpy.GetCount_management(output_fc_path)[0]))