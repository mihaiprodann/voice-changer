import queue
import threading
import numpy as np
import sounddevice as sd


PREFERRED_HOSTS = ("PulseAudio", "PipeWire")
VC_SINK_NAME = "VoiceChanger Sink"


class DSPState:
    def __init__(self, sr: int):
        self.sr = sr


def process_block(x: np.ndarray, state: DSPState) -> np.ndarray:
        return x


class AudioEngine:
    def __init__(self):
        self.stream = None
        self.q_status = queue.Queue()
        self.lock = threading.Lock()
        self.state = None
        self.running = False
        self.current_sr = None
        self.blocksize = None
        self.indev = None
        self.outdev = None

    def list_devices(self):
        devs = sd.query_devices()
        hostapis = sd.query_hostapis()
        in_list, out_list = [], []
        for i, d in enumerate(devs):
            host = hostapis[d["hostapi"]]["name"]
            if d["max_input_channels"] > 0 and host in PREFERRED_HOSTS:
                in_list.append((i, d["name"], host))
            if d["max_output_channels"] > 0 and host in PREFERRED_HOSTS:
                out_list.append((i, d["name"], host))
        if not in_list or not out_list:
            for i, d in enumerate(devs):
                host = hostapis[d["hostapi"]]["name"]
                if d["max_input_channels"] > 0 and i not in [x[0] for x in in_list]:
                    in_list.append((i, d["name"], host))
                if d["max_output_channels"] > 0 and i not in [x[0] for x in out_list]:
                    out_list.append((i, d["name"], host))
        return in_list, out_list

    def find_output_index(self, prefer_name=VC_SINK_NAME):
        _, out_devs = self.list_devices()
        for idx, name, host in out_devs:
            if prefer_name in name:
                return idx
        return out_devs[0][0] if out_devs else None

    def _callback(self, indata, outdata, frames, time, status):
        if status:
            try:
                self.q_status.put_nowait(str(status))
            except queue.Full:
                pass
        x = indata[:, 0].astype(np.float32, copy=False)
        with self.lock:
            y = process_block(x, self.state)
        outdata.fill(0.0)
        outdata[:, 0] = y

    def start(self, indev, outdev=None, sr=48000, blocksize=512):
        if self.running:
            return
        if outdev is None:
            outdev = self.find_output_index()
        self.current_sr = sr
        self.blocksize = blocksize
        self.indev = indev
        self.outdev = outdev
        self.state = DSPState(sr)
        self.stream = sd.Stream(
            samplerate=sr,
            blocksize=blocksize,
            dtype="float32",
            channels=1,
            device=(indev, outdev),
            callback=self._callback,
        )
        self.stream.start()
        self.running = True

    def stop(self):
        if self.stream is not None:
            try:
                self.stream.stop()
                self.stream.close()
            finally:
                self.stream = None
        self.running = False
