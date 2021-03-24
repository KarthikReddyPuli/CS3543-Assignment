##
# CS3357 Assignment 3
# Nicholas Porrone (250918147)

# Instructions:
# Make sure you run this file first! , Then you may run UDP_Client.py
# Enjoy!

import binascii
import socket
import struct
import sys
import hashlib
import select

UDP_IP = "0.0.0.0"
UDP_PORT = 5005
UDP_PORT2 = 5002
Client_IP = "192.168.122.228"

unpacker = struct.Struct('I I 8s 32s')

# Create the socket and listen
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)  # ACK
sock2 = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)  # Data Packets

sock.bind((UDP_IP, UDP_PORT))

for x in range(0, 3):

    print("Packet Number: " + str(x+1))

    while True:

        # Receive Data
        data, addr = sock.recvfrom(1024)  # buffer size is 1024 bytes
        UDP_Packet = unpacker.unpack(data)
        print("received from:", addr)
        print("received message:", UDP_Packet)

        # Create the Checksum for comparison
        values = (UDP_Packet[0], UDP_Packet[1], UDP_Packet[2])
        packer = struct.Struct('I I 8s')
        packed_data = packer.pack(*values)
        chksum = bytes(hashlib.md5(packed_data).hexdigest(), encoding="UTF-8")

        # Compare Checksums to test for corrupt data
        if UDP_Packet[3] == chksum and UDP_Packet[1] == x % 2:
            print('CheckSums Match, Sequence Number is correct, Packet OK')

            # Create the Checksum
            values = (1, UDP_Packet[1], UDP_Packet[2])
            UDP_Data = struct.Struct('I I 8s')
            packed_data = UDP_Data.pack(*values)
            chksum = bytes(hashlib.md5(packed_data).hexdigest(), encoding="UTF-8")

            # Build the UDP Packet
            values = (1, UDP_Packet[1], UDP_Packet[2], chksum)

            print("Sending Packet: ")  # Print packet before packing data
            print(values)

            UDP_Packet_Data = struct.Struct('I I 8s 32s')
            UDP_Packet = UDP_Packet_Data.pack(*values)

            # Send Packet through
            sock2.sendto(UDP_Packet, (Client_IP, UDP_PORT2))

            break

        else:

            print('CheckSums do not Match or the Sequence Number is incorrect, Packet is not ok')

            # Create the Checksum
            values = (1, (x+1) % 2, UDP_Packet[2])
            UDP_Data = struct.Struct('I I 8s')
            packed_data = UDP_Data.pack(*values)
            chksum = bytes(hashlib.md5(packed_data).hexdigest(), encoding="UTF-8")

            print("Sending Packet: ")
            print(UDP_Packet)

            # Build the UDP Packet
            values = (1, (x + 1) % 2, UDP_Packet[2], chksum)
            UDP_Packet_Data = struct.Struct('I I 8s 32s')
            UDP_Packet = UDP_Packet_Data.pack(*values)

            # Send Packet through
            sock2.sendto(UDP_Packet, (Client_IP, UDP_PORT2))


