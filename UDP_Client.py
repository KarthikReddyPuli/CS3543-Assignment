##
# CS3357 Assignment 3
# Nicholas Porrone (250918147)

# Instructions:
# Be sure to run UDP_Server.py before this file!
# Enjoy :)

import binascii
import socket
import struct
import sys
import hashlib
import select

UDP_IP = "0.0.0.0"
UDP_PORT = 5005
UDP_PORT2 = 5002
SERVER_IP = "192.168.122.186"
PData = None
DataA = (b'NCC-1701', b'NCC-1664', b'NCC-1017')
print("UDP target IP:", UDP_IP)
print("UDP target port:", UDP_PORT2)

# Send the UDP Packet
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)  # ACKS
sock2 = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)  # Data Packets

sock2.bind((UDP_IP, UDP_PORT2))

# Create a loop to send each mark
for x in range(0, 3):

    print("Packet Number: " + str(x+1))

    while True:

        # Create the Checksum
        values = (0, x % 2, DataA[x])
        UDP_Data = struct.Struct('I I 8s')
        packed_data = UDP_Data.pack(*values)
        chksum = bytes(hashlib.md5(packed_data).hexdigest(), encoding="UTF-8")

        # Build the UDP Packet
        values = (0, x % 2, DataA[x], chksum)

        print("Sending Packet: ")  # Send the packet before packing it
        print(values)

        UDP_Packet_Data = struct.Struct('I I 8s 32s')
        UDP_Packet = UDP_Packet_Data.pack(*values)

        # Send Packet through
        sock.sendto(UDP_Packet, (SERVER_IP, UDP_PORT))

        # Create a timer
        timer = select.select([sock2], [], [], 0.009)

        # Check if data was sent
        if timer[0]:
            PData, addr = sock2.recvfrom(1024)
        # If not,
        else:
            print("Timer Expired")
            PData = None

        if PData is None:
            print("data is none")
            continue

        else:
            print("Recieved: ")

            # Unpack Data
            UDPRecv = UDP_Packet_Data.unpack(PData)
            UDP_Packet = UDP_Packet_Data.unpack(PData)
            values = (UDP_Packet[0], UDP_Packet[1], UDP_Packet[2])
            packer = struct.Struct('I I 8s')
            packed_data = packer.pack(*values)
            chksum = bytes(hashlib.md5(packed_data).hexdigest(), encoding="UTF-8")

            # Print the Data

            print(UDP_Packet)

            # Check if data is corrupt
            if UDP_Packet[3] == chksum:
                print('CheckSums Match')
            else:
                print('Checksums Do Not Match, Packet Corrupt')
                continue

            # Check the sequence number.
            if UDP_Packet[1] == (x+1) % 2:
                print("Incorrect Sequence Number, \nPacket resending ...\n...", x)
                continue
            else:
                print("Sequence Number Correct")

            # Check if data is Acknowledged
            if UDP_Packet[0] == 1:
                print('Packet is Acknowledged')
                break
            else:
                print('Packet is not Acknowlegde')
