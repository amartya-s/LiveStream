import io
import pickle
import tkinter as tk
import urllib.request
import zlib
from multiprocessing import Queue

from PIL import ImageTk, Image

from LiveStream.application.controller import ClientController


class App:
    def __init__(self, root):
        self.master = root
        self.main_frame = None
        self.client_containers = dict()
        self.output_video_queue = Queue()
        self.controller = ClientController()
        self.create_widgets()
        self.initialize()

    def initialize(self):
        self.controller.start_servers()
        self.controller.setup_clients()

    def create_widgets(self):
        main_frame = tk.Frame(self.master)
        main_frame.pack()

        client_frame1 = tk.Frame(master=main_frame)
        client_frame1.pack(side=tk.LEFT)

        client_frame2 = tk.Frame(master=main_frame)
        client_frame2.pack(side=tk.RIGHT)

        bt = tk.Button(master=self.master, text="Start Broadcasting", font="Times 20 bold", borderwidth=4,
                       relief="raised", justify="center", width=20, height=1, command=self.start_broadcasting)
        bt.pack(side=tk.BOTTOM, pady=30)

        self.main_frame = main_frame

        print("Widgets created")

    def show_frame(self):
        raw_data = urllib.request.urlopen("https://i.postimg.cc/pdwrKzwK/congratulations.png").read()

        window = tk.Toplevel(self.master)

        temp = tk.Frame(window, bg='pink', relief='ridge', borderwidth=2)
        temp.pack()
        img = Image.open(io.BytesIO(raw_data))
        self.tkimage = ImageTk.PhotoImage(img)
        tk.Label(temp, image=self.tkimage, width=1800, height=1080).pack()

        print(img)

    def start_broadcasting(self):
        # self.show_frame()

        self.controller.stream_video(self.output_video_queue)
        self.controller.stream_audio()

        self.process_video_frames()

    def create_container(self):
        label = tk.Label(self.main_frame, relief='ridge', borderwidth=5)
        label.pack(side=tk.LEFT, padx=10, pady=50)
        return label

    def update_UI(self, frame, container):
        # print("{}x{}".format(width,height))
        # b, g, r = cv2.split(frame)
        # frame = cv2.merge((r, g, b))
        # frame=cv2.resize(frame, (1080, 720))
        # ImageTk.PhotoImage(image=img)

        photo = ImageTk.PhotoImage(image=Image.fromarray(frame))
        # print(photo)
        height, width, no_channels = frame.shape
        print(photo)

        container.configure(image=photo, width=width, height=height)
        container.image = photo
        container.update()

    def process_video_frames(self):
        try:
            client, frame = self.output_video_queue.get(block=True)  # wait till we get a frame, sender might be slow
            # print("Queue len: {}".format(self.output_video_queue.qsize()))
            if client != 'ME':
                frame = pickle.loads(zlib.decompress(frame))

            if client not in self.client_containers:
                self.client_containers[client] = self.create_container()
                print("Created container for {}".format(client))

            self.update_UI(frame, self.client_containers[client])

            # cv2.imshow(client, frame)
            # cv2.waitKey(10)
        except Exception as e:
            print(e)
        self.master.after(1, self.process_video_frames)


if __name__ == '__main__':
    root = tk.Tk()

    app = App(root)

    root.title("LiveStream")
    root.geometry("1920x720")
    tk.mainloop()
