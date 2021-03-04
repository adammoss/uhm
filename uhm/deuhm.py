from __future__ import division

import math
import os
import sys
import argparse
import tempfile
import collections
import json

import librosa
import librosa.display
import numpy as np
from ibm_watson import SpeechToTextV1
from ibm_cloud_sdk_core.authenticators import IAMAuthenticator
import soundfile as sf
import warnings
warnings.filterwarnings('ignore')


class DeUhm:

    def __init__(self, input_file, feedback=0, api_key=None, api_url=None):

        API_KEY = os.environ.get('WATSON_API_KEY', api_key)
        API_URL = os.environ.get('WATSON_API_URL', api_url)

        authenticator = IAMAuthenticator(API_KEY)
        self.service = SpeechToTextV1(authenticator=authenticator)
        self.service.set_service_url(API_URL)

        self.input_file = input_file
        self.feedback = feedback
        if self.feedback > 0:
            print('Reading audio from input file')
        self.y, self.sr = librosa.load(self.input_file)
        if self.feedback > 0:
            print('Finished reading audio')
        self.duration = math.ceil(len(self.y) / self.sr)

    def transcribe(self, chunk_duration=60, model='en-GB_BroadbandModel', max_duration=None):
        fillers = []
        if max_duration is not None:
            max_chunks = math.ceil(max_duration / chunk_duration)
            chunks = range(math.ceil(self.duration / chunk_duration))[0:max_chunks]
        else:
            chunks = range(math.ceil(self.duration / chunk_duration))
        filler_id = 1
        for chunk in chunks:
            offset = chunk_duration * chunk
            y, sr = librosa.load(self.input_file, duration=chunk_duration, offset=chunk_duration * chunk)
            temp = tempfile.NamedTemporaryFile(suffix=".flac")
            sf.write(temp, y, sr)
            result = self.service.recognize(
                audio=temp.read(),
                content_type='audio/flac',
                model=model,
                timestamps=True,
                word_confidence=True).get_result()
            temp.close()
            for res in result.get('results'):
                for alt in res.get('alternatives'):
                    timestamps = alt.get('timestamps')
                    word_confidence = alt.get('word_confidence')
                    if len(timestamps) == len(word_confidence):
                        for i in range(len(timestamps)):
                            if timestamps[i][0] == '%HESITATION' and word_confidence[i][0] == '%HESITATION':
                                filler = collections.OrderedDict([
                                    ('id', filler_id),
                                    ('start', offset + timestamps[i][1]),
                                    ('end', offset + timestamps[i][2]),
                                    ('confidence', word_confidence[i][1])
                                ])
                                if self.feedback > 0:
                                    print(json.dumps(filler, indent=1))
                                fillers.append(filler)
                                filler_id += 1
        return fillers

    def get_background(self, t_start, t_end):
        y, sr = librosa.load(self.input_file, duration=t_end - t_start, offset=t_start)
        D = librosa.stft(y)
        S_full, phase = librosa.magphase(D)
        S_filter = librosa.decompose.nn_filter(S_full,
                                               aggregate=np.median,
                                               metric='cosine',
                                               width=int(librosa.time_to_frames(2, sr=sr)))
        S_filter = np.minimum(S_full, S_filter)
        margin_i, margin_v = 2, 10
        power = 2
        mask_i = librosa.util.softmask(S_filter,
                                       margin_i * (S_full - S_filter),
                                       power=power)
        S_background = mask_i * S_full
        return librosa.griffinlim(S_background)

    def filler_audio(self, fillers, padding=0.5):
        return [librosa.load(self.input_file, duration=f['end'] - f['start'] + 2*padding,
                             offset=f['start'] - padding) for f in fillers]

    def valid_fillers(self, fillers, hesitation_threshold=0.1, exclude_filler_ids=[], exclude_times=[]):
        valid_fillers = []
        for filler in fillers:
            include = True
            for exclude_time in exclude_times:
                if filler['end'] >= exclude_time >= filler['start']:
                    include = False
            if include and filler['confidence'] > hesitation_threshold and filler['id'] not in exclude_filler_ids:
                valid_fillers.append(filler)
        return valid_fillers

    def new_audio(self, fillers, mode='mute'):
        y = np.copy(self.y)
        for filler in fillers:
            if mode == 'mute':
                y[int(filler['start'] * self.sr):int(filler['end'] * self.sr)] = 0
            elif mode == 'background':
                try:
                    y_background = self.get_background(filler['start'], filler['end'] + 5)
                except:
                    y_background = []
                if len(y_background) > int(filler['end'] * self.sr) - int(filler['start'] * self.sr):
                    y[int(filler['start'] * self.sr):int(filler['end'] * self.sr)] = \
                        y_background[0:int(filler['end'] * self.sr) - int(filler['start'] * self.sr)]
                else:
                    y[int(filler['start'] * self.sr):int(filler['end'] * self.sr)] = 0
        return y, self.sr

    def new_video(self, output_file, fillers, mode='cut'):
        try:
            os.remove(output_file)
        except OSError:
            pass
        if mode == 'cut':
            between = []
            start_time = 0
            for filler in fillers:
                between.append('between(t,%s,%s)' % (start_time, filler['start']))
                start_time = filler['end']
            between.append('between(t,%s,%s)' % (start_time, self.duration + 1))
            video_select = """"select='""" + '+'.join(between) + '''\', setpts=N/FRAME_RATE/TB\"'''
            audio_select = """"aselect='""" + '+'.join(between) + '''\', asetpts=N/SR/TB\"'''
            os.system('ffmpeg -i %s -vf %s -af %s %s' % (self.input_file, video_select, audio_select, output_file))
        else:
            temp = tempfile.NamedTemporaryFile(suffix=".flac")
            y, sr = self.new_audio(fillers, mode=mode)
            sf.write(temp, y, sr)
            os.system('ffmpeg -i %s -i %s -c:v copy -map 0:v:0 -map 1:a:0 %s' % (self.input_file, temp.name, output_file))
            temp.close()


def run():
    parser = argparse.ArgumentParser()

    parser.add_argument('input', type=str)
    parser.add_argument('output', type=str)
    parser.add_argument('--model', type=str, default='en-GB_BroadbandModel')
    parser.add_argument('--hesitation_threshold', type=float, default=0.1)
    parser.add_argument('--chunk_duration', type=int, default=60)
    parser.add_argument('--feedback', type=int, default=1)
    parser.add_argument('--max_transcribe_duration', type=int, default=None)
    parser.add_argument('--exclude_times', nargs='+', default=[])
    parser.add_argument('--exclude_ids', nargs='+', default=[])
    parser.add_argument('-m', '--mode', type=str, default='cut')
    parser.add_argument('--api_key', type=str, default=None)
    parser.add_argument('--api_url', type=str, default=None)

    args = parser.parse_args()

    exclude_ids = [int(exclude_id) for exclude_id in args.exclude_ids]
    exclude_times = [float(exclude_time) for exclude_time in args.exclude_times]

    u = DeUhm(args.input, feedback=args.feedback, api_key=args.api_key, api_url=args.api_url)
    fillers = u.transcribe(chunk_duration=args.chunk_duration, model=args.model,
                           max_duration=args.max_transcribe_duration)
    valid_fillers = u.valid_fillers(fillers, hesitation_threshold=args.hesitation_threshold,
                                    exclude_times=exclude_times, exclude_filler_ids=exclude_ids)
    u.new_video(args.output, valid_fillers, mode=args.mode)


if __name__ == '__main__':
    run()
