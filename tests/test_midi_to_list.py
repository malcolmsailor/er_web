import os
import sys
import tempfile
import traceback
import mido

sys.path.insert(
    0, os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
)

import er_web.midi_to_list as midi_to_list


def _init_mf(n_tracks):
    mf = mido.MidiFile()
    for _ in range(n_tracks):
        track = mido.MidiTrack()
        mf.tracks.append(track)
    return mf


def _save_mf_and_get_list(mf):
    _, f_path = tempfile.mkstemp(suffix=".mid", prefix="er_web_test_tempi")
    mf.save(f_path)
    out = midi_to_list.midi_to_list(f_path)
    os.remove(f_path)
    return out


def test_pitchbend():
    mf = _init_mf(2)
    mf.ticks_per_beat = 1
    # 4-tuples are (track, channel, time, pitch) for pitchwheel msgs
    # 5-tuples are (track, channel, time, note, release) for note on/off pairs
    msgs = [
        (0, 0, 0, 2048),
        (0, 0, 0, 60, 2),
        (0, 1, 0, 1024),
        (0, 1, 0, 64, 4),
        (1, 0, 0, 67, 2),
        (0, 0, 2, 1024),
        (0, 0, 2, 62, 4),
        (1, 0, 2, 2048),
        (1, 0, 2, 67, 4),
    ]
    # Track 0, channel 0: 60.5 then 62.25
    # Track 0, channel 1: 64.25
    # Track 1, channel 1: 67, then 67.5
    expected_notes = [
        (0, 0, 60.5, 0, 1),
        (0, 1, 64.25, 0, 2),
        (1, 0, 67, 0, 1),
        (0, 0, 62.25, 1, 2),
        (1, 0, 67.5, 1, 2),
    ]
    for msg in msgs:
        if len(msg) == 4:
            track, channel, time, pitch = msg
            mf.tracks[track].append(
                mido.Message(
                    "pitchwheel", channel=channel, time=time, pitch=pitch
                )
            )
        else:
            track, channel, time, note, release = msg
            mf.tracks[track].append(
                mido.Message("note_on", note=note, time=time, channel=channel)
            )
            mf.tracks[track].append(
                mido.Message(
                    "note_off", note=note, time=release, channel=channel
                )
            )

    # convert to relative times
    for track in mf.tracks:
        track.sort(key=lambda x: x.time)
        time = 0
        for msg in track:
            delta = msg.time - time
            time = msg.time
            msg.time = delta

    out = _save_mf_and_get_list(mf)
    for item in out:
        if not item[1] == "note":
            continue
        tup = track, channel, pitch, onset, release = item[2:7]
        assert tup in expected_notes
        expected_notes.remove(tup)
    assert not expected_notes


def test_tempi():
    mf = _init_mf(1)
    track = mf.tracks[0]
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

    # _, f_path = tempfile.mkstemp(suffix=".mid", prefix="er_web_test_tempi")
    # mf.save(f_path)
    # out = midi_to_list.midi_to_list(f_path)
    # os.remove(f_path)
    out = _save_mf_and_get_list(mf)
    for note, (start, end) in zip(
        (msg for msg in out if msg[1] == "note"), start_and_end_times
    ):
        assert note[5] == start and note[6] == end


def test_sort():
    mf = _init_mf(1)
    track = mf.tracks[0]
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
