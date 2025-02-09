import wave
import numpy as np
import os
from pydub import AudioSegment


def chunk_wav(wav_path, emotions, persist_chunk = False, chunk_dest = None, emo_count = None):
    if emo_count is None:
        emo_count = {}

    audio_file = AudioSegment.from_wav(wav_path)

    for ie, e in enumerate(emotions):
        start = e['start'] * 1000
        end = e['end'] * 1000

        emotion = e['emotion']
        if persist_chunk:
            counter = emo_count.get(emotion)
            if counter is None:
                counter = 1
            else:
                counter += 1
            emo_count[emotion] = counter

            filename = emotion + '_' + str(counter) + '.wav'
            chunk_path = os.path.join(chunk_dest, filename)

            chunk = audio_file[start: end]
            chunk.export(chunk_path, format = 'wav')

    return emo_count


def split_wav(wav, emotions, persist_chunk = False, chunk_dest = None, emo_count = None):
    if emo_count is None:
        emo_count = {}
    (nchannels, sampwidth, framerate, nframes, comptype, compname), samples = wav

    left = samples[0::nchannels]
    right = samples[1::nchannels]

    frames = []
    for ie, e in enumerate(emotions):
        start = e['start']
        end = e['end']

        e['right'] = right[int(start * framerate):int(end * framerate)]
        e['left'] = left[int(start * framerate):int(end * framerate)]

        frames.append({'left': e['left'], 'right': e['right']})

        emotion = e['emotion']
        if persist_chunk:
            counter = emo_count.get(emotion)
            if counter is None:
                counter = 1
            else:
                counter += 1
            emo_count[emotion] = counter

            filename = emotion + '_' + str(counter) + '.wav'
            print(os.path.join(chunk_dest, filename))

            chunk = wave.open(filename, 'wb')
            nframes_chunk = len(e['right'])
            chunk.setparams((nchannels, sampwidth, framerate, nframes_chunk, comptype, compname))
            chunk.writeframesraw(e['left'])
            chunk.writeframesraw(e['right'])
            chunk.close()

    return frames, emo_count


def get_field(data, key):
    return np.array([e[key] for e in data])


def pad_sequence_into_array(Xs, maxlen = None, truncating = 'post', padding = 'post', value = 0.):
    Nsamples = len(Xs)
    if maxlen is None:
        lengths = [s.shape[0] for s in Xs]  # 'sequences' must be list, 's' must be numpy array, len(s) return the first dimension of s
        maxlen = np.max(lengths)

    Xout = np.ones(shape = [Nsamples, maxlen] + list(Xs[0].shape[1:]), dtype = Xs[0].dtype) * np.asarray(value, dtype = Xs[0].dtype)
    Mask = np.zeros(shape = [Nsamples, maxlen], dtype = Xout.dtype)
    for i in range(Nsamples):
        x = Xs[i]
        if truncating == 'pre':
            trunc = x[-maxlen:]
        elif truncating == 'post':
            trunc = x[:maxlen]
        else:
            raise ValueError("Truncating type '%s' not understood" % truncating)
        if padding == 'post':
            Xout[i, :len(trunc)] = trunc
            Mask[i, :len(trunc)] = 1
        elif padding == 'pre':
            Xout[i, -len(trunc):] = trunc
            Mask[i, -len(trunc):] = 1
        else:
            raise ValueError("Padding type '%s' not understood" % padding)
    return Xout, Mask


def convert_gt_from_array_to_list(gt_batch, gt_batch_mask = None):
    B, L = gt_batch.shape
    gt_batch = gt_batch.astype('int')
    gts = []
    for i in range(B):
        if gt_batch_mask is None:
            l = L
        else:
            l = int(gt_batch_mask[i, :].sum())
        gts.append(gt_batch[i, :l].tolist())
    return gts


def get_audio(path_to_wav, filename):
    file_path = os.path.join(path_to_wav, filename)
    wav = wave.open(file_path, mode = "r")
    (nchannels, sampwidth, framerate, nframes, comptype, compname) = wav.getparams()
    content = wav.readframes(nframes)
    samples = np.fromstring(content, dtype = np.int16)
    return (nchannels, sampwidth, framerate, nframes, comptype, compname), samples


def get_transcriptions(path_to_transcriptions, filename):
    f = open(path_to_transcriptions + filename, 'r').read()
    f = np.array(f.split('\n'))
    transcription = {}
    for i in range(len(f) - 1):
        g = f[i]
        i1 = g.find(': ')
        i0 = g.find(' [')
        ind_id = g[:i0]
        ind_ts = g[i1 + 2:]
        transcription[ind_id] = ind_ts
    return transcription


def get_emotions(path_to_emotions, filename):
    file_path = os.path.join(path_to_emotions, filename)
    f = open(file_path, 'r').read()
    f = np.array(f.split('\n'))
    idx = f == ''
    idx_n = np.arange(len(f))[idx]
    emotion = []
    for i in range(len(idx_n) - 2):
        g = f[idx_n[i] + 1:idx_n[i + 1]]
        head = g[0]
        i0 = head.find(' - ')
        start_time = float(head[head.find('[') + 1:head.find(' - ')])
        end_time = float(head[head.find(' - ') + 3:head.find(']')])
        actor_id = head[head.find(filename[:-4]) + len(filename[:-4]) + 1:
                        head.find(filename[:-4]) + len(filename[:-4]) + 5]
        emo = head[head.find('\t[') - 3:head.find('\t[')]
        vad = head[head.find('\t[') + 1:]

        v = float(vad[1:7])
        a = float(vad[9:15])
        d = float(vad[17:23])

        j = 1
        emos = []
        while g[j][0] == "C":
            head = g[j]
            start_idx = head.find("\t") + 1
            evoluator_emo = []
            idx = head.find(";", start_idx)
            while idx != -1:
                evoluator_emo.append(head[start_idx:idx].strip().lower()[:3])
                start_idx = idx + 1
                idx = head.find(";", start_idx)
            emos.append(evoluator_emo)
            j += 1

        emotion.append({'start': start_time,
            'end': end_time,
            'id': filename[:-4] + '_' + actor_id,
            'v': v,
            'a': a,
            'd': d,
            'emotion': emo,
            'emo_evo': emos})
    return emotion
