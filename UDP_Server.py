##
# CS3357 Assignment 3
# Nicholas Porrone (250911024147)

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
import time
from hurry.filesize import size

fileUpdate = threading.Event()
endLoop = threading.Event()
repeatRecv = threading.Event()

UDP_IP = "0.0.0.0"
UDP_PORT = 5005
UDP_PORT2 = 5002
Client_IP = '127.0.0.1'
bytesCount = 1024
maxThreads = 8
fileName = 'out_CS3543_100MB'
if len(sys.argv) == 2:
    Client_IP = sys.argv[1]
if len(sys.argv) >= 3:
    fileName = sys.argv[2]
endMessage = b'complete'
out_file = open(fileName, "wb")

unpacker = struct.Struct('I I 1024s 32s')

# Create the socket and listen
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)  # ACK
sock2 = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)  # Data Packets

sock.bind((UDP_IP, UDP_PORT))

end = 0
x = 0
writeCount = 1
Timeout = 0.5

class Queue:

  def __init__(self):
    self.queue = list()

  def addtoq(self,dataval):
    self.queue.insert(0,dataval)
    repeatRecv.set()
    return True

  def size(self):
    return len(self.queue)

  def removefromq(self):
    if len(self.queue)==0:
        return (0,0)
    return self.queue.pop()

dataQueue = Queue()

def writeData(count,data):
    global writeCount
    if(writeCount > count):
        return
    while count != writeCount :
        fileUpdate.wait()

    fileUpdate.clear()
    out_file.write(data)
    writeCount = writeCount+1
    print("Wrote: ",size(count*bytesCount))
    fileUpdate.set()
    return

def closeFile(count):
    if(writeCount > count):
        return
    while count != writeCount :
        fileUpdate.wait()
    endLoop.set()
    repeatRecv.set()
    out_file.close()
    print("File closed")

def receive_data():
    while endLoop.is_set() == False:
        newData = dataQueue.removefromq()
        if newData[0] != 0:
            UDP_Packet = unpacker.unpack(newData[0])
            #print("received from:", addr)
            #print("received message:", UDP_Packet)

            # Create the Checksum for comparison
            values = (UDP_Packet[0], UDP_Packet[1], UDP_Packet[2])
            packer = struct.Struct('I I 1024s')
            packed_data = packer.pack(*values)
            chksum = bytes(hashlib.md5(packed_data).hexdigest(), encoding="UTF-8")

            # Compare Checksums to test for corrupt data
            if UDP_Packet[3] == chksum and UDP_Packet[1] == UDP_Packet[0] % 2:
                #print('CheckSums Match, Sequence Number is correct, Packet OK')
                # Build the UDP Packet
                values = (UDP_Packet[0], UDP_Packet[1], UDP_Packet[2], chksum)

                #print("Sending Packet: ", values)  # Print packet before packing data

                UDP_Packet_Data = struct.Struct('I I 1024s 32s')
                UDP_Packet_send = UDP_Packet_Data.pack(*values)

                # Send Packet through
                sock2.sendto(UDP_Packet_send, (Client_IP, UDP_PORT2))
                offset = removeNullBytes(UDP_Packet[2])
                if UDP_Packet[2][:offset] == endMessage:
                    closeFile(UDP_Packet[0])
                else:
                    writeData(UDP_Packet[0],UDP_Packet[2][:offset])
            else:

                print('CheckSums do not Match or the Sequence Number is incorrect, Packet is not ok')

                # Create the Checksum
                values = (1, (UDP_Packet[0]+1) % 2, UDP_Packet[2])
                UDP_Data = struct.Struct('I I 1024s')
                packed_data = UDP_Data.pack(*values)
                chksum = bytes(hashlib.md5(packed_data).hexdigest(), encoding="UTF-8")

                #print("Sending Packet: ")
                #print(UDP_Packet)

                # Build the UDP Packet
                values = (1, (UDP_Packet[0] + 1) % 2, UDP_Packet[2], chksum)
                UDP_Packet_Data = struct.Struct('I I 1024s 32s')
                UDP_Packet = UDP_Packet_Data.pack(*values)

                # Send Packet through
                sock2.sendto(UDP_Packet, (Client_IP, UDP_PORT2))
        else:
            repeatRecv.wait()


def removeNullBytes(input):
    offset = bytesCount
    i=offset - 1
    while i>-1:
        if input[i] == 0:
            offset = offset - 1
            i = i - 1
        else:
            break
    return offset

repeatRecv.clear()

while maxThreads>0 and endLoop.is_set() == False:
    maxThreads = maxThreads - 1
    #print("Packet Number: " + str(x+1))
    data, addr = sock.recvfrom(2048)
    dataQueue.addtoq((data,addr))
    repeatRecv.clear()
    thread = threading.Thread(target=receive_data)
    thread.start()
    x = x+1

while endLoop.is_set() == False:
    #print("Packet Number: " + str(x+1))
    data, addr = sock.recvfrom(2048)
    dataQueue.addtoq((data,addr))
    repeatRecv.clear()
    x = x+1