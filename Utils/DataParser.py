from shapely.geometry import Point

class DataParser:
    """
    Class responsible of parsing the user coordinates contained into the HTTP request
    """
    
    def parse(self, data):
        """
        Parse the data into the HTTP request

        @param data: the field 'data' of the request
        @return: dictionary containing both the 'snapped' and the 'raw' data
        """
        dict_routes = {}
        dict_routes['snapped'] = self._parseGeoJSON(data, 'snappedPoints')
        dict_routes['raw'] = self._parseGeoJSON(data, 'rawData')

        return dict_routes

    def _parseGeoJSON(self, data, kind):
        """
        Parse a single type of data ('snapped' or 'raw')

        @param data: the field 'data' of the request
        @param kind: the type of data that need to be extracted ('snapped' or 'raw')
        @return: a list of Point
        """
        trip_coordinates = []

        for p in data[kind]:
            longitude = p["location"]["longitude"]
            latitude = p["location"]["latitude"]
            point = self._create_point(longitude, latitude)
            trip_coordinates.append(point)

        return trip_coordinates

    def _create_point(self, longitude, latitude):
        """
        Create a Point starting from its coordinates

        @param longitude: the Point longitude
        @param latitude: the Point latitude
        @return: the Point
        """
        return Point(longitude, latitude)