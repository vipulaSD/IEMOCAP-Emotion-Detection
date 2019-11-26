import os
from helper import *

data_path = "C:\\academic-data\\iemocap"
sessions = ['Session1', 'Session2', 'Session3', 'Session4', 'Session5']

framerate = 16000


def chunk_utterances():
    for session in sessions:
        path_to_wav = os.path.join(data_path, session, 'dialog', 'wav')
        path_to_emotions = os.path.join(data_path, session, 'dialog', 'EmoEvaluation')
        chunk_dest = os.path.join(data_path, 'chunks', session)
        print(path_to_wav)

        if not os.path.exists(chunk_dest):
            os.makedirs(chunk_dest)

        files2 = os.listdir(path_to_wav)

        files = []
        for f in files2:
            if f.endswith(".wav"):
                if f[0] == '.':
                    files.append(f[2:-4])
                else:
                    files.append(f[:-4])

        emo_count = {}
        for f in files:
            print(f)

            wav_path = os.path.join(path_to_wav, f + '.wav')
            emotions = get_emotions(path_to_emotions, f + '.txt')
            emo_count = chunk_wav(wav_path, emotions, persist_chunk = True, chunk_dest = chunk_dest, emo_count = emo_count)


if __name__ == '__main__':
    chunk_utterances()
