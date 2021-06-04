import io
import math
import numpy as np
import wave
import subprocess

from .midi_to_list import midi_to_list

SAMPLE_RATE = 44100

TYPE = 1
PITCH = 4
ONSET = 5
RELEASE = 6
VELOCITY = 7


def pitch_to_hz(pitch):
    return 440.0 * (2 ** ((pitch - 69) / 12.0))


def get_array(midi_list, sample_rate, onset_dur=0.005, release_dur=0.005):
    # onset and release envelopes eliminate "clicking" when sine waves
    # come immediately on/off
    onset_dur = int(sample_rate * onset_dur)
    onset_envelope = np.linspace(0, 1, onset_dur)
    release_dur = int(sample_rate * release_dur)
    release_envelope = np.linspace(1, 0, release_dur)

    total_dur = midi_list[-1][RELEASE]
    if total_dur is None:
        assert midi_list[-1][TYPE] == "end_of_track"
        total_dur = midi_list[-1][ONSET]

    t = np.linspace(
        0, total_dur, int(math.ceil(total_dur) * sample_rate), False
    )
    out = np.zeros_like(t)

    const_factor = 2 * np.pi

    for event in midi_list:
        if event[TYPE] != "note":
            continue
        start_i = np.searchsorted(t, event[ONSET])
        end_i = np.searchsorted(t, event[RELEASE])
        note = np.sin(
            t[start_i:end_i] * pitch_to_hz(event[PITCH]) * const_factor
        ) * (event[VELOCITY] / 127)
        note[:onset_dur] *= onset_envelope
        note[-release_dur:] *= release_envelope
        out[start_i:end_i] += note

    out /= np.max(out)

    return out


def write_mono_wav(np_array, out_path_or_f, sample_rate):
    audio = (np_array * (2 ** 15 - 1)).astype("<h")
    with wave.open(out_path_or_f, "wb") as f:
        # 2 Channels.
        f.setnchannels(1)
        # 2 bytes per sample.
        f.setsampwidth(2)
        f.setframerate(sample_rate)
        f.writeframes(audio.tobytes())


def midi_to_wav(midi_path, sample_rate=SAMPLE_RATE, out_path=None):
    event_list = midi_to_list(midi_path)
    sample_array = get_array(event_list, sample_rate)
    write_mono_wav(sample_array, out_path, sample_rate)


class FfmpegError(Exception):
    pass


def wav_to_mp4(outf, output_path):
    p = subprocess.Popen(
        # "-y" to overwrite output files without asking
        ["ffmpeg", "-y", "-i", "-", output_path],
        stdin=subprocess.PIPE,
    )
    p.communicate(outf.getvalue())
    if p.returncode != 0:
        raise FfmpegError()


def midi_to_mp4(midi_path, mp4_path):
    f = io.BytesIO()
    # TODO rather than writing than re-opening mido object, just pass it
    # through directly
    midi_to_wav(midi_path, out_path=f)
    wav_to_mp4(f, mp4_path)
    f.close()


if __name__ == "__main__":
    MIDI_FILE = "/Users/Malcolm/Google Drive/python/efficient_rhythms/output_midi/effrhy355.mid"
    OUT_PATH = "read_midi.wav"
    # outf = "foo"
    outf = io.BytesIO()
    midi_to_wav(MIDI_FILE, out_path=outf)
    # midi_to_wav(MIDI_FILE, out_path=outf)
    # wav_to_mp4(OUT_PATH, OUT_PATH.replace(".wav", ".mp4"))
    wav_to_mp4(outf, OUT_PATH.replace(".wav", ".mp4"))
    outf.close()

    # l = midi_to_list(MIDI_FILE)
    # # for item in l:
    # #     print(item)
    # a = get_array(l, SAMPLE_RATE)
    # write_mono_wav(a, OUT_PATH, SAMPLE_RATE)
