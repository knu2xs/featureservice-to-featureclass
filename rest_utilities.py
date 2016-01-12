"""
purpose:        Provide utilities to download all features from a feature service to a local feature class.
dob:            10 Apr 2015
author:         Joel McCune (joel.mccune@gmail.com)
"""
# make sure the local path is included when searching for packages
import os.path
import re
import arcpy
from packages import requests


class FeatureService(object):
    """
    Representation of a feature layer with capabilities to access properties and methods to a REST endpoint.
    """
    def __init__(self, feature_service_url):
        self.url = feature_service_url
        self.properties = self._describe()

    def _get_dict(self, url, query_string):
        """
        Helper method to streamline the process of making calls to the rest endpoint and outputting a dictionary.
        :param query_string: Everything following the ? in the url.
        :return: Dictionary created from the JSON response.
        """
        # create url for rest call
        url = "{0}?{1}".format(url, query_string)

        # make the rest endpoint call, load into a dictionary and return the json result
        return requests.get(url).json()

    def _describe(self):
        """
        Access the properties of the REST service and load the properties into a dictionary object.
        :return: A dictionary of properties loaded directly from the JSON response structure.
        """
        # make a rest call to get the REST endpoint properties
        return self._get_dict(self.url, 'f=json')

    def query(self, query_dict):
        """
        Run a query using a dictionary of key/value pairs corresponding to the query properties for a feature layer.
        This dictionary will be used to construct the query string in the url.
        :param query_dict: Key/value pairs corresponding to the query properties for a feature layer
        :return: Dictionary created from the JSON response to the query.
        """
        # create list of formatted strings
        query_list = ["{0}={1}".format(key, value) for key, value in query_dict.items()]

        # combine elements with an ampersand and preceded by a question mark, run the query and return the dictionary
        return self._get_dict("{0}/query".format(self.url), "&".join(query_list))

    def get_fid_list(self):
        """
        Get a list of all feature ID's for the feature class.
        :return: List of feature ID values for the feature layer.
        """
        # get the dictionary object
        json_dict = self.query({
            'where': '1%3D1',  # 1=1
            'returnIdsOnly': 'true',
            'f': 'json'
        })

        # return the object ID's back as a list
        return json_dict['objectIds']

    def _get_feature_list(self, fid_list):
        """
        Get a list of features for the feature class.
        :fid_list: List of integer values representing the object ID's to be retrieved.
        :return: List of dictionaries for the attributes and geometry.
        """
        # create single string of values separated by commas
        fid_string = ','.join([str(fid) for fid in fid_list])

        # query the REST endpoint and get the features
        rest_dict = self.query({
            'objectIds': fid_string,
            'outFields': '*',  # all fields
            'f': 'json'
        })

        # dictionary to look up geometry types
        geometry_type = {
            'esriGeometryPoint': 'Point',
            'esriGeometryMultipoint': 'MultiPoint',
            'esriGeometryPolyline': 'MultiLineString',
            'esriGeometryPolygon': 'Polygon'
        }

        # list to store features
        feature_list = []

        # helper function to get geometry key
        def get_geometry_json(feature_geometry_dictionary):

            # if the geometry is defined as paths, representing lines, return the geometry
            if 'paths' in feature_geometry_dictionary:
                return feature_geometry_dictionary['paths']

            # if the geometry is defined as loops, representing polygons, return the geometry
            elif 'rings' in feature_geometry_dictionary:
                return feature_geometry_dictionary['rings']

            # if the geometry is defined in terms of x and y, points, return the geometry
            elif 'x' and 'y' in feature_geometry_dictionary:
                return [feature_geometry_dictionary['x'], feature_geometry_dictionary['y']]

        # for every feature returned
        for feature in rest_dict['features']:

            # format the geometry as Esri JSON
            esrijson = {
                'type': geometry_type[rest_dict['geometryType']],
                'coordinates': get_geometry_json(feature['geometry'])
            }

            # create the dictionary with the attributes and geometry and append it to the list
            feature_list.append({
                'attributes': feature['attributes'],
                'geometry': arcpy.AsShape(esrijson)
            })

        # return the feature list
        return feature_list

    def _validate_field(self, field_instance):
        """
        Toss out fields not valid to be processed, either because not wanted or causing too many headaches in
        processing.
        :param field_instance: Field object being tested.
        :return: Boolean indicating if field is valid or not.
        """

        # if the field is an object id, not valid
        if field_instance['type'] == 'esriFieldTypeOID':
            return False

        # if the field is a geometry field, not valid
        elif field_instance['type'] == 'esriFieldTypeGeometry':
            return False

        # if the field name has OBJECTID in the name
        elif re.match(r'^OBJECTID.*', field_instance['name']):
            return False

        # if the field has Shape. in the name
        elif re.match(r'^Shape\..*', field_instance['name']):
            return False

        # although datetime is useful, it also can be a gigantic pain in the ass...yes a bad hack
        # if you know of a better way, please fix it and submit a pull request
        elif field_instance['type'] == 'esriFieldTypeDate':
            return False

        # I don't need them, if you do, please feel free to delete this
        elif field_instance['type'] == 'esriFieldTypeGlobalID':
            return False

        # if it makes it this far, it must be valid
        else:
            return True

    def save_to_feature_class(self, output_feature_class):
        """
        Save the feature service to a feature class.
        :param output_feature_class: Where to save the feature class to with the full path and name.
        :return: Path to feature class.
        """
        # dictionary to look up geometry types
        geometry_type = {
            'esriGeometryPoint': 'POINT',
            'esriGeometryMultipoint': 'MULTIPOINT',
            'esriGeometryPolyline': 'POLYLINE',
            'esriGeometryPolygon': 'POLYGON'
        }

        # create feature class
        fc = arcpy.CreateFeatureclass_management(
            out_path=os.path.dirname(output_feature_class),
            out_name=os.path.basename(output_feature_class),
            geometry_type=geometry_type[self.properties['geometryType']],
            spatial_reference=arcpy.SpatialReference(self.properties['extent']['spatialReference']['latestWkid'])
        )[0]

        # dictionary to look up field types
        field_type = {
            'esriFieldTypeString': 'TEXT',
            'esriFieldTypeFloat': 'FLOAT',
            'esriFieldTypeDouble': 'DOUBLE',
            'esriFieldTypeSmallInteger': 'SHORT',
            'esriFieldTypeInteger': 'LONG',
            'esriFieldTypeDate': 'DATE',
            'esriFieldTypeGlobalID': 'GUID'
        }

        # fields variable for insert cursor later
        insert_field_list = []

        # add fields
        for field in self.properties['fields']:

            # if the field is not the object id or geometry field
            if self._validate_field(field):

                # if this is a text field, look up the length and use it, otherwise just use a blank placeholder
                if field_type[field['type']] == 'TEXT':
                    length = field['length']
                else:
                    length = ""

                # add this field name to the fields name list
                insert_field_list.append(field['name'])

                # add field with properties
                arcpy.AddField_management(
                    in_table=fc,
                    field_name=field['name'],
                    field_type=field_type[field['type']],
                    field_alias=field['alias'],
                    field_length=length,
                )

        # if the max batch query is less than 100, set this to the batch size, otherwise use 100 since retrieving
        # greater than 100 records from feature services backed by enterprise SDE's using ObjectIDs is documented
        # to suffer from performance issues
        if self.properties['maxRecordCount'] > 100:
            batch_size = 100
        else:
            batch_size = self.properties['maxRecordCount']

        # get the list of all feature id's
        fid_list = self.get_fid_list()

        # create a list of lists (redundant?) to use for making query requests to the REST endpoint
        fid_batch_list = [fid_list[i: i + int(batch_size)] for i in range(0, len(fid_list)-1, int(batch_size))]

        # add geometry to the fields list
        insert_field_list.append('SHAPE@')

        # use an insert cursor to insert features
        with arcpy.da.InsertCursor(fc, insert_field_list) as insert_cursor:

            # iterate the batch lists
            for fid_batch in fid_batch_list:

                # make the rest call to get the features
                feature_list = self._get_feature_list(fid_batch)

                # for every feature in the feature list
                for feature in feature_list:

                    # get a list of attribute values using iterator to match up dictionary values matching the fields
                    # being used
                    attribute_list = []

                    # iterate the validated field names
                    for attribute_name in insert_field_list:

                        # do not get geometry
                        if attribute_name != 'SHAPE@':

                            # retrieve the value from the dictionary for the attribute name and add it to the list
                            attribute_list.append(feature['attributes'][attribute_name])

                    # add geometry to the list
                    attribute_list.append(feature['geometry'])

                    # use the insert cursor to insert a record
                    insert_cursor.insertRow(attribute_list)

        # return the path to the feature class
        return fc