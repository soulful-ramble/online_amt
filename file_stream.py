import os
import pyaudio
import queue
import time
import numpy as np
import wave


CHUNK = 2048
RATE = 44100

# pyaudio
# https://people.csail.mit.edu/hubert/pyaudio/docs/#id4

# this code is from https://blog.naver.com/chandong83/221149828690


class FileStream(object):
    def __init__(self, rate, chunk, channels, file_path: str):
        self._rate = rate
        self._chunk = chunk
        self._channels = channels
        self._file_path = file_path

        self._buff = queue.Queue()
        self.closed = True

    def __enter__(self):
        self._audio_interface = pyaudio.PyAudio()

        print("path", self._file_path)

        with wave.open(self._file_path, 'rb') as wf:

            # self._audio_stream = self._audio_interface.open(
            #     format=pyaudio.paInt16,
            #     channels=self._channels, rate=self._rate,
            #     input=True, frames_per_buffer=self._chunk,
            #     stream_callback=self._fill_buffer,
            # )

            # Define callback for playback (1)
            # def callback(in_data, frame_count, time_info, status):

            #     self._buff.put(in_data)

            #     data = wf.readframes(frame_count)
            #     # If len(data) is less than requested frame_count, PyAudio automatically
            #     # assumes the stream is finished, and the stream stops.
            #     return (data, pyaudio.paContinue)

            print('wave info: ',  wf.getsampwidth(),
                  wf.getnchannels(), wf.getframerate(), self._chunk)

            def callback(in_data, frame_count, time_info, status):
                data = wf.readframes(frame_count)
                print('data', type(data))
                print('callback params', frame_count, time_info, status)
                self._buff.put(data)
                # If len(data) is less than requested frame_count, PyAudio automatically
                # assumes the stream is finished, and the stream stops.
                return (data, pyaudio.paContinue)

            print("format", self._audio_interface.get_format_from_width(
                wf.getsampwidth()  # 必须是2 也就是样本位数必须是16, wave不支持32位
            ))
            print("format...", pyaudio.paInt16)

            self._audio_stream = self._audio_interface.open(
                format=self._audio_interface.get_format_from_width(
                    wf.getsampwidth()  # 必须是2 也就是样本位数必须是16, wave不支持32位
                ),
                channels=wf.getnchannels(),
                rate=wf.getframerate(),
                output=True,
                frames_per_buffer=self._chunk,
                stream_callback=callback,
            )

            self._audio_stream.start_stream()

            while self._audio_stream.is_active():
                time.sleep(0.1)
            # Play samples from the wave file (3)
            # while True:
            #     data = wf.readframes(self._chunk)
            #     # print('data(buffer) type', type(data))
            #     # data(buffer) type <class 'bytes'>
            #     self._buff.put(data)

            # self._audio_stream.close()

        self.closed = False

        return self

    # def __exit__(self, type, value, traceback):
    #     self._audio_stream.stop_stream()
    #     self._audio_stream.close()

    #     self.closed = True
    #     self._buff.put(None)
    #     self._audio_interface.terminate()

    def __exit__(self, type, value, traceback):
        self._audio_stream.stop_stream()
        self._audio_stream.close()

        self.closed = True
        print("exit.......")
        self._buff.put(None)
        self._audio_interface.terminate()

    def _fill_buffer(self, in_data, frame_count, time_info, status_flags):
        # print('in_data(buffer) type', type(in_data))
        # in_data(buffer) type <class 'bytes'>
        print('_fill_buffer', in_data)
        self._buff.put(in_data)
        return None, pyaudio.paContinue

    def generator(self):
        while not self.closed:
            chunk = self._buff.get()
            if chunk is None:
                return
            data = [chunk]
            while True:
                try:
                    chunk = self._buff.get(block=False)
                    if chunk is None:
                        return
                    data.append(chunk)
                except queue.Empty:
                    break

            yield b''.join(data)


def main():
    # 마이크 열기
    path = os.path.join(os.getcwd(), 'twinkle_twinkle_mono.wav')
    with FileStream(RATE, CHUNK, 1, file_path=path) as stream:
        for i in range(1000):
            data = stream._buff.get()
            # print('data', data, type(data))
            decoded = np.frombuffer(data, dtype=np.int16) / 32768
            print(stream._buff.qsize(), decoded[0:5])
            # for x in audio_generator:
            #     # 마이크 음성 데이터
            #     print(x)


if __name__ == '__main__':
    main()
