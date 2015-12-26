'''
Simple interface to send spikes to SpiNNaker using ethernet communication.
This module can also be used in the command line.
'''

import socket
import sys
import os
import time
import struct

def simple_send_UDP(IP, PORT, packet):
    """
    This is a very simple function to send packets using UDP.
    In case of an IOError, a message is printed and it keeps trying to send.

    IP: who is going to receive the packet
    PORT: port where the packet will be received
    packet: string containing the information to be sent.
    """
    sockO = (socket.socket(socket.AF_INET,     # IP
                           socket.SOCK_DGRAM)) # UDP

    # Keeps trying to send until the packet is sent
    while True:
        try:
            sockO.sendto(packet, (IP, PORT))
            break

        except IOError:
            print "simple_send_UDP IO error?"


def format_packet(neuron_indices, maxsize=64, binary_header_cfg='0b00001000'):
    """
    Receives a list of neuron indices and returns a list of packets formatted to 
    be sent to SpiNNaker using UDP. The packets will be maxsize long.

    neuron_indices: list containing the indices of the neurons receiving spikes.
    maxsize: maximum number of indices to be included in each individual UDP packet (default: 64).
    binary_header_cfg: 8 bits used to tell SpiNNaker which type of packet is this. Here it's used
    basic packet with no prefix (15-14:00), no payload (13:0), payload is not timestamps (12:0),
    32-bit key (11-10:10) and version (9-8:00). 

    """


    cfg_header = int(binary_header_cfg,2)

    n_spks = len(neuron_indices)

    # Generates the packet headers by testing if there're more than maxsize neuron indices
    if n_spks>maxsize:
        ratio = n_spks/maxsize
        n_pckts = ratio + (1 if n_spks%maxsize else 0)
        formatted_packets = []
        for pi in range(0,ratio):
            pck_header = [struct.pack('<BB',maxsize,cfg_header)] # 2bytes = 16bits
            pck_payload = [struct.pack("<L", key) for key in neuron_indices[ratio*pi:ratio*(pi+1)]]
            formatted_packets.append("".join(pck_header+pck_payload))

        # in case there's a remainder
        if n_spks%maxsize:
            pck_header = [struct.pack('<BB',n_spks%maxsize,cfg_header)] # 2bytes = 16bits
            pck_payload = [struct.pack("<L", key) for key in neuron_indices[ratio*pi:ratio*pi+n_spks%maxsize]]
            formatted_packets.append("".join(pck_header+pck_payload))
    else:
        n_pckts = 1
        pck_header=[struct.pack('<BB',n_spks,cfg_header)]
        pck_payload = [struct.pack("<L", key) for key in neuron_indices]
        formatted_packets = ["".join(pck_header+pck_payload)]

    return formatted_packets


if __name__=="__main__":

    from json import loads

    list_of_neuron_indices = []

    # http://stackoverflow.com/a/13143479
    if os.fstat(sys.stdin.fileno()).st_size > 0:
        for line in sys.stdin:
            list_of_neuron_indices = line

    if list_of_neuron_indices == []:        
        if len(sys.argv) < 4:
            print "{0} <machine-name> <port> <list of lists of neuron indices> <loop>".format(sys.argv[0])
            print "<loop> is optional."
            print "The script also tries to read the stdin for the neuron indices and in this situation <list of lists of neuron indices> must not be provided."
            sys.exit()
        else:
            list_of_neuron_indices = loads(sys.argv[3])
    else:
        if len(sys.argv) < 3:
            print "{0} <machine-name> <port> <loop>".format(sys.argv[0])
            print "<loop> is optional."
            print "A <list of lists of neuron indices> must be provided through the stdin."
            sys.exit()

    remote_host=sys.argv[1]

    remote_port=int(sys.argv[2])

    if len(sys.argv) == 5:
        assert sys.argv[4]=="0" or sys.argv[4]=="1"
        loop=bool(int(sys.argv[4]))
    else:
        loop=False

    time_between_keys = 0.1
    time_between_sequences = 0.2


    while True:
        for keys in list_of_neuron_indices:

            packet_list = format_packet(keys)

            for packet in packet_list:
                print packet
                simple_send_UDP(remote_host, remote_port, packet)
                time.sleep(time_between_keys)

        if not loop:
            break

        time.sleep(time_between_sequences)