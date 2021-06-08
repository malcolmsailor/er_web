import os
import sys
import tempfile
import subprocess
import traceback

sys.path.insert(
    0, os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
)

import er_web.midi_to_audio as midi_to_audio


def test_midi_to_wav():
    # For some reason, the midi file I am using has 10 tracks but only tracks
    # 3,5, and 7 have any note events!
    # (I should investigate why efficient_rhythms is making such weird output.)
    midi_path = os.path.join(
        os.path.dirname((os.path.realpath(__file__))), "test.mid"
    )
    _, wav_path = tempfile.mkstemp(suffix=".wav")
    midi_to_audio.midi_to_wav(midi_path, out_path=wav_path)
    print("ctrl-C to interrupt playback")
    try:
        while True:
            subprocess.run(["afplay", wav_path])
    except KeyboardInterrupt:
        print("")
    os.remove(wav_path)


if __name__ == "__main__":
    test_midi_to_wav()
