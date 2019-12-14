import numpy as np
import geopandas as gpd
from shapely.geometry import LineString, Point
import os
import pathlib

# INPUT
# List of NP.ARRAYs with data

class LinestringSelector(object):

    def __init__(self, Istops, Fstops):
        current_dir = pathlib.Path(__file__).parent.parent
        routes_file = current_dir.joinpath("data/bus_routes.geojson")
        self.data = gpd.read_file(routes_file)
        self.SlicedLineStringList = []
        self.Istops = Istops
        self.Fstops = Fstops

    def _preprocess_data(self):
        """
        Creates tuples of type (bus_id, starting_point, ending_point)
        """

        start_final_points_array = []

        for _ , initial_stop in self.Istops.iterrows():
            initial_point = initial_stop['point']
            bus_id = initial_stop['bus_id']

            relevant_final_points = np.array(self.Fstops['bus_id'] == str(bus_id))
            final_stops = self.Fstops[relevant_final_points]

            for _ , final_stop in final_stops.iterrows():
                final_point = final_stop['point']
                points_tuple = (bus_id, initial_point, final_point)
                start_final_points_array.append(points_tuple)

        return start_final_points_array

    def to_list_of_points(self, linestrings_array):
        bus_lines = []
        route_points = []

        for bus_line in linestrings_array:
            for linestring in bus_line:
                p1 = Point(linestring.coords[0])
                assert type(p1) == Point
                p2 = Point(linestring.coords[1])
                route_points.append(p1)
                route_points.append(p2)
            route_points = self._remove_duplicates(route_points)
            bus_lines.append(route_points)
        
        return bus_lines

    def get_sliced_routes(self):
        """
        Returns an array of type [ (bus_id, sliced_linestring), ... ]
        """

        sliced_linestrings_array = []

        # Get all tuples to analyse
        tuples_array = self._preprocess_data()

        print("tuples array " + str(len(tuples_array)))
        for tuple_s in tuples_array:
            print(tuple_s)
        print("------------------------------------------------------------------------")

        # For each tuple:
        for bus_start_stop_tuple in tuples_array:
            # Pick all the dataframe rows of that bus line
            possible_linestrings = self.data['linea'] == int(bus_start_stop_tuple[0])
            selected_linestrings = self.data[possible_linestrings]

            # Foreach linestring:
            for linestring in selected_linestrings['geometry']:
                # Get the sliced LineString & append to array
                sliced_linestring = self._get_sliced_multi_linestring(linestring,
                                                                      bus_start_stop_tuple[1],
                                                                      bus_start_stop_tuple[2])
                if sliced_linestring is not None:
                    sliced_linestrings_array.append(sliced_linestring)

        route_points = self.to_list_of_points(sliced_linestrings_array)
        return route_points

    def _convert_to_multilinestring(self, linestring):
        """
        Creates a collection of LineStrings that compose the original LineString
        """

        linestring_array = []

        # For num_of_points
        for i in range(len(linestring.coords) - 1):
            # Pick two consectuive points
            first_point = Point(linestring.coords[i])
            second_point = Point(linestring.coords[i + 1])
            # Create new LineString with those points
            linestring_new = LineString([first_point, second_point])
            linestring_array.append(linestring_new)

        return np.asarray(linestring_array, dtype=LineString)


    def _get_sliced_multi_linestring(self, linestring, starting_point, finishing_point):
        """
        Created and returns the sliced LineString
        """

        # Convert original LineString to MultiLineString
        multi_linestring = self._convert_to_multilinestring(linestring)
        # Get index of the nearest LineString to the starting stop
        starting_index = self._get_index_of_min_distance(multi_linestring, starting_point)
        # Get index of the nearest LineString to the final stop
        finishing_index = self._get_index_of_min_distance(multi_linestring, finishing_point)

        # TODO check index order to apply logic (if starting comes latter than finishing then do logic)
        # If the start_index is before the finishing_index (original LineString is ordered)
        if starting_index <= finishing_index:
            # Get only the relevant LineStrings
            sliced_multi_linestring = multi_linestring[starting_index:finishing_index]
            return sliced_multi_linestring

        elif finishing_index < starting_index:
            # TODO check a scenario to see what could be done
            #raise Exception("Not yet implemented")
            return None
        else:
            # TODO can they be equal? Should not be
            #raise Exception("This case shouldn't be possible")
            return None

    def _convert_to_linestring(self, multi_linestring):
        """
        Creates LineString from multiple LineStrings
        """

        return LineString(multi_linestring)

    def _get_index_of_min_distance(self, multi_linestring, point):
        """
        Returns the index of the nearest LineString to a given point

        This method is used to get the index of the nearest LineString to a bus
        stop, which, depending if it's a final bus stop or the initial one, will be
        used to slice the multi_linestring arraty in order to get only the relevant
        portion of the original LineString
        """

        distances = []

        for linestring in multi_linestring:
            dist = linestring.distance(point)
            distances.append(dist)

        return distances.index(min(distances))
   
    def _remove_duplicates(self, points: list):
        unique_list = []

        for point in points:
            if point not in unique_list:
                unique_list.append(point)

        return unique_list

