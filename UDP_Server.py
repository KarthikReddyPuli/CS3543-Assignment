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
import codecs
import threading

fileUpdate = threading.Event()
endLoop = threading.Event()

UDP_IP = "0.0.0.0"
UDP_PORT = 5005
UDP_PORT2 = 5002
Client_IP = '127.0.0.1'
bytesCount = 8
fileName = 'out_CS3543_100MB'
if len(sys.argv) == 2:
    Client_IP = sys.argv[1]
if len(sys.argv) >= 3:
    fileName = sys.argv[2]
endMessage = b'complete'
out_file = open(fileName, "wb")

unpacker = struct.Struct('I I 8s 32s')

# Create the socket and listen
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)  # ACK
sock2 = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)  # Data Packets

sock.bind((UDP_IP, UDP_PORT))

end = 0
x = 0
writeCount = 0

def writeData(count,data):
    global writeCount
    if(writeCount > count):
        return
    while count != writeCount :
        fileUpdate.wait()

    fileUpdate.clear()
    out_file.write(data)
    writeCount = writeCount+1
    fileUpdate.set()

def closeFile(count):
    if(writeCount > count):
        return
    endLoop.set()
    while count != writeCount :
        fileUpdate.wait()

    out_file.close()
    print("File closed")

def receive_data(data,addr):

    # Receive Data
    UDP_Packet = unpacker.unpack(data)
    #print("received from:", addr)
    #print("received message:", UDP_Packet)

    # Create the Checksum for comparison
    values = (UDP_Packet[0], UDP_Packet[1], UDP_Packet[2])
    packer = struct.Struct('I I 8s')
    packed_data = packer.pack(*values)
    chksum = bytes(hashlib.md5(packed_data).hexdigest(), encoding="UTF-8")

    # Compare Checksums to test for corrupt data
    if UDP_Packet[3] == chksum and UDP_Packet[1] == UDP_Packet[0] % 2:
        #print('CheckSums Match, Sequence Number is correct, Packet OK')

        # Create the Checksum
        values = (1, UDP_Packet[1], UDP_Packet[2])
        UDP_Data = struct.Struct('I I 8s')
        packed_data = UDP_Data.pack(*values)
        chksum = bytes(hashlib.md5(packed_data).hexdigest(), encoding="UTF-8")

        # Build the UDP Packet
        values = (UDP_Packet[0], UDP_Packet[1], UDP_Packet[2], chksum)

        #print("Sending Packet: ")  # Print packet before packing data
        #print(values)

        UDP_Packet_Data = struct.Struct('I I 8s 32s')
        UDP_Packet_send = UDP_Packet_Data.pack(*values)

        # Send Packet through
        sock2.sendto(UDP_Packet_send, (Client_IP, UDP_PORT2))

        if UDP_Packet[2] == endMessage:
            closeFile(UDP_Packet[0])
        else:
            offset = removeNullBytes(UDP_Packet[2])
            writeData(UDP_Packet[0],UDP_Packet[2][:offset])

    else:

        print('CheckSums do not Match or the Sequence Number is incorrect, Packet is not ok')

        # Create the Checksum
        values = (1, (UDP_Packet[0]+1) % 2, UDP_Packet[2])
        UDP_Data = struct.Struct('I I 8s')
        packed_data = UDP_Data.pack(*values)
        chksum = bytes(hashlib.md5(packed_data).hexdigest(), encoding="UTF-8")

        #print("Sending Packet: ")
        #print(UDP_Packet)

        # Build the UDP Packet
        values = (1, (UDP_Packet[0] + 1) % 2, UDP_Packet[2], chksum)
        UDP_Packet_Data = struct.Struct('I I 8s 32s')
        UDP_Packet = UDP_Packet_Data.pack(*values)

        # Send Packet through
        sock2.sendto(UDP_Packet, (Client_IP, UDP_PORT2))

def removeNullBytes(input):
    offset = 8
    i=7
    while i>-1:
        if input[i] == 0:
            offset = offset - 1
            i = i - 1
        else:
            break
    return offset

while endLoop.is_set() == False:

    print("Packet Number: " + str(x+1))
    data, addr = sock.recvfrom(1024)
    #receive_data(data,addr)
    thread = threading.Thread(target=receive_data,args=(data,addr,))
    thread.start()
    x = x+1


