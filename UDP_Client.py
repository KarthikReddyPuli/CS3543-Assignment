import binascii
import socket
import struct
import sys
import hashlib
import select
import threading
import datetime
import time
from copy import deepcopy

sys.setrecursionlimit(10**6)
UDP_IP = "0.0.0.0"
UDP_PORT = 5005
UDP_PORT2 = 5002
SERVER_IP = '127.0.0.1'
fileName = 'CS3543_100MB'
maxThreads = 1
currentThreads = maxThreads
maxRetries = 24
Timeout = 1
TimeoutQueue = 0.1
if len(sys.argv) >= 2:
    SERVER_IP = sys.argv[1]

if len(sys.argv) >= 3:
    fileName = sys.argv[2]

recvUpdate = threading.Event()
recv_UDP_Packet = [-1,0]
in_file = open(fileName, "rb")
PData = None
bytesCount = 1024 * 63
endMessage = b'complete'
data = ""
MAX_QUEUE = 1000
UDP_Data = struct.Struct('I I '+ str(bytesCount) +'s')
UDP_Packet_Data = struct.Struct('I I '+ str(bytesCount) +'s 32s')
print("UDP target IP:", SERVER_IP)
print("UDP target port:", UDP_PORT2)

# Send the UDP Packet
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)  # ACKS
sock2 = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)  # Data Packets

sock2.bind((UDP_IP, UDP_PORT2))
x=0
end=0

# Queue to store the pending packets
class Queue:

  def __init__(self):
    self.queue = list()

  def addtoq(self,dataval):
    self.queue.insert(0,dataval)
    return True

  def size(self):
    return len(self.queue)

  def removefromq(self):
    if len(self.queue)==0:
        return (0,0)
    return self.queue.pop()

dataQueue = Queue()

def updateRecv():
    global recv_UDP_Packet
    global end
    while currentThreads>0:
        recvUpdate.clear()
        timer = select.select([sock2], [], [], Timeout)
        # Check if data was sent
        if timer[0]:
            PData, addr = sock2.recvfrom(bytesCount +1024)
            recv_UDP_Packet = UDP_Packet_Data.unpack(PData)
            #print("Received: ",PData)
        recvUpdate.set()

def sendData(count,data):
    # Create the Checksum
    values = (count, count % 2, data)
    packed_data = UDP_Data.pack(*values)
    chksum = bytes(hashlib.md5(packed_data).hexdigest(), encoding="UTF-8")

    # Build the UDP Packet
    values = (count, count % 2, data, chksum)

    #print("Sending Packet: ")  # Send the packet before packing it
    #print(values)
    UDP_Packet = UDP_Packet_Data.pack(*values)

    # Send Packet through
    sock.sendto(UDP_Packet, (SERVER_IP, UDP_PORT))
    #print("Packet Number: " + str(count+1))
    startTime = datetime.datetime.now()
    timeout = 0

    while recv_UDP_Packet[0] != values[0] :
        #print("recv_UDP_Packet: ",recv_UDP_Packet[0],"  UDP_Packet: ", UDP_Packet[0])
        recvUpdate.wait()
        recvUpdate.clear()
        timeDifference = datetime.datetime.now() - startTime
        if timeDifference.total_seconds() > Timeout :
            timeout = 1
            break

    if timeout == 1:
        if recv_UDP_Packet[0] != UDP_Packet[0]:
            print("Timeout: ",UDP_Packet[0])
            return sendData(count,data)
    
    #print("Passed Timeout")
    UDP_Packet = deepcopy(recv_UDP_Packet)

    # Print the Data

    #print(UDP_Packet)

    # Check if data is corrupt
    if UDP_Packet[3] != chksum:
        print('Checksums Do Not Match, Packet Corrupt')
        return sendData(count,data)

    # Check the sequence number.
    if UDP_Packet[1] == (count+1) % 2:
        print("Incorrect Sequence Number, \nPacket resending ...\n...", x)
        return sendData(count,data)
    return


def readAndSendData():
    while True:
        newData = dataQueue.removefromq()
        if newData[0]!=0:
            sendData(newData[0],newData[1])
        else:
            if end==0 :
                continue
            else:
                return

updateRecvThread = threading.Thread(target=updateRecv)
updateRecvThread.start()
threadsArr = list()
# Create a loop to send each mark
while maxThreads > 0 and end == 0:
    maxThreads = maxThreads - 1
    #print("Packet Number: " + str(x+1))
    data = in_file.read(bytesCount)
    if data == b'' :
        in_file.close()
        data = endMessage
        end = 1
    dataQueue.addtoq((x,data))
    thread = threading.Thread(target=readAndSendData)
    thread.start()
    threadsArr.append(thread)
    #sendData(x,data)
    x = x + 1

while end == 0 :
    #print("Packet Number: " + str(x+1))
    if dataQueue.size() > MAX_QUEUE:
        continue
    data = in_file.read(bytesCount)
    if data == b'' :
        in_file.close()
        data = endMessage
        end = 1
        print("Added end to queue")
    dataQueue.addtoq((x,data))
    x = x+1

for thread in threadsArr:
    thread.join()

currentThreads = 0
