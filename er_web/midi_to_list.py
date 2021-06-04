import collections
import fractions
import os
import warnings

import mido

NUM_CHANNELS = 16

# TODO handle tempi!


def _convert_to_abs_time_and_sort(in_mid):
    def _sorter_string(msg):
        # We want to put pitchwheel events before any note events that occur
        # simultaneously
        if msg.type == "pitchwheel":
            return "aaaa"
        return msg.type

    for track in in_mid.tracks:
        tick_time = 0
        for msg in track:
            tick_time += msg.time
            # NB Mido docs say it is preferred to treat messages as immutable
            #   but I don't see the advantage in creating a bunch of copies
            #   here
            msg.time = tick_time
        # pitchwheel before note_off before note_on
        track.sort(key=_sorter_string)
        track.sort(key=lambda msg: msg.time)


def midi_to_list(
    in_midi_fname,
    # TODO I think I want to delete this flag since dicts aren't sortable
    output_type="tuple",
    header=False,
    time_type=float,
    max_denominator=8192,
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
        output_type: a string, either "dict" or "tuple". # TODO document further
        time_type: the numeric type that should be used to express time
            attributes. The default is `float`, but if preserving exact relative
            timings is important it may be better to use `fractions.Fraction`
            to avoid float rounding issues.
        max_denominator: integer. Only has an effect if `time_type` is
            `fractions.Fraction`, in which case this argument sets the
            maximum denominator.
            Default: 8192
        overlapping_notes: string. Defines what happens when more than one
            note-on event on the same pitch occurs on the same track and
            channel, with no intervening note-off event. Ideally there should
            not be any such events, but that cannot be guaranteed. To
            illustrate the effect of the possible values, imagine there is a
            midi file with note-on events at time 0 and time 1, and note-off
            events at time 2 and time 3, with all events having the same pitch
            (e.g., midi number 60).
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


    Returns: a list of "events".
        - non-note events are just midi messages
        - note events are the combination of a note-on with the following
            note-off event.
            # TODO what if two note-ons on same pitch are followed by a note-off?
        The list should be suitable for writing to a csv file.
        All events have onset, release (or duration?), channel, pitch, and velocity, and 'other' fields.
        - pitch, velocity, and duration (or release?) are null for non-note events; channel is null for
            events that do not have a channel attribute; all other fields go
            into "other" as some sort of string representation (TODO ?)
        Tracks and channels are zero-indexed.

        Simultaneous note-on and note-off events on the same pitch will be interpreted as a
        note off *followed* by a note on event. (I.e., we understand repeated
        notes on the same pitch (and expect a preceding note-on and a following note-off), rather than a note with zero length)

        Output will be sorted as follows:
            - by onset
            - then by track number, from highest to lowest (the logic of this
                order being that we expect bass voice to be last)
            - then by pitch, from highest to lowest
            - then by time of release
        Except for the last criterion (which is unlikely to apply and indeed
        can only apply if overlapping_notes has a value other than "end_all"), these
        are taken from Andie's script.

    Raises:
        exceptions
    """

    # TODO flag to filter what kind of events are returned?
    # TODO flag to control behavior when sustain pedal is depressed
    midi_basename = os.path.basename(in_midi_fname)

    def _event(
        type_,
        track=None,
        channel=None,
        pitch=None,
        onset=None,
        release=None,
        velocity=None,
        other=None,
    ):
        if isinstance(channel, float):
            breakpoint()
        if output_type == "dict":
            return {
                "filename": midi_basename,
                "type": type_,
                "track": track,
                "channel": channel,
                "pitch": pitch,
                "onset": onset,
                "release": release,
                "velocity": velocity,
                "other": other,
            }
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

    def _get_time(tick_time):
        if time_type == fractions.Fraction:
            return fractions.Fraction(
                tick_time, ticks_per_beat
            ).limit_denominator(max_denominator=max_denominator)
        return time_type(tick_time / ticks_per_beat)

    def _pitch_bend_handler(track_pb_dict, msg):
        track_pb_dict[msg.channel] = msg.pitch

    def _note_on_handler(msg, track_note_on_dict, track_pb_dict):
        if track_pb_dict is None:
            # msg.note as key is a midinumber (0-127)
            # msg.note as second item of tuple is a pitch number (which depends
            #   in principle on the temperament)
            track_note_on_dict[msg.channel][msg.note].append((msg, msg.note))
            return
        pitch_bend = (
            0 if channel not in track_pb_dict else track_pb_dict[channel]
        )
        # TODO document that an error will be raised if this is not found
        pitch = inverse_pb_tup_dict[(msg.note, pitch_bend)]
        track_note_on_dict[msg.channel][msg.note].append((msg, pitch))

    def _note_off_handler(msg, track_i, track_note_on_dict):
        midinum = msg.note
        out = []
        while True:
            try:
                note_on_msg, pitch = track_note_on_dict[msg.channel][
                    midinum
                ].pop(0 if overlapping_notes == "end_first" else -1)
            except IndexError:
                if out:
                    return out
                warnings.warn(
                    f"note_off event with pitch {msg.note} at "
                    f"time {_get_time(msg.time)} "
                    f"on track {track_i}, "
                    f"channel {msg.channel}, but no note_on event still sounding"
                )
                return None

            onset = _get_time(note_on_msg.time)
            release = _get_time(msg.time)
            out.append(
                _event(
                    type_="note",
                    track=track_i,
                    channel=msg.channel,
                    pitch=pitch,
                    onset=onset,
                    release=release,
                    velocity=note_on_msg.velocity,
                )
            )
            if overlapping_notes != "end_all":
                return out

    def _other_msg_handler(msg, track_i):
        other = vars(msg)
        onset = _get_time(other.pop("time"))
        type_ = other.pop("type")
        try:
            channel = other.pop("channel")
        except KeyError:
            channel = None
        return _event(
            type_=type_,
            track=track_i,
            channel=channel,
            onset=onset,
            other=other,  # TODO format vars somehow?
        )

    # Sorting the tracks avoids orphan note or pitchwheel events.
    in_mid = mido.MidiFile(in_midi_fname)
    _convert_to_abs_time_and_sort(in_mid)
    num_tracks = len(in_mid.tracks)
    ticks_per_beat = in_mid.ticks_per_beat
    out = []

    note_on_dict = {
        i: {j: collections.defaultdict(list) for j in range(NUM_CHANNELS)}
        for i in range(num_tracks)
    }
    if pb_tup_dict is not None:
        pitch_bend_dict = {
            i: {j: {} for j in range(NUM_CHANNELS)} for i in range(num_tracks)
        }
        inverse_pb_tup_dict = {v: k for k, v in pb_tup_dict.items()}

    # messages don't have a track attribute, so (as far as I can tell) the only
    # way to assign each message to a track is to iterate over the tracks
    # and then combine and sort afterwards. This seems inefficient (but maybe
    # it's what mido is doing under the hood anyway when we iterate over the
    # whole file?)
    for track_i, track in enumerate(in_mid.tracks):
        if pb_tup_dict is None:
            track_pb_dict = None
        else:
            track_pb_dict = pitch_bend_dict[track_i]
        for msg in track:
            if msg.type == "pitchwheel":
                _pitch_bend_handler(track_pb_dict, msg)
            elif msg.type == "note_off" or (
                msg.type == "note_on" and msg.velocity == 0
            ):
                notes = _note_off_handler(msg, track_i, note_on_dict[track_i])
                if notes:
                    out.extend(notes)
            elif msg.type == "note_on":
                _note_on_handler(msg, note_on_dict[track_i], track_pb_dict)
            else:
                out.append(_other_msg_handler(msg, track_i))

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
    if output_type == "dict":
        # TODO verify dicts are sortable
        out.sort(key=lambda x: 0 if x["release"] is None else x["release"])
        out.sort(
            key=lambda x: 128 if x["pitch"] is None else x["pitch"],
            reverse=True,
        )
        out.sort(key=lambda x: x["track"])
        out.sort(key=lambda x: x["onset"])
    else:
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
