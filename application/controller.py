import pickle
import queue
import threading
import zlib
from multiprocessing import Process, Queue

import cv2
import pyaudio

from LiveStream.client.client_udp import Client
from LiveStream.config import *
from LiveStream.config import AUDIO_HOST, AUDIO_PORT, VIDEO_HOST, VIDEO_PORT, AUDIO_FRAME_RATE, AUDIO_BUFFER_SIZE
from LiveStream.server.server_udp import Server

USE_MULTIPROCESSING = True


class ClientController:
    def __init__(self):
        self.client_audio = None
        self.client_video = None

    @staticmethod
    def res_1080p(cv):
        cv.set(3, 1920)
        cv.set(4, 1080)

    @staticmethod
    def res_720p(cv):
        cv.set(3, 1280)
        cv.set(4, 720)

    @staticmethod
    def res_480p(cv):
        cv.set(3, 640)
        cv.set(4, 480)

    @staticmethod
    def res_320p(cv):
        cv.set(3, 480)
        cv.set(4, 360)

        return cv

    @staticmethod
    def set_res(cv, width, height):
        cv.set(3, width)
        cv.set(4, height)

    def start_servers(self):
        server_video = Server(VIDEO_HOST, VIDEO_PORT)
        server_audio = Server(AUDIO_HOST, AUDIO_PORT)

        if VIDEO_HOST == 'localhost':
            threading.Thread(target=server_video.start).start()
        if AUDIO_HOST == 'localhost':
            threading.Thread(target=server_audio.start).start()

    def setup_clients(self):
        print("Connecting to server ... ")
        self.client_video = Client(type=TYPE_VIDEO, host=VIDEO_HOST, port=VIDEO_PORT)
        self.client_video.setup()
        print("Client setup done | {}".format(TYPE_VIDEO))

        self.client_audio = Client(type=TYPE_AUDIO, host=AUDIO_HOST, port=AUDIO_PORT)
        self.client_audio.setup()
        print("Client setup done | {}".format(TYPE_AUDIO))

    def send_video_frames(self, output_queue):
        vc = self.get_vc_opencv()
        # ClientController.res_1080p(vc)
        if not vc:
            print("Error reading from camera")
            return

        retries = 0

        while True:
            try:
                frame = self.capture_frame(vc)
                output_queue.put(('ME', frame))
                compressed_byte_stream = zlib.compress(pickle.dumps(frame))
                self.client_video.send(compressed_byte_stream)
                retries = 0
            except Exception as e:
                retries += 1
                print(e)
                if retries == 10:
                    break

        print("Error sending video")

    def stream_video(self, output_video_queue):
        if USE_MULTIPROCESSING:
            p1 = Process(target=self.send_video_frames, args=(output_video_queue,))
            p1.start()
            print("Process created for sending video")
        else:
            t1 = threading.Thread(target=self.send_video_frames, args=(output_video_queue,))
            t1.start()
            print("Thread created for sending video")

        if USE_MULTIPROCESSING:
            p2 = Process(target=self.client_video.receive, args=(output_video_queue,))
            p2.start()
            print("Process created for receiving video")
        else:
            t2 = threading.Thread(target=self.client_video.receive, args=(output_video_queue,))
            t2.start()
            print("Thread created for receiving video")

    def send_audio_frames(self):
        device = pyaudio.PyAudio()

        audio_stream_in = device.open(
            format=pyaudio.paFloat32,
            channels=2,
            rate=AUDIO_FRAME_RATE,
            input=True,
            frames_per_buffer=AUDIO_BUFFER_SIZE
        )
        retries = 0
        while True:
            try:
                frame = audio_stream_in.read(AUDIO_BUFFER_SIZE)
                compressed_byte_stream = zlib.compress(pickle.dumps(frame))

                self.client_audio.send(compressed_byte_stream)
                retries = 0
            except Exception as e:
                print(e)
                retries += 1

                if retries == 10:
                    break

        print("Error sending audio")

    def process_audio(self, audio_output_queue):
        device = pyaudio.PyAudio()

        audio_stream_out = device.open(
            format=pyaudio.paFloat32,
            channels=2,
            rate=AUDIO_FRAME_RATE,
            output=True,
            frames_per_buffer=AUDIO_BUFFER_SIZE
        )

        while True:
            try:
                client, compressed_byte_stream = audio_output_queue.get(block=True)

                frame = pickle.loads(zlib.decompress(compressed_byte_stream))

                audio_stream_out.write(frame)
            except Exception as e:
                print(e)

    def stream_audio(self):
        audio_output_queue = None
        if USE_MULTIPROCESSING:
            audio_output_queue = Queue()
        else:
            audio_output_queue = queue.Queue()

        if USE_MULTIPROCESSING:
            p1 = Process(target=self.send_audio_frames)
            p1.start()
            print("Process created for sending audio")

            Process(target=self.client_audio.receive, args=(audio_output_queue,)).start()
            print("Process created for receiving audio")

            p2 = Process(target=self.process_audio, args=(audio_output_queue,))
            p2.start()
            print("Process created for processing received  audio")

        else:
            t1 = threading.Thread(target=self.send_audio_frames)
            t1.start()
            print("Thread created for sending audio")

            threading.Thread(target=self.client_audio.receive, args=(audio_output_queue,)).start()
            print("Thread created for receiving audio")

            t2 = threading.Thread(target=self.process_audio, args=(audio_output_queue,))
            t2.start()
            print("Thread created for processing received  audio")

    def get_vc_opencv(self):
        vc = None

        try:
            vc = cv2.VideoCapture(0)
            check, frame = vc.read()
            print("Check 1:{}".format(check))
            if not check:
                vc = cv2.VideoCapture(1)
                print("Check 2:{}".format(check))
                check, frame = vc.read()

                if not check:
                    vc = cv2.VideoCapture(-1)
                    check, frame = vc.read()
                    print("Check 3:{}".format(check))

                    if not check:
                        vc = None
                        raise Exception("Error reading from cam. Cam might be busy")
            # vc.set(cv2.CAP_PROP_FRAME_WIDTH, 240)
            # vc.set(cv2.CAP_PROP_FRAME_HEIGHT, 180)

            print(
                "Actual resolution: {}x{}".format(vc.get(cv2.CAP_PROP_FRAME_WIDTH), vc.get(cv2.CAP_PROP_FRAME_HEIGHT)))
            # window = tkinter.Tk()
            # self.canvas = tkinter.Canvas(window, width=500, height=500)
        except Exception as e:
            print(e)

        return vc

    def capture_frame(self, vc):
        check, frame = vc.read()
        return frame
