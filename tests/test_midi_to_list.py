import os
import sys
import tempfile
import traceback
import mido

sys.path.insert(
    0, os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
)

import er_web.midi_to_list as midi_to_list


def test_tempi():
    mf = mido.MidiFile()
    track = mido.MidiTrack()
    mf.tracks.append(track)
    mf.ticks_per_beat = 4  # artificially low to make the math easy :)

    # 2-tuples are (tempo, time) for set_tempo messages
    # 3-tuples are (note, time, release) for note on/off pairs
    msgs = [
        (120, 0),
        (60, 0, 4),
        (61, 2, 2),
        (60, 0),
        (62, 0, 4),
        (63, 2, 2),
    ]
    start_and_end_times = [
        (0, 0.5),
        (0.75, 1.0),
        (1.0, 2.0),
        (2.5, 3.0),
    ]
    for msg in msgs:
        if len(msg) == 2:
            tempo, time = msg
            track.append(
                mido.MetaMessage(
                    "set_tempo", tempo=mido.bpm2tempo(tempo), time=time
                )
            )
        else:
            note, time, release = msg
            track.append(mido.Message("note_on", note=note, time=time))
            track.append(mido.Message("note_off", note=note, time=release))

    _, f_path = tempfile.mkstemp(suffix=".mid", prefix="er_web_test_tempi")
    mf.save(f_path)
    out = midi_to_list.midi_to_list(f_path)
    os.remove(f_path)
    for note, (start, end) in zip(
        (msg for msg in out if msg[1] == "note"), start_and_end_times
    ):
        assert note[5] == start and note[6] == end


def test_sort():
    mf = mido.MidiFile()
    track = mido.MidiTrack()
    mf.tracks.append(track)
    msg_attrs = [
        ("note_on", {"time": 0, "note": 60}),
        ("pitchwheel", {"time": 0, "pitch": 1000}),
        ("note_on", {"time": 4, "note": 60}),
        ("note_off", {"time": 0, "note": 60}),
        ("note_off", {"time": 4, "note": 60}),
    ]
    out_indices = [1, 0, 3, 2, 4]
    in_msgs = [
        mido.Message(msg_type, **kwargs) for msg_type, kwargs in msg_attrs
    ]
    for msg in in_msgs:
        track.append(msg)
    out_msgs = midi_to_list.compile_msgs(mf)
    try:
        for in_i, out_i in enumerate(out_indices):
            assert in_msgs[in_i] is out_msgs[out_i]
    except:  # pylint: disable=bare-except

        exc_type, exc_value, exc_traceback = sys.exc_info()
        traceback.print_exception(
            exc_type, exc_value, exc_traceback, file=sys.stdout
        )
        breakpoint()


# def test_read():
#     midi_list = midi_to_list.midi_to_list(
#         os.path.join(os.path.dirname((os.path.realpath(__file__))), "test2.mid")
#     )
#     num_voices = 3
#     for i in range(num_voices):
#         print(f"VOICE {i}")
#         for msg in midi_list:
#             if msg[2] == i:
#                 print(msg)
#         print("\n\n")


if __name__ == "__main__":
    test_tempi()
    test_sort()
    # test_read()
