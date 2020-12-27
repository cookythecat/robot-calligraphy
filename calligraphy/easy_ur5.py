"""
the class EasyUr5 is API for remote controlling UR5
robot_writing_logics holds an EasyUr5 object, and calls member method of this class for remote controlling UR5
"""
import math
import socket
import struct
import time
import numpy

HOST = "172.19.97.157"
PORT_30002 = 30002
PORT_30003 = 30003
ROBOT_SPEED = 0.28
ROBOT_ACCELERATION = 0.2
BROKEN_FINAL_RATE = 0.1
NORMAL_FINAL_RATE = 0.1


class EasyUr5:
    """
    UR5 API class
    """
    def __init__(self):
        """
        create connection between local machine and UR5
        """
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.connect((HOST, PORT_30002))

    def get_pose(self):
        """
        get the position of the tool of UR5
        :return: the position of the tool of UR5
        """
        socket1 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        socket1.connect((HOST, PORT_30003))
        socket1.settimeout(1)
        try:
            socket_res = socket1.recv(1108)
        except Exception as e:
            socket1 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            socket1.connect((HOST, PORT_30003))
            socket1.settimeout(1)
            print(e)

        pose = self.parse_cartesian_info(socket_res, 4 + 8 + 48 * 9 + 0 * 8)
        socket1.close()
        return pose

    @staticmethod
    def parse_cartesian_info(data_bytes, byte_idx):
        """
        parse the cartesian response from UR5
        :param data_bytes: bytes response information from UR5
        :param byte_idx: the index of current cursor
        :return: the actual position of the tool
        """
        actual_tool_pose = [0, 0, 0, 0, 0, 0]
        for pose_value_idx in range(6):
            actual_tool_pose[pose_value_idx] = struct.unpack('!d', data_bytes[(byte_idx + 0):(byte_idx + 8)])[0]
            byte_idx += 8
        return actual_tool_pose

    def test_move_to(self, position, r=0.001):
        """
        let the tool move to @position
        :param position: target position, [x, y, z, axis_1, axis_2, axis_3]
        :param r: blend radius
        :return: ok if finished this function without exception
        """
        # create command
        command = "movel(p["
        for i in range(5):
            command = command + str(position[i]) + ", "
        command = command + str(position[5])
        command = command + "], a=" + str(ROBOT_ACCELERATION) + ", v=" + str(ROBOT_SPEED) + ", r= " + str(r) + ")\n"
        # send command
        print(command)
        self.socket.sendall(command.encode('utf-8'))
        while True:
            time.sleep(0.002)
            current_pose = self.get_pose()
            error = 0
            for i in range(3):
                error += abs(current_pose[i] - position[i])
            arg1, arg2 = 0, 0
            for i in range(3, 6):
                if abs(current_pose[i] - position[i]) > 2 * math.pi:
                    arg1 += (-abs(current_pose[i] - position[i]) + math.pi * 2)
                else:
                    arg1 += abs(current_pose[i] - position[i])
            for i in range(3, 6):
                if abs(current_pose[i] + position[i]) > 2 * math.pi:
                    arg2 += (-abs(current_pose[i] + position[i]) + math.pi * 2)
                else:
                    arg2 += abs(current_pose[i] + position[i])

            if error < 1e-2 and min(arg1, arg2) < 0.1 + r * 3 * math.pi:
                print('break')
                break
        print('finished')
        return 'ok'

    def test_move_to_n(self, pos_l, slow_down, first, r=0.002):
        """
        move follow a trajectory of a sub-stroke
        :param pos_l: position array
        :param slow_down: boolean, if the stroke should slow down at the end of the sub-stroke
        :param first: boolean, if the sub-stroke is the first of the stroke
        :param r: blend radius
        :return: None
        """
        move_cmd_ = "def tes():\n"
        if not slow_down:
            midway = (numpy.array(pos_l[-2]) + numpy.array(pos_l[-1])) * 0.5
            midway[2] = midway[2] - 0.0125
            pos_l = numpy.insert(pos_l, -1, midway, axis=0)
        argc = len(pos_l)
        for i, pos in enumerate(pos_l):
            if first and i < 2:
                self.test_move_to(pos, 0.0)
                continue
            statement = "["
            for item in range(5):
                statement += str(pos[item]) + ", "
            statement += str(pos[5]) + "]"
            move_cmd_ += "  global Waypoint_%d_p=p%s\n" % (i + 1, statement)

        move_cmd_ += "  $ 1 \"Robot Program\"\n  $ 2 \"MoveP\"\n"

        broken_decrease_unit = ((1 - BROKEN_FINAL_RATE) * ROBOT_SPEED) / 35
        decrease_unit = ((1 - NORMAL_FINAL_RATE) * ROBOT_SPEED) / 12
        for i in range(argc - 1):
            speed = ROBOT_SPEED
            if not slow_down and argc - 2 == i:
                continue
            if slow_down and i >= argc - 1 - 35:
                speed = ROBOT_SPEED - broken_decrease_unit * (i - (argc - 1 - 35))
            if not slow_down and i >= argc - 1 - 12:
                speed = ROBOT_SPEED - decrease_unit * (i - (argc - 1 - 12))
            if first and i < 2:
                continue
            move_cmd_ += "  $ %d \"Waypoint_%d\"\n" % (i + 3, i + 1)
            move_cmd_ += "  movep(Waypoint_%d_p, a=%s, v=%.3f, r=%.3f)\n" % (i + 1, str(ROBOT_ACCELERATION), speed, r)

        if slow_down:
            move_cmd_ += "  $ %d \"Waypoint_%d\"\n" % (argc + 2, argc)
            move_cmd_ += "  movep(Waypoint_%d_p, a=%s, v=%.3f)\n" % (
                argc, str(ROBOT_ACCELERATION), BROKEN_FINAL_RATE * ROBOT_SPEED)
        else:
            move_cmd_ += "  $ %d \"Waypoint_%d\"\n" % (argc + 1, argc)
            move_cmd_ += "  movep(Waypoint_%d_p, a=%s, v=%.3f, r=%.3f)\n" % (
                argc - 1, str(ROBOT_ACCELERATION), NORMAL_FINAL_RATE * ROBOT_SPEED * 2, 0.001)
            move_cmd_ += "  $ %d \"Waypoint_%d\"\n" % (argc + 2, argc)
            move_cmd_ += "  movep(Waypoint_%d_p, a=%s, v=%.3f)\n" % (
                argc, str(ROBOT_ACCELERATION), NORMAL_FINAL_RATE * ROBOT_SPEED * 2)

        move_cmd_ += "end\n"
        print(move_cmd_)
        self.socket.sendall("rq_activate_and_wait()\n".encode('utf-8'))
        self.socket.sendall(move_cmd_.encode('utf-8'))
        self.socket.sendall("tes()\n".encode('utf-8'))

        endpos = pos_l[-1]
        while True:
            time.sleep(0.005)
            current_pose = self.get_pose()
            error = 0
            for i in range(3):
                error += abs(current_pose[i] - endpos[i])
            angerr1, angerr2 = 0, 0
            for i in range(3, 6):
                if abs(current_pose[i] - endpos[i]) > 2 * math.pi:
                    angerr1 += (-abs(current_pose[i] - endpos[i]) + math.pi * 2)
                else:
                    angerr1 += abs(current_pose[i] - endpos[i])
            for i in range(3, 6):
                if abs(current_pose[i] + endpos[i]) > 2 * math.pi:
                    angerr2 += (-abs(current_pose[i] + endpos[i]) + math.pi * 2)
                else:
                    angerr2 += abs(current_pose[i] + endpos[i])
            if error < 1e-3 and min(angerr1, angerr2) < 0.1:
                break
