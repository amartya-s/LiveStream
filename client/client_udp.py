import socket
import sys
import time
import traceback

from LiveStream.config import PAYLOAD_MAX_LEN
from LiveStream.packet.packet import SimpleRTSPPacket, PacketTypes

MSGLEN = PAYLOAD_MAX_LEN + SimpleRTSPPacket.HEADER_LEN


class Client:
    def __init__(self, type, host, port):
        self.socket = None
        self.type = type
        self.server_address = (host, port)
        self.seq_no = 0

    def set_receiver(self, queue):
        self.receive_queue = queue

    def setup(self):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

        packet = SimpleRTSPPacket()
        packet.encode(PacketTypes.SETUP)
        self.socket.sendto(packet.packet(), self.server_address)

        response = self.socket.recvfrom(1024)

        print(response)

        print("{} | Client socket created".format(self.type))

    def send(self, payload):
        start_time = time.time()
        payload_len = len(payload)
        total_fragmentation = int(payload_len / PAYLOAD_MAX_LEN) if payload_len % PAYLOAD_MAX_LEN == 0 else int(
            payload_len / PAYLOAD_MAX_LEN) + 1

        partial_payload = payload[0: PAYLOAD_MAX_LEN]

        offset = 0
        fragment_no = 1

        while partial_payload:
            data_packet = SimpleRTSPPacket()
            data_packet.encode(packet_type=PacketTypes.DATA, seq_no=self.seq_no, fragment_no=fragment_no,
                               total_fragments=total_fragmentation, offset=offset, payload_len=payload_len,
                               payload=partial_payload)

            self.socket.sendto(data_packet.packet(), self.server_address)

            offset += PAYLOAD_MAX_LEN
            partial_payload = payload[offset: offset + PAYLOAD_MAX_LEN]

            fragment_no += 1

        if self.seq_no % 10 == 0:
            print(
                "{} | Sent frames: {} | Total fragmentation: {} Last frame duration: {}s".format(self.type, self.seq_no,
                                                                                                 total_fragmentation,
                                                                                                 round(
                                                                                                     time.time() - start_time,
                                                                                                     3)))

        self.seq_no += 1

    def receive(self, output_queue):
        self.payload_by_seq_no = dict()
        while True:
            try:
                chunk, address = self.socket.recvfrom(MSGLEN)
                self.process_packet(chunk, output_queue)
            except Exception as e:
                print(e)
                ex_type, ex, tb = sys.exc_info()
                traceback.print_tb(tb)

    def process_packet(self, chunk, output_queue):
        data_packet = SimpleRTSPPacket()
        data_packet.decode(chunk)

        seq_no = data_packet.seq_no()
        fragment_no = data_packet.fragment_no()
        payload = data_packet.payload
        total_fragments = data_packet.total_fragments()
        offset = data_packet.offset()
        payload_len = data_packet.payload_len()
        # print("received seq:{} | fragment no: {}".format(seq_no, fragment_no))
        if seq_no not in self.payload_by_seq_no:
            self.payload_by_seq_no[seq_no] = {'start_time': time.time(), 'byte_stream': bytearray(payload_len),
                                              'fragments_count': 0, 'data': []}

        self.payload_by_seq_no[seq_no]['byte_stream'][offset:] = payload
        self.payload_by_seq_no[seq_no]['fragments_count'] += 1

        if self.payload_by_seq_no[seq_no]['fragments_count'] == total_fragments:
            payload = self.payload_by_seq_no[seq_no]['byte_stream']
            # if frame_no < self.frame_no:
            #     print("OUT OF ORDER FRAME DETECTED: {}".format(frame_no))
            #     return

            output_queue.put(('Client', payload))
            # output_queue.put(('Client1', payload))
            # output_queue.put(('Client2', payload))
            # output_queue.put(('Client3', payload))

            # if seq_no % 10 == 0:
            print("{} | Received frames count: {} | Last frame duration {}s ".format(self.type, seq_no, round(
                time.time() - self.payload_by_seq_no[seq_no]['start_time'], 3)))

            del self.payload_by_seq_no[seq_no]
