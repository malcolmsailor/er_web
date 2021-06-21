import collections
import functools
import fractions
import os
import warnings

import mido

NUM_CHANNELS = 16
DEFAULT_MIDI_TEMPO = 500_000  # 120 bpm

# For pitchbend
# for EastWest, SIZE_OF_SEMITONE should be 4096
# for Vienna, SIZE_OF_SEMITONE should be 8192
SIZE_OF_SEMITONE = 4096


def add_track_and_abs_time(track, track_i):
    tick_time = 0
    for msg in track:
        tick_time += msg.time
        # NB Mido docs say it is preferred to treat messages as immutable
        #   but I don't see the advantage in creating a bunch of copies
        #   here.
        msg.time = tick_time
        # Moreover, the mido.Message class has overwritten setattr to
        #   fail for arbitrary attribute names. So the following hack
        #   becomes necessary.
        # object.__setattr__(msg, "abs_time", tick_time)
        object.__setattr__(msg, "track", track_i)
        yield msg


def compile_msgs(in_mid):
    """For various reasons, mido's built-in iteration over midi files won't work
    here. (E.g., it does not include track numbers, and it does not allow
    setting arbitrary message attributes [it runs checks to enforce that all
    msg attributes conform to its API], nor can we modify messages during
    iteration (because it returns copies of all msgs).) So instead, we build
    a list and return it here.
    """
    out = []
    for track_i, track in enumerate(in_mid.tracks):
        out.extend(add_track_and_abs_time(track, track_i))

    def _sorter_string(msg):
        # We want to put pitchwheel events before any note events that occur
        # simultaneously
        if msg.type == "pitchwheel":
            return "aaaa"
        return msg.type

    # tracks should already be in order so we don't need to sort on these
    out.sort(key=_sorter_string)
    out.sort(key=lambda msg: msg.time)
    return out


def _event(
    type_,
    track=None,
    channel=None,
    pitch=None,
    onset=None,
    release=None,
    velocity=None,
    other=None,
    midi_basename=None,
):
    return (
        midi_basename,
        type_,
        track,
        channel,
        pitch,
        onset,
        release,
        velocity,
        other,
    )


def _pitch_bend_handler(pb_dict, msg, size_of_semitone=SIZE_OF_SEMITONE):
    pb_dict[msg.track][msg.channel] = msg.pitch / size_of_semitone


def _note_off_handler(
    msg, release, note_on_dict=None, overlapping_notes=None, event=None
):
    midinum = msg.note
    out = []
    while True:
        try:
            note_on_msg, pitch, onset = note_on_dict[msg.track][msg.channel][
                midinum
            ].pop(0 if overlapping_notes == "end_first" else -1)
        except IndexError:
            if out:
                return out
            warnings.warn(
                f"note_off event with pitch {msg.note} at "
                f"time {release} "
                f"on track {msg.track}, "
                f"channel {msg.channel}, but no note_on event still sounding"
            )
            return None

        out.append(
            event(
                type_="note",
                track=msg.track,
                channel=msg.channel,
                pitch=pitch,
                onset=onset,
                release=release,
                velocity=note_on_msg.velocity,
            )
        )
        if overlapping_notes != "end_all":
            return out


def _note_on_handler(
    msg, time, note_on_dict=None, pb_dict=None, inv_pb_tup_dict=None
):
    if pb_dict is None:
        # msg.note as key is a midinumber (0-127)
        # msg.note as second item of tuple is a pitch number (which depends
        #   in principle on the temperament)
        note_on_dict[msg.track][msg.channel][msg.note].append(
            (msg, msg.note, time)
        )
        return
    pitch_bend = (
        0 if msg.channel not in pb_dict else pb_dict[msg.track][msg.channel]
    )
    # TODO document that an error will be raised if this is not found
    # pitch = inv_pb_tup_dict[(msg.note, pitch_bend)]
    pitch = msg.note + pitch_bend
    note_on_dict[msg.track][msg.channel][msg.note].append((msg, pitch, time))


def _other_msg_handler(msg, time, event=None):
    other = vars(msg)
    type_ = other.pop("type")
    try:
        channel = other.pop("channel")
    except KeyError:
        channel = None
    return event(
        type_=type_,
        track=msg.track,
        channel=channel,
        onset=time,
        other=other,
    )


def midi_to_list(
    in_midi_fname,
    header=False,
    overlapping_notes="end_all",
    pb_tup_dict=None,
):
    """Read a midi file and return a list of events.

    Note-on and note-off events will be compiled into a single event with
    attack and release.

    description

    Args:
        in_midi_fname: path to input midi file.

    Keyword args:
        overlapping_notes: string. Defines what happens when more than one
        note-on event on the same pitch occurs on the same track and channel,
        with no intervening note-off event. Ideally there should not be any such
        events, but that cannot be guaranteed for arbitrary input. To illustrate
        the effect of the possible values, imagine there is a midi file with
        note-on events at time 0 and time 1, and note-off events at time 2 and
        time 3, with all events having the same pitch (e.g., midi number 60).
            Possible values:
                "end_all" (default): a note-off event ends *all* sounding
                    note-on events with the same track and channel and pitch.
                    Thus in the example there would be two notes:
                        - onset 0, release 2
                        - onset 1, release 2
                    There would be an "orphan" note-off event at time 3, which
                    will emit a warning.
                    This setting corresponds most closely to how midi playback
                    ordinarily behaves.
                "end_first": a note-off event ends the *first* sounding note-on
                    event with the same track and channel and pitch. Thus the
                    example would produce the following two notes:
                        - onset 0, release 2
                        - onset 1, release 3
                "end_last": a note-off event ends the *last* sounding note-on
                    event with the same track and channel and pitch. Thus the
                    example would produce the following two notes:
                        - onset 0, release 3
                        - onset 1, release 2
        pb_tup_dict: dictionary. TODO document.


    Returns: a list of 9-tuple "events", either
        - non-note midi messages, or
        - note events, i.e., the combination of a note-on with the following
            note-off event.
        The fields of the tuples are:
            (
                "filename",
                "type",
                "track",
                "channel",
                "pitch",
                "onset",
                "release",
                "velocity",
                "other",
            )
        The list is suitable for writing to a csv file.
        - pitch, velocity, and duration (or release?) are null for non-note
            events; channel is null for events that do not have a channel attribute;
            all other fields go into "other" as a dict.
        Tracks and channels are zero-indexed.

        Simultaneous note-on and note-off events on the same pitch will be
        interpreted as a note off *followed* by a note on event. (I.e., we
        understand repeated notes on the same pitch (and expect a preceding
        note-on and a following note-off), rather than a note with zero length)

        Output will be sorted as follows:
            - by onset
            - then by track number, from highest to lowest (the logic of this
                order being that we expect bass voice to be last)
            - then by pitch, from highest to lowest
            - then by time of release
        Except for the last criterion (which is unlikely to apply and indeed
        can only apply if overlapping_notes has a value other than "end_all"),
        these are taken from Andie's script.

    Raises:
        exceptions
    """

    # TODO flag to filter what kind of events are returned?
    # TODO flag to control behavior when sustain pedal is depressed
    midi_basename = os.path.basename(in_midi_fname)

    # Sorting the tracks avoids orphan note or pitchwheel events.
    in_mid = mido.MidiFile(in_midi_fname)
    num_tracks = len(in_mid.tracks)
    tpb = in_mid.ticks_per_beat
    msgs = compile_msgs(in_mid)

    out = []

    note_on_dict = {
        i: {j: collections.defaultdict(list) for j in range(NUM_CHANNELS)}
        for i in range(num_tracks)
    }

    if pb_tup_dict is not None:
        pb_dict = {
            i: {j: {} for j in range(NUM_CHANNELS)} for i in range(num_tracks)
        }
        inv_pb_tup_dict = {v: k for k, v in pb_tup_dict.items()}
    else:
        pb_dict = {
            i: {j: 0 for j in range(NUM_CHANNELS)} for i in range(num_tracks)
        }
        inv_pb_tup_dict = None

    # partial function bindings
    event = functools.partial(_event, midi_basename=midi_basename)
    pb_handler = functools.partial(_pitch_bend_handler, pb_dict)
    note_off_handler = functools.partial(
        _note_off_handler,
        note_on_dict=note_on_dict,
        overlapping_notes=overlapping_notes,
        event=event,
    )
    note_on_handler = functools.partial(
        _note_on_handler,
        note_on_dict=note_on_dict,
        pb_dict=pb_dict,
        inv_pb_tup_dict=inv_pb_tup_dict,
    )
    other_msg_handler = functools.partial(
        _other_msg_handler,
        event=event,
    )
    tempo = DEFAULT_MIDI_TEMPO
    tick_time = 0
    time = 0

    for msg in msgs:
        tick_delta = msg.time - tick_time
        tick_time = msg.time
        time += mido.tick2second(tick_delta, tpb, tempo)
        if msg.type == "pitchwheel":
            pb_handler(msg)
        elif msg.type == "note_off" or (
            msg.type == "note_on" and msg.velocity == 0
        ):
            notes = note_off_handler(msg, time)
            if notes:
                out.extend(notes)
        elif msg.type == "note_on":
            note_on_handler(msg, time)
        else:
            out.append(other_msg_handler(msg, time))

        try:
            tempo = msg.tempo
        except AttributeError:
            pass

    for track_i, track in note_on_dict.items():
        for channel_i, channel in track.items():
            try:
                assert not channel
            except AssertionError:
                for pitch, note_ons in channel.items():
                    try:
                        assert not note_ons
                    except AssertionError:
                        warnings.warn(
                            f"Pitch {pitch} is still on (no note-off event on "
                            f"track {track_i}, channel {channel_i} before end)"
                        )
    # release_i = 6
    # only non-note events have release = None, put them first
    out.sort(key=lambda x: 0 if x[6] is None else x[6])
    # pitch_i = 4
    out.sort(key=lambda x: 128 if x[4] is None else x[4], reverse=True)
    # track_i = 2
    out.sort(key=lambda x: x[2], reverse=True)
    # onset_i = 5
    out.sort(key=lambda x: x[5])
    if header:
        out.insert(
            0,
            (
                "filename",
                "type",
                "track",
                "channel",
                "pitch",
                "onset",
                "release",
                "velocity",
                "other",
            ),
        )
    return out
