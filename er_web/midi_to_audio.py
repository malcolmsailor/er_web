import io
import math
import numpy as np
from scipy import signal
import wave
import subprocess

import malsynth

from .midi_to_list import midi_to_list

SAMPLE_RATE = 44100

TYPE = 1
TRACK = 2
CHANNEL = 3
PITCH = 4
ONSET = 5
RELEASE = 6
VELOCITY = 7
OTHER = 8


def get_array(midi_list, sample_rate, final_release_dur=1):
    synths = {}
    synth_assignments = {}
    total_dur = midi_list[-1][RELEASE]
    if total_dur is None:
        assert midi_list[-1][TYPE] == "end_of_track"
        total_dur = midi_list[-1][ONSET]
    total_dur += final_release_dur

    t = np.linspace(
        0, total_dur, int(math.ceil(total_dur * sample_rate)), False
    )

    out = np.zeros_like(t)

    # synth = malsynth.FollowSquare(
    #     # sample_rate=sample_rate, attack=0.01, decay=0.2, sustain=0
    #     oscillators=[malsynth.Oscillator(), malsynth.Oscillator(detune=0.5)],
    #     sample_rate=sample_rate,
    #     attack=0.01,
    #     decay=0.25,
    #     sustain=0,
    # )

    for event in midi_list:
        if event[TYPE] == "program_change":
            program = event[OTHER]["program"]
            program %= len(malsynth.synths)  # TODO remove
            # synth_assignments[(event[TRACK], event[CHANNEL])] = synths[program]
            if program not in synths:
                synths[program] = malsynth.synths[program](sample_rate)
            synth_assignments[event[TRACK]] = synths[program]  # TODO remove

        if event[TYPE] != "note":
            continue
        # synth_assignments[(event[TRACK], event[CHANNEL])](
        synth_assignments[event[TRACK]](  # TODO remove
            t, out, event[PITCH], event[ONSET], event[RELEASE], event[VELOCITY]
        )
    # it seems that the output needs to be on a half-closed interval [0, 1)
    # (rather than [0, 1]), or there are clicks and pops in the output (from
    # overflow?). In fact we seem to need to give a generous buffer (e.g.,
    # when I used np.max(out) * 1.01, there were still artefacts.)
    out /= np.max(out) * 1.1

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


def convert_from_wav(outf, output_path):
    # output format will be determined by the extension of output_path
    p = subprocess.Popen(
        # "-y" to overwrite output files without asking
        ["ffmpeg", "-y", "-i", "-", output_path],
        stdin=subprocess.PIPE,
    )
    p.communicate(outf.getvalue())
    if p.returncode != 0:
        raise FfmpegError()


def midi_to_audio(midi_path, out_path):
    wav_file = io.BytesIO()
    # TODO rather than writing than re-opening mido object, just pass it
    # through directly
    midi_to_wav(midi_path, out_path=wav_file)
    convert_from_wav(wav_file, out_path)
    wav_file.close()


if __name__ == "__main__":
    MIDI_FILE = "/Users/Malcolm/Google Drive/python/efficient_rhythms/output_midi/effrhy355.mid"
    OUT_PATH = "read_midi.wav"
    outf = io.BytesIO()
    midi_to_wav(MIDI_FILE, out_path=outf)
    convert_from_wav(outf, OUT_PATH.replace(".wav", ".mp4"))
    outf.close()
