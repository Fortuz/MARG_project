"""
This file was taken from the NatNet SDK and modified.
NatNet Version 2.10.0 (06/15/2016)
"""

import socket
import struct
from threading import Thread


def trace(*args):
    pass  # print("".join(map(str, args)))


# Create structs for reading various object types to speed up parsing.
Vector3 = struct.Struct('<fff')
Quaternion = struct.Struct('<ffff')
FloatValue = struct.Struct('<f')
DoubleValue = struct.Struct('<d')


class NatNetClient:
    def __init__(self, server_ip_address="192.168.0.105", local_ip_address="192.168.0.147",
                 multicast_address="239.255.42.99", command_port=1510, data_port=1511):

        # Change this value to the IP address of the NatNet server.
        self.server_ip_address = server_ip_address

        # Change this value to the IP address of your local network interface
        self.local_ip_address = local_ip_address

        # This should match the multicast address listed in Motive's streaming settings.
        self.multicast_address = multicast_address

        # NatNet Command channel
        self.command_port = command_port

        # NatNet Data channel
        self.data_port = data_port

        # Set this to a callback method of your choice to receive new frame.
        self.new_frame_listener = None

        # Set this to a callback method of your choice to receive per-rigid-body data at each frame.
        self.rigid_body_listener = None

        # NatNet stream version. This will be updated to the actual version the server is using during initialization.
        self.__nat_net_stream_version = (2, 10, 0, 0)

    # Client/server message ids
    NAT_PING = 0
    NAT_PINGRESPONSE = 1
    NAT_REQUEST = 2  # Unrecognized request
    NAT_RESPONSE = 3
    NAT_REQUEST_MODELDEF = 4
    NAT_MODELDEF = 5
    NAT_REQUEST_FRAMEOFDATA = 6  # Unrecognized request
    NAT_FRAMEOFDATA = 7
    NAT_MESSAGESTRING = 8
    NAT_DISCONNECT = 9
    NAT_UNRECOGNIZED_REQUEST = 100

    # Create a data socket to attach to the NatNet stream
    def __create_data_socket(self, port):
        result = socket.socket(socket.AF_INET,  # Internet
                               socket.SOCK_DGRAM,
                               socket.IPPROTO_UDP)  # UDP

        result.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        # buffer size to 1 for real-time display
        result.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, 1)

        result.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP,
                          socket.inet_aton(self.multicast_address) + socket.inet_aton(self.local_ip_address))

        result.bind(('', port))

        return result

    # Create a command socket to attach to the NatNet stream
    def __create_command_socket(self):
        result = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        result.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        result.bind(('', 0))
        result.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)

        return result

    # Unpack a rigid body object from a data packet
    def __unpack_rigid_body(self, data):
        offset = 0
        # ID (4 bytes)
        rigid_body_id = int.from_bytes(data[offset:offset + 4], byteorder='little')
        rigid_body_name = int.from_bytes(data[offset:offset + 4], byteorder='little')
        offset += 4
        trace("Rigid Body ID:", rigid_body_id)

        # Position and orientation
        pos = Vector3.unpack(data[offset:offset + 12])
        offset += 12
        trace("\tPosition:", pos[0], ",", pos[1], ",", pos[2])
        rot = Quaternion.unpack(data[offset:offset + 16])
        offset += 16
        trace("\tOrientation:", rot[0], ",", rot[1], ",", rot[2], ",", rot[3])

        # Send information to any listener.
        if self.rigid_body_listener is not None:
            self.rigid_body_listener(rigid_body_id, pos, rot)

        trace("\tPosition:", pos[0], ",", pos[1], ",", pos[2])
        # RB Marker Data ( Before version 3.0.  After Version 3.0 Marker data is in description )
        if self.__nat_net_stream_version[0] < 3 and self.__nat_net_stream_version[0] != 0:
            # Marker count (4 bytes)
            marker_count = int.from_bytes(data[offset:offset + 4], byteorder='little')
            offset += 4
            marker_count_range = range(0, marker_count)
            trace("\tMarker Count:", marker_count)

            # Marker positions
            for i in marker_count_range:
                pos = Vector3.unpack(data[offset:offset + 12])
                offset += 12
                trace("\tMarker", i, ":", pos[0], ",", pos[1], ",", pos[2])

            if self.__nat_net_stream_version[0] >= 2:
                # Marker ID's
                for i in marker_count_range:
                    marker_id = int.from_bytes(data[offset:offset + 4], byteorder='little')
                    offset += 4
                    trace("\tMarker ID", i, ":", marker_id)

                # Marker sizes
                for i in marker_count_range:
                    size = FloatValue.unpack(data[offset:offset + 4])
                    offset += 4
                    trace("\tMarker Size", i, ":", size[0])

        if self.__nat_net_stream_version[0] >= 2:
            marker_error, = FloatValue.unpack(data[offset:offset + 4])
            offset += 4
            trace("\tMarker Error:", marker_error)

        # Version 2.6 and later
        if (((self.__nat_net_stream_version[0] == 2) and (self.__nat_net_stream_version[1] >= 6)) or
                self.__nat_net_stream_version[0] > 2 or self.__nat_net_stream_version[0] == 0):
            param, = struct.unpack('h', data[offset:offset + 2])
            tracking_valid = (param & 0x01) != 0
            offset += 2
            trace("\tTracking Valid:", 'True' if tracking_valid else 'False')

        return offset

    # Unpack a skeleton object from a data packet
    def __unpack_skeleton(self, data):
        offset = 0

        skeleton_id = int.from_bytes(data[offset:offset + 4], byteorder='little')
        offset += 4
        trace("Skeleton ID:", skeleton_id)

        rigid_body_count = int.from_bytes(data[offset:offset + 4], byteorder='little')
        offset += 4
        trace("Rigid Body Count:", rigid_body_count)
        for j in range(0, rigid_body_count):
            offset += self.__unpack_rigid_body(data[offset:])

        return offset

    # Unpack data from a motion capture frame message
    def __unpack_mocap_data(self, data):
        trace("Begin MoCap Frame\n-----------------\n")

        data = memoryview(data)
        offset = 0

        # Frame number (4 bytes)
        frame_number = int.from_bytes(data[offset:offset + 4], byteorder='little')
        offset += 4
        trace("Frame:", frame_number)

        # Marker set count (4 bytes)
        marker_set_count = int.from_bytes(data[offset:offset + 4], byteorder='little')
        offset += 4
        trace("Marker Set Count:", marker_set_count)

        for i in range(0, marker_set_count):
            # Model name
            model_name, separator, remainder = bytes(data[offset:]).partition(b'\0')
            offset += len(model_name) + 1
            trace("Model Name:", model_name.decode('utf-8'))

            # Marker count (4 bytes)
            marker_count = int.from_bytes(data[offset:offset + 4], byteorder='little')
            offset += 4
            trace("Marker Count:", marker_count)

            for j in range(0, marker_count):
                pos = Vector3.unpack(data[offset:offset + 12])
                offset += 12
                # trace( "\tMarker", j, ":", pos[0],",", pos[1],",", pos[2] )

        # Unlabeled markers count (4 bytes)
        unlabeled_markers_count = int.from_bytes(data[offset:offset + 4], byteorder='little')
        offset += 4
        trace("Unlabeled Markers Count:", unlabeled_markers_count)

        for i in range(0, unlabeled_markers_count):
            pos = Vector3.unpack(data[offset:offset + 12])
            offset += 12
            trace("\tMarker", i, ":", pos[0], ",", pos[1], ",", pos[2])

        # Rigid body count (4 bytes)
        rigid_body_count = int.from_bytes(data[offset:offset + 4], byteorder='little')
        offset += 4
        trace("Rigid Body Count:", rigid_body_count)

        for i in range(0, rigid_body_count):
            offset += self.__unpack_rigid_body(data[offset:])

        # Version 2.1 and later
        skeleton_count = 0
        if not (self.__nat_net_stream_version[0] == 2 and self.__nat_net_stream_version[1] > 0) \
                or self.__nat_net_stream_version[0] > 2:
            skeleton_count = int.from_bytes(data[offset:offset + 4], byteorder='little')
            offset += 4
            trace("Skeleton Count:", skeleton_count)
            for i in range(0, skeleton_count):
                offset += self.__unpack_skeleton(data[offset:])

        # Labeled markers (Version 2.3 and later)
        labeled_marker_count = 0
        if (self.__nat_net_stream_version[0] == 2 and self.__nat_net_stream_version[1] > 3) \
                or self.__nat_net_stream_version[0] > 2:
            labeled_marker_count = int.from_bytes(data[offset:offset + 4], byteorder='little')
            offset += 4
            trace("Labeled Marker Count:", labeled_marker_count)
            for i in range(0, labeled_marker_count):
                labeled_marker_id = int.from_bytes(data[offset:offset + 4], byteorder='little')
                offset += 4
                pos = Vector3.unpack(data[offset:offset + 12])
                offset += 12
                size = FloatValue.unpack(data[offset:offset + 4])
                offset += 4

                # Version 2.6 and later
                if (self.__nat_net_stream_version[0] == 2 and self.__nat_net_stream_version[1] >= 6) \
                        or self.__nat_net_stream_version[0] > 2:
                    param, = struct.unpack('h', data[offset:offset + 2])
                    offset += 2
                    occluded = (param & 0x01) != 0
                    point_cloud_solved = (param & 0x02) != 0
                    model_solved = (param & 0x04) != 0

                # Version 3.0 and later
                if self.__nat_net_stream_version[0] >= 3:
                    residual, = FloatValue.unpack(data[offset:offset + 4])
                    offset += 4
                    trace("Residual:", residual)

        # TODO: false parsing BME MotionLab : if False
        # Force Plate data (version 2.9 and later)
        if False and (self.__nat_net_stream_version[0] == 2 and self.__nat_net_stream_version[1] >= 9) \
                or self.__nat_net_stream_version[0] > 2:
            force_plate_count = int.from_bytes(data[offset:offset + 4], byteorder='little')
            offset += 4
            trace("Force Plate Count:", force_plate_count)
            for i in range(0, force_plate_count):
                # ID
                force_plate_id = int.from_bytes(data[offset:offset + 4], byteorder='little')
                offset += 4
                trace("Force Plate", i, ":", force_plate_id)

                # Channel Count
                force_plate_channel_count = int.from_bytes(data[offset:offset + 4], byteorder='little')
                offset += 4

                # Channel Data
                for j in range(0, force_plate_channel_count):
                    trace("\tChannel", j, ":", force_plate_id)
                    force_plate_channel_frame_count = int.from_bytes(data[offset:offset + 4], byteorder='little')
                    offset += 4
                    for k in range(0, force_plate_channel_frame_count):
                        force_plate_channel_val = int.from_bytes(data[offset:offset + 4], byteorder='little')
                        offset += 4
                        trace("\t\t", force_plate_channel_val)

        # Device data (version 2.11 and later)
        if (self.__nat_net_stream_version[0] == 2 and self.__nat_net_stream_version[1] >= 11) \
                or self.__nat_net_stream_version[0] > 2:
            device_count = int.from_bytes(data[offset:offset + 4], byteorder='little')
            offset += 4
            trace("Device Count:", device_count)
            for i in range(0, device_count):
                # ID
                device_id = int.from_bytes(data[offset:offset + 4], byteorder='little')
                offset += 4
                trace("Device", i, ":", device_id)

                # Channel Count
                device_channel_count = int.from_bytes(data[offset:offset + 4], byteorder='little')
                offset += 4

                # Channel Data
                for j in range(0, device_channel_count):
                    trace("\tChannel", j, ":", device_id)
                    device_channel_frame_count = int.from_bytes(data[offset:offset + 4], byteorder='little')
                    offset += 4
                    for k in range(0, device_channel_frame_count):
                        device_channel_val = int.from_bytes(data[offset:offset + 4], byteorder='little')
                        offset += 4
                        trace("\t\t", device_channel_val)

        # time_code
        time_code = int.from_bytes(data[offset:offset + 4], byteorder='little')
        offset += 4
        time_code_sub = int.from_bytes(data[offset:offset + 4], byteorder='little')
        offset += 4

        # Timestamp (increased to double precision in 2.7 and later)
        if (self.__nat_net_stream_version[0] == 2 and self.__nat_net_stream_version[1] >= 7) \
                or self.__nat_net_stream_version[0] > 2:
            timestamp, = DoubleValue.unpack(data[offset:offset + 8])
            offset += 8
        else:
            timestamp, = FloatValue.unpack(data[offset:offset + 4])
            offset += 4

        # Hires Timestamp (Version 3.0 and later)
        if self.__nat_net_stream_version[0] >= 3:
            stamp_camera_exposure = int.from_bytes(data[offset:offset + 8], byteorder='little')
            offset += 8
            stamp_data_received = int.from_bytes(data[offset:offset + 8], byteorder='little')
            offset += 8
            stamp_transmit = int.from_bytes(data[offset:offset + 8], byteorder='little')
            offset += 8

        # Frame parameters
        param, = struct.unpack('h', data[offset:offset + 2])
        is_recording = (param & 0x01) != 0
        tracked_models_changed = (param & 0x02) != 0
        offset += 2

        # Send information to any listener.
        if self.new_frame_listener is not None:
            self.new_frame_listener(frame_number, marker_set_count, unlabeled_markers_count, rigid_body_count,
                                    skeleton_count, labeled_marker_count, time_code, time_code_sub, timestamp,
                                    is_recording, tracked_models_changed)

    # Unpack a marker set description packet
    def __unpack_marker_set_description(self, data):
        offset = 0

        name, separator, remainder = bytes(data[offset:]).partition(b'\0')
        offset += len(name) + 1
        trace("Markerset Name:", name.decode('utf-8'))

        marker_count = int.from_bytes(data[offset:offset + 4], byteorder='little')
        offset += 4

        for i in range(0, marker_count):
            name, separator, remainder = bytes(data[offset:]).partition(b'\0')
            offset += len(name) + 1
            trace("\tMarker Name:", name.decode('utf-8'))

        return offset

    # Unpack a rigid body description packet
    def __unpack_rigid_body_description(self, data):
        offset = 0

        # Version 2.0 or higher
        if self.__nat_net_stream_version[0] >= 2:
            name, separator, remainder = bytes(data[offset:]).partition(b'\0')
            offset += len(name) + 1
            trace("\tRigidBody Name:", name.decode('utf-8'))

        rigid_body_id = int.from_bytes(data[offset:offset + 4], byteorder='little')
        offset += 4

        parent_id = int.from_bytes(data[offset:offset + 4], byteorder='little')
        offset += 4

        timestamp = Vector3.unpack(data[offset:offset + 12])
        offset += 12

        # Version 3.0 and higher, rigid body marker information contained in description
        if self.__nat_net_stream_version[0] >= 3 or self.__nat_net_stream_version[0] == 0:
            marker_count = int.from_bytes(data[offset:offset + 4], byteorder='little')
            offset += 4
            trace("\tRigidBody Marker Count:", marker_count)

            marker_count_range = range(0, marker_count)
            for marker in marker_count_range:
                marker_offset = Vector3.unpack(data[offset:offset + 12])
                offset += 12
            for marker in marker_count_range:
                active_label = int.from_bytes(data[offset:offset + 4], byteorder='little')
                offset += 4

        return offset

    # Unpack a skeleton description packet
    def __unpack_skeleton_description(self, data):
        offset = 0

        name, separator, remainder = bytes(data[offset:]).partition(b'\0')
        offset += len(name) + 1
        trace("\tMarker Name:", name.decode('utf-8'))

        skeleton_id = int.from_bytes(data[offset:offset + 4], byteorder='little')
        offset += 4

        rigid_body_count = int.from_bytes(data[offset:offset + 4], byteorder='little')
        offset += 4

        for i in range(0, rigid_body_count):
            offset += self.__unpack_rigid_body_description(data[offset:])

        return offset

    # Unpack a data description packet
    def __unpack_data_descriptions(self, data):
        offset = 0
        dataset_count = int.from_bytes(data[offset:offset + 4], byteorder='little')
        offset += 4

        for i in range(0, dataset_count):
            data_type = int.from_bytes(data[offset:offset + 4], byteorder='little')
            offset += 4
            if data_type == 0:
                offset += self.__unpack_marker_set_description(data[offset:])
            elif data_type == 1:
                offset += self.__unpack_rigid_body_description(data[offset:])
            elif data_type == 2:
                offset += self.__unpack_skeleton_description(data[offset:])

    def __data_thread_function(self, socket):
        while True:
            # Block for input
            data, addr = socket.recvfrom(32768)  # 32k byte buffer size
            if len(data) > 0:
                self.__process_message(data)

    def __process_message(self, data):
        trace("Begin Packet\n------------\n")

        message_id = int.from_bytes(data[0:2], byteorder='little')
        trace("Message ID:", message_id)

        packet_size = int.from_bytes(data[2:4], byteorder='little')
        trace("Packet Size:", packet_size)

        offset = 4
        if message_id == self.NAT_FRAMEOFDATA:
            self.__unpack_mocap_data(data[offset:])
        elif message_id == self.NAT_MODELDEF:
            self.__unpack_data_descriptions(data[offset:])
        elif message_id == self.NAT_PINGRESPONSE:
            offset += 256  # Skip the sending app's Name field
            offset += 4  # Skip the sending app's Version info
            self.__nat_net_stream_version = struct.unpack('BBBB', data[offset:offset + 4])
            trace("NatNet Stream Version:", self.__nat_net_stream_version)
            offset += 4
        elif message_id == self.NAT_RESPONSE:
            if packet_size == 4:
                command_response = int.from_bytes(data[offset:offset + 4], byteorder='little')
                offset += 4
            else:
                message, separator, remainder = bytes(data[offset:]).partition(b'\0')
                offset += len(message) + 1
                trace("Command response:", message.decode('utf-8'))
        elif message_id == self.NAT_UNRECOGNIZED_REQUEST:
            trace("Received 'Unrecognized request' from server")
        elif message_id == self.NAT_MESSAGESTRING:
            message, separator, remainder = bytes(data[offset:]).partition(b'\0')
            offset += len(message) + 1
            trace("Received message from server:", message.decode('utf-8'))
        else:
            trace("ERROR: Unrecognized packet type")

        trace("End Packet\n----------\n")

    def send_command(self, command, command_str, command_socket, address=None):

        if address is None:
            address = (self.server_ip_address, self.command_port)

        # Compose the message in our known message format
        if command == self.NAT_REQUEST_MODELDEF or command == self.NAT_REQUEST_FRAMEOFDATA:
            packet_size = 0
            command_str = ""
        elif command == self.NAT_REQUEST:
            packet_size = len(command_str) + 1
        elif command == self.NAT_PING:
            command_str = "Ping"
            packet_size = len(command_str) + 1
        else:
            packet_size = len(command_str) + 1

        data = command.to_bytes(2, byteorder='little')
        data += packet_size.to_bytes(2, byteorder='little')

        data += command_str.encode('utf-8')
        data += b'\0'

        trace("Command:", data)
        command_socket.sendto(data, address)

    def run(self):
        #TODO: not working with BME MoCap
        # Create the command socket
        self.command_socket = self.__create_command_socket()
        if self.command_socket is None:
            print("Could not open command channel")
            exit

        # Create a separate thread for receiving command packets
        command_thread = Thread(target=self.__data_thread_function, args=(self.command_socket,))
        command_thread.start()

        # Request NatNet streaming version
        self.send_command(self.NAT_PING, "", self.command_socket)

        # Request model
        self.send_command(self.NAT_REQUEST_MODELDEF, "", self.command_socket)

        # Request frame of data
        self.send_command(self.NAT_REQUEST_FRAMEOFDATA, "", self.command_socket)

        # Create the data socket
        self.data_socket = self.__create_data_socket(self.data_port)
        if self.data_socket is None:
            print("Could not open data channel")
            exit

        # Create a separate thread for receiving data packets
        data_thread = Thread(target=self.__data_thread_function, args=(self.data_socket,))
        data_thread.start()


if __name__ == '__main__':
    # This is a callback function that gets connected to the NatNet client and called once per mocap frame.
    def receive_new_frame(frame_number, marker_set_count, unlabeled_markers_count, rigid_body_count,
                          skeleton_count, labeled_marker_count, time_code, time_code_sub, timestamp,
                          is_recording, tracked_models_changed):
        print("Received frame", frame_number)


    # This is a callback function that gets connected to the NatNet client. It is called once per rigid body per frame
    def receive_rigid_body_frame(id, position, rotation):
        print("Received frame for rigid body", id)


    # This will create a new NatNet client ()
    streamingClient = NatNetClient("192.168.1.153", "192.168.1.30")

    # Configure the streaming client to call our rigid body handler on the emulator to send data out.
    streamingClient.new_frame_listener = receive_new_frame
    streamingClient.rigid_body_listener = receive_rigid_body_frame

    # Start up the streaming client now that the callbacks are set up.
    # This will run perpetually, and operate on a separate thread.
    streamingClient.run()
