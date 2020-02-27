from NatNetClient import NatNetClient
import socket
import numpy as np
from queue import Queue

class Mocapreader:

    def __init__(self, bodylist):
        IP = socket.gethostbyname(socket.gethostname())
        print(IP)
        self.streamingClient = NatNetClient(server_ip_address="192.168.0.105", local_ip_address="192.168.0.143")
        self.queues={}
        # Configure the streaming client to call our rigid body handler on the emulator to send data out.
        self.streamingClient.new_frame_listener = self.receive_new_frame
        self.streamingClient.rigid_body_listener = self.receive_rigid_body_frame
        self.datalog={}
        self.bodylist=bodylist
        for body in self.bodylist:
            self.datalog[body]=[]
            self.queues[body]=[True,Queue(maxsize=1000)]

    def save_log(self, filename, bodyid):
        np.savetxt(filename,np.array(self.datalog[bodyid]), delimiter=',')

    def reset_log(self):
        self.datalog={}
        for body in self.bodylist:
            self.datalog[body]=[]

    def run(self):
        # This is a callback function that gets connected to the NatNet client and called once per mocap frame.
        # Start up the streaming client now that the callbacks are set up.
        # This will run perpetually, and operate on a separate thread.
        self.streamingClient.run()

    def receive_new_frame(self, frame_number, marker_set_count, unlabeled_markers_count, rigid_body_count,
                          skeleton_count, labeled_marker_count, time_code, time_code_sub, timestamp,
                          is_recording, tracked_models_changed):
        pass


    # This is a callback function that gets connected to the NatNet client. It is called once per rigid body per frame
    def receive_rigid_body_frame(self, id, position, rotation):
        if id in self.bodylist:
            self.queues[id][1].put(np.array(list(position)+list(rotation)))
            #self.datalog[id].append(list(position)+list(rotation))