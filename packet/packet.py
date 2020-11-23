from datetime import datetime


class PacketTypes:
    SETUP = 0
    DATA = 1


class SimpleRTSPPacket:
    HEADER_LEN = 13

    def __init__(self):
        self.header = bytearray(SimpleRTSPPacket.HEADER_LEN)
        self.payload = b''
        self.payload_length = 0

    def encode(self, packet_type, seq_no=0, fragment_no=0, total_fragments=0, offset=0, payload_len=0, payload=b''):
        timestamp = int(datetime.strftime(datetime.now(), '%H%M%S%f'))

        self.header[0] = packet_type
        self.header[1] = (seq_no >> 8) & 0xFF
        self.header[2] = seq_no & 0xFF

        self.header[3] = (fragment_no >> 8) & 0xFF
        self.header[4] = fragment_no & 0xFF

        self.payload = payload

        self.header[5] = (total_fragments >> 8) & 0xFF
        self.header[6] = total_fragments & 0xFF

        self.header[5] = (total_fragments >> 8) & 0xFF
        self.header[6] = total_fragments & 0xFF

        self.header[7] = (offset >> 16) & 0xFF
        self.header[8] = (offset >> 8) & 0xFF
        self.header[9] = offset & 0xFF

        self.header[10] = (payload_len >> 16) & 0xFF
        self.header[11] = (payload_len >> 8) & 0xFF
        self.header[12] = payload_len & 0xFF

    def decode(self, byte_stream):
        self.header = byte_stream[:SimpleRTSPPacket.HEADER_LEN]
        self.payload = byte_stream[SimpleRTSPPacket.HEADER_LEN:]

    def packet(self):
        return self.header + self.payload

    def packet_type(self):
        return self.header[0]

    def seq_no(self):
        return self.header[1] << 8 | self.header[2]

    def fragment_no(self):
        return self.header[3] << 8 | self.header[4]

    def total_fragments(self):
        return self.header[5] << 8 | self.header[6]

    def offset(self):
        return self.header[7] << 16 | self.header[8] << 8 | self.header[9]

    def payload_len(self):
        return self.header[10] << 16 | self.header[11] << 8 | self.header[12]

    @staticmethod
    def get_packet_type(byte_stream):
        return byte_stream[0]

    @staticmethod
    def get_packet_len(byte_stream):
        return byte_stream[10] << 16 | byte_stream[11] << 8 | byte_stream[12]

    @staticmethod
    def get_seq_no(byte_stream):
        return byte_stream[1] << 8 | byte_stream[2]
