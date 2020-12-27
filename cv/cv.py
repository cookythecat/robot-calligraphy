#!/usr/bin/python
# -*- coding: utf-8 -*-
import math
import os
import json
import numpy as np
import PIL
import cv2
import data.common_characters

MY_PATH = os.path.abspath(os.path.dirname(__file__))
JSON_DIR = os.path.join(MY_PATH, r"..\data\data.json")


def all_black(image):
    """
    the method would check if a matrix of a image is consisted of all black points
    :param image: matrix of a image
    :return: if the matrix of a image is consisted of all black points
    """
    return (np.array(image) == 0).all()


def obtain_container(gif_name):
    """
    obtain a container of frames of a GIF
    :param gif_name: name of the GIF
    :return: the container of the frames of the GIF
    """
    container = []
    image = PIL.Image.open(gif_name)
    iterator = PIL.ImageSequence.Iterator(image)
    for frame in iterator:
        img = frame.convert('RGB')
        img = cv2.cvtColor(np.asarray(img), cv2.COLOR_RGB2BGR)
        container.append(img)
    return container


# define graph algo

def find_first(graph):
    """
    the method would find the most top-left point of a matrix of a stroke
    :param graph: matrix of a stroke
    :return: the coordinate of the point
    """
    shape = get_shape(graph)
    shortest = shape[0] + shape[1] + 1
    shortest_index = [-1, -1]
    for i in range(shape[0]):
        for j in range(shape[1]):
            if graph[i][j] > 0 and shortest > i + j:
                shortest = i + j
                shortest_index = [i, j]
    return shortest_index


def dfs(
        matrix,
        current,
        trajectory,
        shape,
        visited,
        gray,
        complete,
):
    """
    DFS algorithm for finding trajectory of a stoke
    :param matrix: the matrix of a stroke
    :param current: the current visiting point in the matrix of a stroke
    :param trajectory: a set storing wanted trajectory (array of points)
    :param shape: shape of the matrix of a stroke
    :param visited: boolean matrix of visited points
    :param gray: gray graph of the matrix
    :param complete: a set of coordinates of points and their corresponding width
    :return: None
    """
    width = find_width(current, gray)
    if not (len(trajectory) > 0 and abs(trajectory[-1][0] - current[0])
            + abs(trajectory[-1][1] - current[1]) > 50):
        trajectory.append(current)
        complete.append([current, width])
    visited[current[0]][current[1]] = 1
    neighbors = [
        [current[0] - 1, current[1] - 1],
        [current[0] - 1, current[1]],
        [current[0] - 1, current[1] + 1],
        [current[0], current[1] - 1],
        [current[0], current[1] + 1],
        [current[0] + 1, current[1] - 1],
        [current[0] + 1, current[1]],
        [current[0] + 1, current[1] + 1],
    ]
    for i in neighbors:
        if not (i[0] >= shape[0] or i[0] < 0 or i[1] >= shape[1]
                or i[1] < 0) and matrix[i[0]][i[1]] > 0 \
                and visited[i[0]][i[1]] == 0:
            dfs(
                matrix,
                i,
                trajectory,
                shape,
                visited,
                gray,
                complete,
            )


def find_path(matrix, gray):
    """
    the helper of dfs path finding algorithm
    :param matrix: the matrix of image of a stroke
    :param gray: the gray graph of the image of a stroke
    :return: the path founded by this method
    """
    # find shape

    shape = np.shape(np.array(matrix))

    # prepare visited

    visited = np.zeros(shape)

    # find first

    first = find_first(matrix)
    trajectory = []
    complete = []
    dfs(
        matrix,
        first,
        trajectory,
        shape,
        visited,
        gray,
        complete,
    )
    return trajectory, complete


def get_shape(matrix):
    """
    get the shape of a matrix array
    :param matrix: 2D array matrix
    :return: the shape of the matrix
    """
    return np.shape(np.array(matrix))


def union(matrix_set):
    """
    get the union of all stroke of one character
    :param matrix_set: set of path matrices of strokes of a characters
    :return: the union matrix of paths of strokes of a character
    """
    shape = get_shape(matrix_set[0])
    union = np.zeros(shape, np.uint8)
    for i in range(shape[0]):
        for j in range(shape[1]):
            for matrix in matrix_set:
                if matrix[i][j] != 0:
                    union[i][j] = 255
    return union


def find_width(index, matrix):
    """
    find the width of a stroke at a given point
    :param index: coordinate of the point
    :param matrix: matrix of a image of a stroke
    :return: the width of a stroke at that point
    """
    # find shape

    shape = get_shape(matrix)
    first_p = [-1, -1]
    first_found = False
    first_r = -1
    for i in range(max(shape)):
        circle = get_circle(index, i)
        for point in circle:
            if point[0] >= shape[0] or point[0] < 0 or point[1] >= shape[1] or point[1] \
                    < 0:
                continue
            if matrix[point[0]][point[1]] == 0:
                if not first_found:
                    first_found = True
                    first_p = point
                    first_r = i
                else:
                    diff_f = np.array(index) - np.array(first_p)
                    diff_s = np.array(index) - np.array(point)
                    x_is_diff = diff_f[1] * diff_s[1] <= 0
                    y_is_diff = diff_f[0] * diff_s[0] <= 0
                    if x_is_diff and y_is_diff:
                        return first_r + i


def get_circle(index, radius):
    """
    get a set of points at a circle
    :param index: center of the circle
    :param radius: radius of the circle
    :return: the set of points at the circle
    """
    circle = []
    for i in range(index[1] - radius, index[1] + radius + 1):
        distance = abs(index[1] - i)
        height = int(math.sqrt(radius ** 2 - distance ** 2))
        if [i, index[0] - height] not in circle:
            circle.append([index[0] - height, i])
        if [i, index[0] + height] not in circle:
            circle.append([index[0] + height, i])
    return circle


def parse_gif(url):
    """
    parse a gif, get the writing paths of a character, the return of the method would be stored in a .json file if
    extract_and_save is called. the .json file can be used as reference for robot calligraphy

    :param url: the url of the GIF of the character
    :return: 2D array of data structures which contain the coordinates of points on the writing path and
    their corresponding width
    """
    gray_set = []
    all_black_set = []
    container = obtain_container(url)
    for i in container:
        # get image

        image = i
        cv2.rectangle(image, (180, 270), (300, 300), (100, 186, 245),
                      -1)
        image = cv2.GaussianBlur(image, (5, 5), 0)
        image = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
        lower = np.array([165, 60, 60])
        upper = np.array([190, 255, 255])
        mask = cv2.inRange(image, lower, upper)
        black = all_black(mask)
        all_black_set.append(black)

    matrix_set, complete_set = \
        processing_logic(container, all_black_set, gray_set)

    union_map = union(matrix_set)
    cv2.imshow('union', union_map)
    cv2.waitKey()
    return complete_set


def processing_logic(container, all_black_set, gray_set):
    """
    the logics of parse_gif
    :param container: container of frames of a GIF about a character
    :param all_black_set: the set of the boolean values about if frames are all constituted of black RGB = (0, 0, 0) points
    :param gray_set: an array of gray graph of frames
    :return: matrix_set, an array of matrices of skeletonized strokes
        complete_set, an nested array of data structures which contain the coordinates of points on the path of strokes
        and their corresponding width
    """
    char = []
    matrix_set = []
    complete_set = []
    counter = -1
    for i in container:

        # get image

        counter += 1
        if not (counter != len(all_black_set) - 1
                and not all_black_set[counter]
                and all_black_set[counter + 1]):
            continue
        image = i
        cv2.rectangle(image, (180, 270), (300, 300), (100, 186, 245),
                      -1)
        image = cv2.GaussianBlur(image, (5, 5), 0)
        result = image.copy()
        image = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
        lower = np.array([165, 60, 60])
        upper = np.array([190, 255, 255])
        mask = cv2.inRange(image, lower, upper)

        result = cv2.bitwise_and(result, result, mask=mask)
        inverted = result
        gray = cv2.cvtColor(inverted, cv2.COLOR_BGR2GRAY)
        gray_set.append(gray)

        thinned = cv2.ximgproc.thinning(gray,
                                        thinningType=cv2.ximgproc.THINNING_ZHANGSUEN)
        matrix_set.append(thinned)

        (trajectory, complete) = find_path(thinned, gray)

        # find direction

        first = trajectory[0]
        last = trajectory[len(trajectory) - 1]
        p_f = image[first[0]][first[1]]
        p_l = image[last[0]][last[1]]
        f_red = 255 > p_f[2] > 165 and p_f[1] > 60 and p_f[0] > 60 \
                and p_f[1] < 200 and p_f[0] < 200
        l_red = 255 > p_l[2] > 165 and p_l[1] > 60 and p_l[0] > 60 \
                and p_l[1] < 200 and p_l[0] < 200
        f_white = p_f[2] > 240 and p_f[1] > 240 and p_f[0] > 240
        l_white = p_l[2] > 240 and p_l[1] > 240 and p_l[0] > 240
        counter2 = counter
        while f_red and l_red and not (f_white and l_white):
            counter2 -= 1
            img_prev = container[counter2]
            p_f = img_prev[first[0]][first[1]]
            p_l = img_prev[last[0]][last[1]]
            f_red = 255 > p_f[2] > 165 and p_f[1] > 60 and p_f[0] > 60 \
                    and p_f[1] < 200 and p_f[0] < 200
            l_red = 255 > p_l[2] > 165 and p_l[1] > 60 and p_l[0] > 60 \
                    and p_l[1] < 200 and p_l[0] < 200
            f_white = p_f[2] > 240 and p_f[1] > 240 and p_f[0] > 240
            l_white = p_l[2] > 240 and p_l[1] > 240 and p_l[0] > 240
        if not (f_white and l_white) and l_red:
            trajectory.reverse()
            complete.reverse()
            print('reversed')
        char.append(trajectory)
        complete_set.append(complete)

    return matrix_set, complete_set


def write_json(url, new_pairs):
    """
    save json into a .json file, it would be placed in ..\data\
    if extract_and_save is called.

    :param url: the url of the .json file
    :param new_pairs: array of pairs of unicode and writing path pairs (unicode, paths).
    :return: none
    """
    with open(url, 'w') as file:
        json.dump(new_pairs, file)


def load_character_lib(file):
    """
    load .json file object
    :param file: a file object about .json file
    :return: a dictionary, key: unicode value: writing path
    """
    user_dic = json.load(file)
    return user_dic


def extract_and_save():
    """
    call this method to get a .json file of the writing paths of 3000+ commonly used chinese characters
    :return: none
    """
    counter = 0
    commons = \
        list(dict.fromkeys(data.common_characters.COMMON_CHARACTERS))
    commons = list(set(commons))
    commons = sorted(commons)
    buffer = {}
    for i in commons:
        unicode = hex(i)
        hex_value = unicode[2:]
        name = '\\' + hex_value + '-bishun.gif'

        url = os.path.join(MY_PATH, r"..\data\chars" + name)
        complete_set = parse_gif(url)
        buffer[hex_value] = complete_set
        if counter % 20 == 0 or i == 0x9f9f:
            write_json(JSON_DIR, buffer)
            buffer = {}
            print('counter: ', counter)
        counter += 1