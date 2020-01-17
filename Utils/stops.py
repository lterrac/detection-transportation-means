import json

import geopandas as gpd
import pathlib
from shapely.geometry import Point
import numpy as np


def _find_common_bus_lines(Ilist: list, Flist: list):
    """
    Find the common bus lines among an Initial list of points and a Final list of points.
    The Initial list should contain at least one Point.
    The Final list should contain at least one Point.

    @param Ilist: Initial list
    @param Flist: Final list
    @return: list with only the lines in common
    """
    # Checking the input format
    # Check the lengths of the input lists are greater than 0
    if len(Ilist) <= 0:
        raise Exception("Initial list should contain at least a point")
    elif len(Flist) <= 0:
        raise Exception("Final list should contain at least a point")
    else:
        starting_lines = [element[0] for element in Ilist]
        ending_lines = [element[0] for element in Flist]
        common_lines = [line for line in starting_lines if line in ending_lines]
        return common_lines


def _unique(lst: list):
    """
    Removes the duplicates from a list

    @param lst: the list with duplicates
    @return: the same list without duplicates
    """
    acc_list = []
    for e in lst:
        is_already_present = True
        for acc_item in acc_list:
            if acc_item[0] == e[0] and \
                    acc_item[1] == e[1] and \
                    acc_item[2] == e[2]:
                is_already_present = False
                break
        if is_already_present:
            acc_list.append((e[0], e[1], e[2]))
    return acc_list

def intercept(Ilist: list, Flist: list):
    """
    Find the interception between two set of stops.
    The Initial list should contain at least one Point.
    The Final list should contain at least one Point.

    @param Ilist: Initial list
    @param Flist: Final list
    @returns: an Initial and a Final Dataframe containing all the lines code in common
    """
    # Checking the input format
    # Check the lengths of the input lists are greater than 0
    if len(Ilist) <= 0:
        raise Exception("Initial list should contain at least a point")
    elif len(Flist) <= 0:
        raise Exception("Final list should contain at least a point")
    else:
        # Find the lines that are in both lists
        common_lines = _find_common_bus_lines(Ilist, Flist)
        # Find the common lines contained in the initial list
        filtered_IList = [element for element in Ilist if element[0] in common_lines]
        # Find the common lines contained in the final list
        filtered_FList = [element for element in Flist if element[0] in common_lines]
        # Delete the duplicates
        filtered_IList = _unique(filtered_IList)
        filtered_FList = _unique(filtered_FList)
        # Wrap them in a geopanda dataframe
        result_IDataframe = gpd.GeoDataFrame(filtered_IList, columns=['bus_id', 'longitude', 'latitude'])
        result_IDataframe['point'] = [Point(float(e[1]), float(e[2])) for e in filtered_IList]
        result_FDataframe = gpd.GeoDataFrame(filtered_FList, columns=['bus_id', 'longitude', 'latitude'])
        result_FDataframe['point'] = [Point(float(e[1]), float(e[2])) for e in filtered_FList]
        return result_IDataframe, result_FDataframe


class stops(object):
    """
    Class that manages the stop search 
    """

    def __init__(self, type_of_dataset="BUS"):
        # Finding the path of the bus stops geoson
        current_dir = pathlib.Path(__file__).parent.parent
        if type_of_dataset is "BUS":
            routes_file = current_dir.joinpath("data/bus_data.geojson")
        elif type_of_dataset is "TRAIN":
            routes_file = current_dir.joinpath("data/train_data.geojson")
        else:
            raise Exception("type of dataset should be BUS or TRAIN, other datasets are not implemented yet.")
        f = open(routes_file)
        data = json.load(f)
        nodes = [feature for feature in data['features'] if 'node' in feature['id']]
        lines_and_stops = []
        # For each node creates a tuple and append it to buses and stops
        for node in nodes:
            longitude = float(node['geometry']['coordinates'][0])
            latitude = float(node['geometry']['coordinates'][1])
            for line in node['properties']['@relations']:
                if 'ref' in line['reltags']:
                    lines_and_stops.append((line['reltags']['ref'], longitude, latitude))
        lines_and_stops = np.array(lines_and_stops)
        # Creating the geopanda dataframe
        dataset = gpd.GeoDataFrame()
        dataset['linea'] = lines_and_stops[:, 0]
        dataset['longitude'] = lines_and_stops[:, 1]
        dataset['latitude'] = lines_and_stops[:, 2]
        self.dataset = dataset

    
    def _search_indexes(self, from_x=0, to_x=0, from_y=0, to_y=0):
        """
        Search the stops from between a square [x0, x1, y0, y1]
        It raises exception if the input are not well formatted

        @param from_x: x starting coordinates
        @param to_x: x ending coordinates
        @param from_y: y starting coordinates
        @param to_y: y ending coordinates
        @return: list of stops inside the square defined by the four parameters
        """
        if from_x > to_x:
            raise Exception("From_x should be less than the to_x")
        elif from_y > to_y:
            raise Exception("From_y should be less than the to_y")
        else:
            # # Computing the result
            # # Start by computing a partial result
            # partial_result = [record for record in self.dataset.values if
            #                   from_x < record[1] < to_x and from_y < record[2] < to_y]
            # result = []
            # for record in partial_result:
            #     bus_lines = record[4].split(',')
            #     for bus_id in bus_lines:
            #         new_record = record.copy()
            #         new_record[4] = bus_id
            #         result.append(new_record)
            # Computing the result
            # Start by computing a partial result
            result = [record for record in self.dataset.values if
                      from_x < float(record[1]) < to_x and from_y < float(record[2]) < to_y]
            return result

    def find_stops_close_to(self, p: Point, radius=0.0003080999999998113, minimum_amount_of_stops=5):
        """
        Find the bus stops close to this point with exponential backoff policy
        The exponential backoff is used in order to find a minimum amount of stops

        @param p: the Point at the center of the circle used to search the stops
        @param radius: the circle radius
        @param minimum_amount_of_stops: minimum number of stops to find

        @return: list of nearest stops inside the circle
        """
        
        # Initialize the result to an empty list
        result = []
        i = 0
        while len(result) < 3 and i < 5:
            # Compute the coordinates of the rectangle used to find the stops
            from_x = p.x - radius
            from_y = p.y - radius
            to_x = p.x + radius
            to_y = p.y + radius
            result = self._search_indexes(from_x, to_x, from_y, to_y)
            # Exponential backoff policy
            radius = radius * 1.5
            i += 1
        return result


if __name__ == '__main__':
    s = stops()
