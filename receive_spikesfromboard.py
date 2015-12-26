import socket
import struct
import sys
import time

def simple_receive_UDP(IPI, PORTI, maxsize=64, clean_loop=1 ):
        """
        This function simply creates a socket, reads all the UDP packets as they arrive. It returns a generator after the first call.
        To read the received packets it's necessary to use the .next() method of the returned generator.

        IPI: "X.X.X.X" ordinary IP address from one of the network interfaces available in the host.
        PORTI: 0 to 65535 (but you need to choose a free one).
        maxsize: maximum number of neuron indices to be included in each individual UDP packet (default: 64).
        clean_loop: controls if the socket buffer should be cleaned before starting to receive packets.

        To check who is using a specific port:
            lsof -i :portNumber
            or
            lsof -i udp:portNumber
        """


        buffer_size = 2+maxsize*4 # 2 bytes are the header and maxsize*4 bytes are the spikes per packet 

        sockI = socket.socket(socket.AF_INET,    # IP
                              socket.SOCK_DGRAM) # UDP

        sockI.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1) # Tells the OS that if someone else is using the PORT, it
                                                                    # can use the same PORT without any error/warning msg.
                                                                    # Actually this is useful because if you restart the script
                                                                    # the OS may not release the socket so fast and an error
                                                                    # may occur.141.163.99.4141.163.99.4141.163.99.4141.163.99.4

        sockI.bind((IPI, PORTI)) # Bind the socket to the IPI/PORTI

        # Add here a test to check if the user asked to clean the buffer before start.
        
        while clean_loop:
            if __name__!="__main__":
                print "Cleaning receiving buffer...", "IP/PORT:", IPI, "/", PORTI
            try:
                data = sockI.recv(1, socket.MSG_DONTWAIT) # buffer size is 1 byte, NON blocking.
                print data
            except IOError: # The try and except are necessary because the recv raises a error when no data is received
                clean_loop = 0
        if __name__!="__main__":
            print "Cleaning receiving buffer...", "IP/PORT:", IPI, "/", PORTI, "...Done!"

        sockI.setblocking(1) # Tells the system that the socket recv() method WILL block until a packet is received            

        # Until this point, the code is going to be executed only once each time the system runs.
        yield

        # The second time the function is called using .next(), it starts here.
        while True:
            try:
                data = sockI.recv(buffer_size) # This is a blocking command, therefore the while loop is not going
                                               # to eat up all the processor time.
                yield data

            except IOError:  # Without the IOError even the keyboard "control+C" is caught here!
                print "UDP read error?"                        
                pass

            except ValueError:
                print "ValueError:", data # DEBUG!
                pass #the data is corrupted, a wrong package appeared at the port, etc...

def translate2list(packet):
    '''
    Translates the UDP packet received from SpiNNaker to a Python list with the keys associated to the spikes.
    The conversion to neuron indices must be made using the generated database "input_output_database.db"
    '''
    received = struct.unpack_from("B", packet, 0) # B => unsigned char (one byte, 8bits)
    count = received[0] # number of entries in the packet
    keys = []
    for i in range(count): 
        # The format of the EIEIO header is 16bits, then it's necessary to skip the first two bytes (the 2+ in the line below)
        # Then each packet is made of four bytes (32bits, if the default value is used in the activate_live_output_for) 
        # in a little-endian format.
        # To print the bits, use: ' '.join('{0:08b}'.format(ord(x), 'b') for x in packet)
        received_key = struct.unpack_from("<L", packet, 2 + (i * 4)) # <L => (little-endian) unsigned long (four bytes)
        keys.append(received_key[0])
    return keys

def get_neuron_indices(database='input_output_database.db', label = "spikes_out"):
    '''
    Reads the database file generated when the board is programmed:
    'application_generated_data_files/latest/input_output_database.db'
    and makes it possible to recover the neuron index according with 
    the received key value.
    Returns a dictionary where the keys give the neuron indices.
    '''
    import sqlite3
    conn = sqlite3.connect(database)

    # https://github.com/svadams/SpinnIO
    qresult=conn.execute("SELECT n.event_id as key, n.atom_id as n_id\
                            FROM event_to_atom_mapping as n\
                            JOIN Partitionable_vertices as p ON n.vertex_id = p.vertex_id\
                            WHERE p.vertex_label=\"%s\"" % label)
    translation=qresult.fetchall()

    qresult.close()

    return dict(translation)



if __name__=="__main__":
    if len(sys.argv) < 2:
        print "{} <IP> <port>".format(sys.argv[0])
        print "Prints the neuron indices list to the stdout."
        sys.exit()

    IP = sys.argv[1]

    port = int(sys.argv[2])

    packet_receiver = simple_receive_UDP(IP, port) # creates the generator
    packet_receiver.next() # initialises the port

    while True:
        try:
            packet = packet_receiver.next()
            print translate2list(packet)
        except:
            raise