from LiveStream.client.client_udp import Client
from LiveStream.config import TYPE_VIDEO, VIDEO_PORT, VIDEO_HOST


class VideoController:
    def __init__(self):
        pass

    def setup(self):
        self.client = Client(type=TYPE_VIDEO, host=VIDEO_HOST, port=VIDEO_PORT)
        self.client.setup()
        print("Client setup done | {}".format(TYPE_VIDEO))
