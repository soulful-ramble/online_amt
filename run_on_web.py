import os
from flask import Flask, render_template, jsonify
import pyaudio
from transcribe import load_model, OnlineTranscriber
from mic_stream import MicrophoneStream
from file_stream import FileStream
import numpy as np
from threading import Thread
import queue
import rtmidi

import logging
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)
app = Flask(__name__)
global Q
Q = queue.Queue()

global Q2
Q2 = queue.Queue()


@app.route('/test')
def test():
    # args = Args()
    # model = load_model(args)
    model = load_model('model-180000.pt')
    global Q2
    t1 = Thread(target=get_file_buffer_and_transcribe,
                name=get_file_buffer_and_transcribe, args=(model, Q2))
    t1.start()
    return render_template('test.html')


@app.route('/')
def home():
    # args = Args()
    # model = load_model(args)
    model = load_model('model-180000.pt')
    global Q
    t1 = Thread(target=get_buffer_and_transcribe,
                name=get_buffer_and_transcribe, args=(model, Q))
    t1.start()
    return render_template('home.html')


@app.route('/_amt', methods=['GET', 'POST'])
def amt():
    global Q
    onsets = []
    offsets = []
    while Q.qsize() > 0:
        rst = Q.get()
        onsets += rst[0]
        offsets += rst[1]
    if len(onsets) or len(offsets):
        print('onsets', 'offsets', onsets, offsets)
    return jsonify(on=onsets, off=offsets)


@app.route('/_amt2', methods=['GET', 'POST'])
def amt2():
    global Q2
    onsets = []
    offsets = []
    while Q2.qsize() > 0:
        rst = Q2.get()
        onsets += rst[0]
        offsets += rst[1]
    if len(onsets) or len(offsets):
        print('onsets', 'offsets', onsets, offsets)
    return jsonify(on=onsets, off=offsets)


def get_file_buffer_and_transcribe(model, q):
    path = os.path.join(os.getcwd(), 'twinkle_twinkle_16k.wav')

    CHUNK = 512
    RATE = 16000

    # CHUNK = 2048
    # RATE = 44100
    CHANNELS = 1

    midiout = rtmidi.MidiOut()
    available_ports = midiout.get_ports()
    if available_ports:
        midiout.open_port(0)
    else:
        midiout.open_virtual_port("My virtual output")

    transcriber = OnlineTranscriber(model, return_roll=False)
    with FileStream(RATE, CHUNK, 1, file_path=path) as stream:
        # with MicrophoneStream(RATE, CHUNK, CHANNELS) as stream:
        # audio_generator = stream.generator()
        print("* recording")
        on_pitch = []
        while True:
            data = stream._buff.get()
            # print("data.length", len(data))
            # Interpret a buffer as a 1-dimensional array.
            decoded = np.frombuffer(data, dtype=np.int16) / 32768

            # print("decoded", decoded)

            if CHANNELS > 1:
                decoded = decoded.reshape(-1, CHANNELS)
                decoded = np.mean(decoded, axis=1)

            frame_output = transcriber.inference(decoded)

            # if len(frame_output[0]) or len(frame_output[1]):
            #     print('frame_output', frame_output)

            on_pitch += frame_output[0]
            for pitch in frame_output[0]:
                note_on = [0x90, pitch + 21, 64]
                midiout.send_message(note_on)
            for pitch in frame_output[1]:
                note_off = [0x90, pitch + 21, 0]
                pitch_count = on_pitch.count(pitch)
                [midiout.send_message(note_off) for i in range(pitch_count)]
            on_pitch = [x for x in on_pitch if x not in frame_output[1]]
            q.put(frame_output)
            # print(sum(frame_output))
        stream.closed = True
    print("* done recording")


def get_buffer_and_transcribe(model, q):
    CHUNK = 512
    FORMAT = pyaudio.paInt16

    CHANNELS = pyaudio.PyAudio().get_default_input_device_info()[
        'maxInputChannels']

    print("channels", CHANNELS)

    RATE = 16000

    midiout = rtmidi.MidiOut()
    available_ports = midiout.get_ports()
    if available_ports:
        midiout.open_port(0)
    else:
        midiout.open_virtual_port("My virtual output")

    stream = MicrophoneStream(RATE, CHUNK, CHANNELS)
    transcriber = OnlineTranscriber(model, return_roll=False)
    with MicrophoneStream(RATE, CHUNK, CHANNELS) as stream:
        audio_generator = stream.generator()
        print("* recording")
        on_pitch = []
        while True:
            data = stream._buff.get()
            # Interpret a buffer as a 1-dimensional array.
            decoded = np.frombuffer(data, dtype=np.int16) / 32768

            # print("decoded", decoded)

            # 【gpt】这段代码的目的是处理多通道音频数据。如果输入的音频数据是多通道的（CHANNELS > 1），
            # 则将其重新整形为一个二维数组，其中每一行表示一个通道的音频数据。
            # 然后，通过计算每一行的平均值，将多通道音频数据转换为单通道音频数据。
            # 这样做的目的是为了简化后续的音频处理和分析操作，使其能够适用于单通道音频数据的处理方法。
            if CHANNELS > 1:
                decoded = decoded.reshape(-1, CHANNELS)
                decoded = np.mean(decoded, axis=1)

            frame_output = transcriber.inference(decoded)

            # print('frame_output', frame_output)
            on_pitch += frame_output[0]
            for pitch in frame_output[0]:
                note_on = [0x90, pitch + 21, 64]
                midiout.send_message(note_on)
            for pitch in frame_output[1]:
                note_off = [0x90, pitch + 21, 0]
                pitch_count = on_pitch.count(pitch)
                [midiout.send_message(note_off) for i in range(pitch_count)]
            on_pitch = [x for x in on_pitch if x not in frame_output[1]]
            q.put(frame_output)
            # print(sum(frame_output))
        stream.closed = True
    print("* done recording")


@app.route('/parse_file_midi', methods=["post"])
def parse_file_midi():
    pass


if __name__ == '__main__':
    # for i in range(0, p.get_device_count()):
    #     print(i, p.get_device_info_by_index(i)['name'])
    app.run(host='0.0.0.0', port=5002, debug=True)
