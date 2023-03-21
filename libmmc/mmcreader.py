import struct
from . import mmcstruct
from enum import Enum

class BadFormat(Exception):
    pass

class BinReader:
    def __init__(self, input, ofs = 0):
        self.data = input
        self.ofs = ofs

    def skip(self, len = 0):
        r = BinReader(self.data, self.ofs)
        self.ofs += len
        return r

    def raw(self, len):
        r = self.data[self.ofs:self.ofs+len]
        self.ofs += len
        return r

    def parse(self, format, len):
        r = struct.unpack_from(format, self.data, self.ofs)
        self.ofs += len
        return r

def parse_mmc(input):
    input = BinReader(input)
    # header
    header = input.skip(0x200)
    # 0x0000
    magic = header.raw(2)
    if magic != b'MC':
        raise BadFormat('illegal magic')
    # 0x0002
    title = header.raw(30)
    # 0x0020
    (time_base, tempo, time_signature_numerator, time_signature_deniminator) = header.parse('4B', 16)
    # 0x0030
    key_signatures_value = list(header.parse('16B', 16))
    key_signatures = [mmcstruct.KeySign.from_code(v) for v in key_signatures_value]
    # 0x0040
    midi_channels = list(header.parse('16B', 16))
    header.skip(32)
    # 0x0070
    comments = [header.raw(16) for _ in range(16)]
    # 0x0170
    # tracks data
    tracks = [
        parse_track(input,
                    id = i,
                    key_signature = key_signatures[i],
                    midi_channel = midi_channels[i],
                    comment = comments[i],
                    isflat = key_signatures_value[i] > 0x80)
        for i in range(16)
    ]
    sep = input.raw(4)
    if sep != b'\xff\xff\xff\xf1':
        raise BadFormat('illegal separator(2)')

    # parse rhythm
    rhythm = parse_rhythm(input)

    return mmcstruct.Song(
        title = title,
        time_base = time_base,
        time_signature_numerator = time_signature_numerator,
        time_signature_deniminator = time_signature_deniminator,
        tracks = tracks,
        rhythm = rhythm)

def parse_track(input, *,
                id,
                key_signature,
                midi_channel,
                comment,
                isflat):
    events = []
    cont = True
    while cont:
        ev = input.parse('4B', 4)
        out = None
        cont = ev[0] != 0xfe or ev[1] != 0xfe or ev[2] != 0xfe or ev[3] != 0xfe
        if cont:
            if ev[0] == 0xff and ev[1] == 0xff and ev[2] == 0xff:
                pass
            elif ev[0] >= 0 and ev[0] <= 0x7f:
                if ev[2] != 0:
                    out = mmcstruct.NoteEvent(ev[1], mmcstruct.Note.from_code(ev[0]), ev[2], ev[3])
                else:
                    out = mmcstruct.RestEvent(ev[1])
            elif ev[0] == 0xfd:
                out = mmcstruct.BarEvent()
            elif ev[0] == 0xe0:
                out = mmcstruct.ProgramChangeEvent(ev[1], ev[2])
            elif ev[0] == 0xe1:
                out = mmcstruct.AfterTouchEvent(ev[1], ev[2])
            elif ev[0] == 0xe2:
                out = mmcstruct.ControlChangeEvent(ev[1], ev[2], ev[3])
            elif ev[0] == 0xe3:
                out = mmcstruct.KeyPressureEvent(ev[1], ev[2])
            elif ev[0] == 0xe4:
                out = mmcstruct.PitchBendEvent(ev[1], (ev[2] + ev[3]*128)-0x2000)
            elif ev[0] == 0xd0:
                out = mmcstruct.MidiChannelEvent(ev[1], ev[2])
            elif ev[0] == 0xfa:
                out = mmcstruct.TempoChangeEvent(ev[1], ev[2])
            elif ev[0] == 0xfb:
                out = mmcstruct.RepeatEvent(ev[1])
            elif ev[0] == 0xfc:
                out = mmcstruct.BeginRepeatRegionEvent()
            elif ev[0] == 0xf0:
                if ev[1] == 0:
                    out = mmcstruct.DalSegnoEvent()
                elif ev[1] == 1:
                    out = mmcstruct.SegnoEvent()
                elif ev[1] == 2:
                    out = mmcstruct.ToCodaEvent()
                elif ev[1] == 3:
                    out = mmcstruct.CodaEvent()
                elif ev[1] == 4:
                    out = mmcstruct.RepeatFirstTimeEvent()
                elif ev[1] == 5:
                    out = mmcstruct.RepeatSecondTimeEvent()
                elif ev[1] == 6:
                    out = mmcstruct.FineEvent()
            elif ev[0] == 0xf2:
                out = mmcstruct.ExclusiveMessageEvent(ev[1])
            else:
                raise BadFormat('unknown track event')
            if out is not None: events.append(out)

    return mmcstruct.Track(id = id, key_signature = key_signature, midi_channel = midi_channel, comment = comment, events = events)


def parse_rhythm(input):
    events = parse_rhythm_track_events(input)
    sep = input.raw(4)
    if sep != b'\xff\xff\xff\xf3':
        raise BadFormat('illegal separator(3)')

    # rhythm pattern header
    # 0x0000
    inst_note_numbers = list(input.parse('32B', 32))
    # 0x0020
    inst_midi_channels = list(input.parse('32B', 32))
    # 0x0040
    (master_midi_channel, ) = input.parse('xB', 2)
    # 0x0042
    inst_gate_times = list(input.parse('32B', 32))
    # 0x0062
    inst_names = [input.raw(8) for i in range(32)]
    # 0x0162
    input.skip(0x200)
    # 0x0362
    pattern_lengths = list(input.parse('64B', 64))
    # 0x03a2
    velocities = list(input.parse('8B', 8))
    # 0x03aa
    sep = input.raw(4)
    if sep != b'\xff\xff\xff\xf4':
        raise BadFormat('illegal separator(4)')

    # patterns
    patterns = [parse_rhythm_pattern(input, i, pattern_lengths[i]) for i in range(64)]
    sep = input.raw(4)
    if sep != b'\xff\xff\xff\xf5':
        raise BadFormat('illegal separator(5)')

    instruments = [
        mmcstruct.RhythmInstrument(
            id = i,
            note_number = inst_note_numbers[i],
            midi_channel = inst_midi_channels[i],
            gate_time = inst_gate_times[i],
            name = inst_names[i])
        for i in range(32)]

    return mmcstruct.Rhythm(
        master_midi_channel = master_midi_channel,
        instruments = instruments,
        velocities = velocities,
        events = events,
        patterns = patterns)

def parse_rhythm_track_events(input):
    events = []
    cont = True
    while cont:
        ev = input.parse('4B', 4)
        cont = ev[0] != 0xfe or ev[1] != 0xfe or ev[2] != 0xfe or ev[3] != 0xfe
        if cont:
            events.append(ev[0])
    return events

def parse_rhythm_pattern(input, id, bar_length):
    events = []
    cont = True
    while cont:
        (t, n) = input.parse('2B', 2)
        cont = t != 0xfe or n != 0xfe
        if cont:
            events.append((t, n % 32, n // 32))
    return mmcstruct.RhythmPattern(id=id, bar_length=bar_length, events=events)
