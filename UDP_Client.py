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
import threading
import datetime

UDP_IP = "0.0.0.0"
UDP_PORT = 5005
UDP_PORT2 = 5002
SERVER_IP = '127.0.0.1'
fileName = 'CS3543_100MB'
if len(sys.argv) >= 2:
    SERVER_IP = sys.argv[1]

if len(sys.argv) >= 3:
    fileName = sys.argv[2]

recvUpdate = threading.Event()
recv_UDP_Packet = [-1]
in_file = open(fileName, "rb")
PData = None
bytesCount = 8
endMessage = b'complete'
data = ""
print("UDP target IP:", SERVER_IP)
print("UDP target port:", UDP_PORT2)

# Send the UDP Packet
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)  # ACKS
sock2 = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)  # Data Packets

sock2.bind((UDP_IP, UDP_PORT2))
x=0
end=0

def updateRecv():
    global recv_UDP_Packet
    UDP_Packet_Data = struct.Struct('I I 8s 32s')
    while True:
        sock2.recvfrom(1024)
        recv_UDP_Packet = UDP_Packet_Data.unpack(PData)
        recvUpdate.set()

def sendData(count,data):
    while True:

        # Create the Checksum
        values = (count, count % 2, data)
        UDP_Data = struct.Struct('I I 8s')
        packed_data = UDP_Data.pack(*values)
        chksum = bytes(hashlib.md5(packed_data).hexdigest(), encoding="UTF-8")

        # Build the UDP Packet
        values = (count, count % 2, data, chksum)

        #print("Sending Packet: ")  # Send the packet before packing it
        #print(values)

        UDP_Packet_Data = struct.Struct('I I 8s 32s')
        UDP_Packet = UDP_Packet_Data.pack(*values)

        # Send Packet through
        sock.sendto(UDP_Packet, (SERVER_IP, UDP_PORT))
        startTime = datetime.datetime.now()
        timeout = 0

        while recv_UDP_Packet[0] != UDP_Packet[0] :
            recvUpdate.wait()
            timeDifference = datetime.datetime.now() - startTime
            if timeDifference.total_seconds() > 1 :
                timeout = 1
                break

        if timeout == 1:
            if recv_UDP_Packet[0] != UDP_Packet[0]:
                print("Timeout")
                continue

        recvUpdate.clear()
        values = (recv_UDP_Packet[0], recv_UDP_Packet[1], recv_UDP_Packet[2])
        packer = struct.Struct('I I 8s')
        packed_data = packer.pack(*values)
        chksum = bytes(hashlib.md5(packed_data).hexdigest(), encoding="UTF-8")

        # Print the Data

        #print(UDP_Packet)

        # Check if data is corrupt
        if UDP_Packet[3] != chksum:
            print('Checksums Do Not Match, Packet Corrupt')
            continue

        # Check the sequence number.
        if UDP_Packet[1] == (count+1) % 2:
            print("Incorrect Sequence Number, \nPacket resending ...\n...", x)
            continue


# Create a loop to send each mark
while end == 0:

    print("Packet Number: " + str(x+1))
    data = in_file.read(bytesCount)
    if data == b'' :
        in_file.close()
        data = endMessage
        end = 1

    thread = threading.Thread(target=sendData,args=(x,data,))
    thread.start()

    x = x + 1
