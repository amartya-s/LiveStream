import socket
import sys
import traceback

from LiveStream.packet.packet import SimpleRTSPPacket, PacketTypes


class Server:
    PAYLOAD_LEN = 1350
    MSGLEN = PAYLOAD_LEN + SimpleRTSPPacket.HEADER_LEN
    CTR = 0

    frames = dict()

    def __init__(self, host, port):
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.bind((host, port))

        self.socket = s

        print('Socket created')

    def start(self):
        print("Waiting for data")
        while True:
            try:
                chunk, from_address = self.socket.recvfrom(Server.MSGLEN)
                host, port = from_address

                packet_type = SimpleRTSPPacket.get_packet_type(chunk)

                if packet_type == PacketTypes.SETUP:
                    self.socket.sendto(b'OK', from_address)
                    print("New client connected: {}".format(from_address))

                if packet_type == PacketTypes.DATA:
                    seq_no = SimpleRTSPPacket.get_seq_no(chunk)
                    self.socket.sendto(chunk, from_address)

            except Exception as e:
                print(e)
                ex_type, ex, tb = sys.exc_info()
                traceback.print_tb(tb)
                print("Packet dropped #{}".format(seq_no))
