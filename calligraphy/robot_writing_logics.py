#!/usr/bin/python
# -*- coding: utf-8 -*-
"""The logics of robot calligraphy

This module contains all the methods needed to convert a paths extracted from GIFs to trajectory information for UR5
The module would use data.json as the paths extracted from GIFs,
please use cv.cv to obtain data.json if you cannot find data.py
The module would store all the trajectories it ever calculated in previously_calculated_trajectory. And it would use
this information when writing the same string.
Please make sure previously_calculated_trajectory.json is existed in ..\data\
Please make sure data.json is existed in ..\data\
"""
import time
import copy
import os
import json
import math
import numpy
import easy_ur5

START_POSITION = [0.10018570816351019, -0.4535427417650308,
                  0.2590640572333883]
ORIENTATION = [0, math.pi, 0]
R = 0.0

STRAIGHT_HEIGHT = 0.01 * 1.3
STRAIGHT_DEVIATION = 0.01 * 0
STRAIGHT_WIDTH = 0.01 * 0

MIDDLE_HEIGHT = 0.01 * 0.83
MIDDLE_DEVIATION = 0.01 * 0.21
MIDDLE_WIDTH = 0.01 * 000.3

DEEPEST_HEIGHT = 0.01 * 0.37
DEEPEST_DEVIATION = 0.01 * 0.1
DEEPEST_WIDTH = 0.01 * 1.17

MY_PATH = os.path.abspath(os.path.dirname(__file__))
JSON_DIR = os.path.join(MY_PATH, r"..\data\previously_calculated_trajectory.json")
CHAR_LIB_DIR = os.path.join(MY_PATH, r"..\data\data.json")


def reduce_by_multiple(trajectory, integer):
    """
    keep only control points in given trajectory which are multiple of @integer
    :param trajectory: array that describes the trajectory
    :param integer: the multiple used for reducing
    :return: the reduced trajectory
    """
    reduced = trajectory[0:len(trajectory) - 1:integer]
    if len(reduced) == 0:
        return trajectory
    if reduced[-1] != trajectory[len(trajectory) - 1]:
        reduced.append(trajectory[len(trajectory) - 1])
    return reduced


def naive_width2z(width):
    # assert width <= 0.01
    """
    a naive way to map width to z axis position
    :param width: width of a corresponding control point
    :return: the z axis position
    """
    assert width >= 0
    return 0.01 - width


def get_mover(
        map_3d,
        stroke_info,
        start_position,
        orientation,
        scale_factor,
):
    """
    get calculated trajectory of a stroke
    :param map_3d: functions for mapping width to z-axis, a polymorphism design
    :param stroke_info: array that describes a stroke
    :param start_position: starting position for a character
    :param orientation: orientation of tool
    :param scale_factor: a constant scalar, used for adjust the size of character you wanted to write
    :return: the calculated trajectory of the given stroke
    """
    three_d_trajectory = []

    map_3d(stroke_info, three_d_trajectory, scale_factor,
           start_position)

    start_lift = copy.deepcopy(three_d_trajectory[0])
    start_lift[2] = start_lift[2] + 0.02

    # add tilt value

    if len(three_d_trajectory) > 1:
        vector_a = numpy.array(three_d_trajectory[0])
        vector_b = numpy.array(three_d_trajectory[1])
        vector_ba = vector_a - vector_b
        dev_start = vector_ba / numpy.linalg.norm(vector_ba) * 0.009
        start_lift[0] += dev_start[0]
        start_lift[1] += dev_start[1]

    three_d_trajectory.insert(0, start_lift)

    mover = []
    for i in three_d_trajectory:
        real_pos = i
        real_ori = orientation
        mover.append(real_pos + real_ori)

    time.sleep(1)
    return mover


def broke_stroke(trajectory):
    """
    break one stroke into one or multiple sub-stroke for preventing error caused by UR5 cannot maintain a speed
    :param trajectory: the trajectory of a stroke
    :return: a array of broken sub-stroke
    """
    stroke_group = []
    pointer1 = 0
    if len(trajectory) < 11:
        print(len(trajectory))
        stroke_group.append(trajectory)
        return stroke_group

    for i in range(5, len(trajectory) - 5):
        y0 = trajectory[i - 1][1]
        y1 = trajectory[i][1]
        y2 = trajectory[i + 1][1]
        y_dif0 = y1 - y0
        y_dif1 = y2 - y1

        x0 = trajectory[i - 1][0]
        x1 = trajectory[i][0]
        x2 = trajectory[i + 1][0]
        x_dif0 = x1 - x0
        x_dif1 = x2 - x1

        max_tolerance = 0.006
        if (x_dif0 * x_dif1 < 0 and (abs(x_dif0) > max_tolerance or abs(x_dif1)
                                     > max_tolerance)) or (y_dif0 * y_dif1 < 0 \
                                                   and (abs(y_dif0) > max_tolerance or abs(y_dif1) > max_tolerance)):
            stroke_group.append([trajectory[pointer1:i + 1], True])
            pointer1 = i + 1
    if pointer1 == len(trajectory) - 1:
        stroke_group[0].append([trajectory[len(trajectory) - 1], False])
    else:
        stroke_group.append([trajectory[pointer1:len(trajectory)],
                             False])

    # mark first:

    stroke_group[0].append(True)
    for i in range(1, len(stroke_group)):
        stroke_group[i].append(False)

    return stroke_group


def double_linear3_mapping(
        stroke_info,
        three_d_trajectory,
        scale_factor,
        start_position,
):
    """
    a way of mapping considering the offset of the brush increases then decreases when z axis position is decreasing
    :param stroke_info: array that describes the stroke information
    :param three_d_trajectory: array that describes the 3D trajectory
    :param scale_factor: a constant scalar, used for adjust the size of character you wanted to write
    :param start_position: start position of the stroke
    :return: a array that describes processed position of the tool
    """
    prev_point2d = stroke_info[0][0]
    for point in stroke_info:
        point3d = copy.deepcopy(point[0])
        direction = numpy.array(point3d) - numpy.array(prev_point2d)
        if prev_point2d == point3d:
            standard_direction = 0
        else:
            standard_direction = numpy.array(direction) / numpy.linalg.norm(direction)
        point3d = [x * scale_factor for x in point3d]
        w = point[1] * scale_factor
        if w > DEEPEST_WIDTH:
            w = DEEPEST_WIDTH

        if w <= MIDDLE_WIDTH:
            deviation_needed = linear_function(STRAIGHT_WIDTH,
                                               MIDDLE_WIDTH, STRAIGHT_DEVIATION, MIDDLE_DEVIATION,
                                               w)
            point3d = numpy.array(point3d) + numpy.array(standard_direction * deviation_needed)
            depth = linear_function(STRAIGHT_WIDTH, MIDDLE_WIDTH,
                                    STRAIGHT_HEIGHT, MIDDLE_HEIGHT, w)
        else:
            deviation_needed = linear_function(MIDDLE_WIDTH,
                                               DEEPEST_WIDTH, MIDDLE_DEVIATION, DEEPEST_DEVIATION,
                                               w)
            point3d = numpy.array(point3d) + numpy.array(standard_direction * deviation_needed)
            depth = linear_function(MIDDLE_WIDTH, DEEPEST_WIDTH,
                                    MIDDLE_HEIGHT, DEEPEST_HEIGHT, w)
        point3d = point3d.tolist()
        point3d.append(depth)

        point3d = numpy.array(point3d) + numpy.array(start_position)
        point3d = point3d.tolist()
        three_d_trajectory.append(point3d)
        prev_point2d = point[0]


def linear_function(
        x1,
        x2,
        y1,
        y2,
        x,
):
    """
    linear function, given a line and a point on that line, It would output the y value corresponding to the x value
    :param x1: x value of point 1
    :param x2: x value of point 2
    :param y1: y value of point 1
    :param y2: y value of point 2
    :param x: x value corresponding to wanted y value
    :return: y value corresponding to the given x value
    """
    k = (y2 - y1) / (x2 - x1)
    y = k * (x - x1) + y1
    return y


def rotate(character, angle):
    """
    given a character and an angle that you want want for rotating, return an rotated character
    :param character: character that you want to rotate
    :param angle: angle you want for rotating
    :return: the rotated character
    """
    for i in character:
        for j in i:
            j[0] = rotate_points([150, 150], j[0], angle)


def rotate_points(origin, point, angle):
    """
    otate a point counterclockwise by a given angle around a given origin.
    The angle should be given in radians.
    :param origin:
    :param point:
    :param angle:
    :return: the rotated list of point
    """

    (ox, oy) = origin
    (px, py) = point

    qx = ox + math.cos(angle) * (px - ox) - math.sin(angle) * (py - oy)
    qy = oy + math.sin(angle) * (px - ox) + math.cos(angle) * (py - oy)
    return qx, qy


def load_character_lib(file):
    """
    load a file object
    :param file: the file to be loaded
    :return: the loaded file dictionary
    """
    user_dic = json.load(file)
    return user_dic


def get_char_mover(
        char,
        start_position,
        orientation,
        scale_factor,
        mapping,
):
    """
    get the writing trajectory of a character
    :param char: character you want to write
    :param start_position: start position of the character
    :param orientation: orientation of the character
    :param scale_factor: a constant scalar, used for adjust the size of character you wanted to write
    :param mapping: the way of mapping width to z-axis coordinate
    :return: the writing trajectory of a character
    """
    previous_location = copy.deepcopy(start_position)
    previous_location[2] += 0.15

    char_mover = []
    counter = 1
    for i in char:
        print('--------------------')
        stroke = get_mover(
            mapping,
            i,
            start_position,
            orientation,
            scale_factor,
        )
        print('stroke #: ', counter)
        sub_stroke_group = broke_stroke(stroke)
        print('a stroke broken into: ', len(sub_stroke_group))
        for j in sub_stroke_group:
            print('before reduce: ', len(j[0]))
            j[0] = reduce_by_multiple(j[0], 4)
            print('after reduced: ', len(j[0]))
            char_mover.append(j)

        end_lift = copy.deepcopy(char_mover[-1][0][-1])
        end_lift[2] = end_lift[2] + 0.045
        c = numpy.array((char_mover[-1][0][-2])[0:2])
        d = numpy.array((char_mover[-1][0][-1])[0:2])
        cd = d - c
        dev_end = cd / numpy.linalg.norm(cd) * 0.03
        end_lift[0] += dev_end[0]
        end_lift[1] += dev_end[1]
        char_mover[-1][0].append(end_lift)

        counter += 1
    return char_mover


def write_considering_depth(
        string_to_write,
        scale,
        dictionary,
        angle,
        mapping,
        machine,
):
    """
    write a string
    :param string_to_write: string to be written
    :param scale: a constant scalar, used for adjust the size of character you wanted to write
    :param dictionary: the dictionary from unicode to writing path
    :param angle: rotating angle of the string you want to write
    :param mapping: the way of mapping width to z-axis
    :param machine: UR5 client
    :return: None
    """
    chars = []

    composed_key = string_to_write + ", " + str(scale) + "," + str(angle) + ", " + mapping.__name__
    check_result, previous_dictionary = try_previously_calculated_trajectory(composed_key)

    if check_result is not None:
        chars = check_result
    else:
        for character in string_to_write:
            character = character.encode('unicode_escape')
            character = str(character)
            character = character[5:-1]

            if character not in dictionary:
                print('characters cannot be found in data.json')
                START_POSITION[0] = START_POSITION[0] + scale * 1.1
                continue

            trajectory = dictionary[character]
            rotate(trajectory, angle)
            current = copy.deepcopy(trajectory)
            chars.append(get_char_mover(
                current,
                START_POSITION,
                ORIENTATION,
                scale,
                mapping
            ))
            START_POSITION[0] = START_POSITION[0] - scale * 300

        previous_dictionary[composed_key] = chars
        with open(JSON_DIR, 'w') as file:
            json.dump(previous_dictionary, file)

    assert machine is not None

    for i in chars:
        for j in i:
            stroke = j[0]
            slow_down = j[1]
            first = j[2]
            machine.test_move_to_n(stroke, slow_down, first)


def try_previously_calculated_trajectory(composed_key):
    """
    try if there is record of previous writing that share the same writing parameters
    (string_to_write , scale, angle, mapping) with current writing. If yes, the function would return previous record
    and the json dictionary. If no, the function would return None and the json dictionary.
    :param composed_key: the string that contains writing parameters(string_to_write , scale, angle, mapping)
    :return: If previous record that share the same parameter with current writing exists, the function would return
    previous record and the json dictionary. If no, the function would return None and the json dictionary.
    """
    previously_calculated_trajectory = \
        load_character_lib(open(JSON_DIR
                                , 'r'))
    if composed_key in previously_calculated_trajectory:
        print('trajectory record founded')
        return previously_calculated_trajectory[composed_key], previously_calculated_trajectory
    return None, previously_calculated_trajectory


if __name__ == '__main__':
    # ask for argument
    string_to_write = ''
    scale = 0.0004
    while True:
        try:
            string_to_write = input('input a string you want to write: ')
            scale = float(input('input scale (you can try 0.0004 first): '))
        except ValueError:
            print("please input valid value")
            continue
        else:
            break

    # read lib
    DIC = \
        load_character_lib(open(CHAR_LIB_DIR, 'r'))
    print(len(DIC))

    # connect to UR5
    MACHINE = None
    MACHINE = easy_ur5.EasyUr5()

    write_considering_depth(
        string_to_write,
        scale,
        DIC,
        math.pi,
        double_linear3_mapping,
        MACHINE,
    )
