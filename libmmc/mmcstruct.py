class KeySign:
    class _Value:
        _code2sym = {}
        def __init__(self, code, symbol):
            self._code2sym[code] = self
            self.code = code
            self.symbol = symbol
            self.is_flat = code >= 0x80
        def __repr__(self):
            return 'KeySign._Value<{}, 0x{:02X}>'.format(self.symbol, self.code)
        def __str__(self):
            return self.symbol
    C      = _Value(0x00, 'C')
    G      = _Value(0x01, 'G')
    D      = _Value(0x02, 'D')
    A      = _Value(0x03, 'A')
    E      = _Value(0x04, 'E')
    B      = _Value(0x05, 'B')
    Fsharp = _Value(0x06, 'F#')
    Csharp = _Value(0x07, 'C#')
    Gsharp = _Value(0x08, 'G#')
    Dsharp = _Value(0x09, 'D#')
    Asharp = _Value(0x0A, 'A#')
    Esharp = _Value(0x0B, 'E#')
    Bsharp = _Value(0x0C, 'B#')
    F      = _Value(0x81, 'F')
    Bflat  = _Value(0x82, 'Bb')
    Eflat  = _Value(0x83, 'Eb')
    Aflat  = _Value(0x84, 'Ab')
    Dflat  = _Value(0x85, 'Db')
    Gflat  = _Value(0x86, 'Gb')
    Cflat  = _Value(0x87, 'Cb')
    Fflat  = _Value(0x88, 'Fb')
    @classmethod
    def from_code(cls, code):
        return cls._Value._code2sym[code]

class Note:
    _MIN = 0
    _MAX = _MIN+127
    class _Value:
        _NOTES_SHARP = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
        _NOTES_FLAT = ['C', 'Db', 'D', 'Eb', 'E', 'F', 'Gb', 'G', 'Ab', 'A', 'Bb', 'B']
        def __init__(self, code):
            self.code = code
        def __repr__(self):
            return 'Note._Value<{}, 0x{:02X}>'.format(self.to_symbol(), self.code)
        def __str__(self):
            return self.to_symbol()
        def to_symbol(self, isflat=False):
            n = self.code % 12
            o = self.code // 12 -1
            return '{}{}'.format(self._NOTES_FLAT[n] if isflat else self._NOTES_SHARP[n], o)
    def _def_cache(l):
        return [l['_Value'](i) for i in range(l['_MIN'], l['_MAX']+1)]
    _cache = _def_cache(locals())
    @classmethod
    def from_code(cls, code):
        return cls._cache[code]

class Event:
    def __init__(self, step_time = 0):
        self.step_time = step_time

class NoteEvent(Event):
    def __init__(self, step_time, note, gate_time, velocity):
        super().__init__(step_time)
        self.note = note
        self.gate_time = gate_time
        self.velocity = velocity

class RestEvent(Event):
    def __init__(self, step_time):
        super().__init__(step_time)

class BarEvent(Event):
    def __init__(self):
        super().__init__()

class ProgramChangeEvent(Event):
    def __init__(self, step_time, number):
        super().__init__(step_time)
        self.number = number

class AfterTouchEvent(Event):
    def __init__(self, step_time, intensity):
        super().__init__(step_time)
        self.intensity = intensity

class ControlChangeEvent(Event):
    def __init__(self, step_time, number, value):
        super().__init__(step_time)
        self.number = number
        self.value = value

class KeyPressureEvent(Event):
    def __init__(self, step_time, note, intensity):
        super().__init__(step_time)
        self.note = note
        self.intensity = intensity

class PitchBendEvent(Event):
    def __init__(self, step_time, intensity):
        super().__init__(step_time)
        self.intensity = intensity

class MidiChannelEvent(Event):
    def __init__(self, step_time, number):
        super().__init__(step_time)
        self.number = number

class TempoChangeEvent(Event):
    def __init__(self, step_time, value):
        super().__init__(step_time)
        self.value = value

class RepeatEvent(Event):
    def __init__(self, times):
        super().__init__()
        self.times = times

class BeginRepeatRegionEvent(Event):
    def __init__(self):
        super().__init__()

class DalSegnoEvent(Event):
    def __init__(self):
        super().__init__()

class SegnoEvent(Event):
    def __init__(self):
        super().__init__()

class ToCodaEvent(Event):
    def __init__(self):
        super().__init__()

class CodaEvent(Event):
    def __init__(self):
        super().__init__()

class RepeatFirstTimeEvent(Event):
    def __init__(self):
        super().__init__()

class RepeatSecondTimeEvent(Event):
    def __init__(self):
        super().__init__()

class FineEvent(Event):
    def __init__(self):
        super().__init__()

class ExclusiveMessageEvent(Event):
    def __init__(self, number):
        super().__init__()
        self.number = number

class Track:
    def __init__(self, *,
                 id = 0,
                 key_signature = 'C',
                 midi_channel = 0,
                 comment = '',
                 events = []):
        self.id = id
        self.key_signature = key_signature
        self.midi_channel = midi_channel
        self.comment = comment
        self.events = events

    def __repr__(self):
        return r"{{track: {{id: {}, key_signature: {}, midi_channel: {}, comment: {}, events: {}}}".format(
            self.id, self.key_signature, self.midi_channel, self.comment, self.events)

class RhythmInstrument:
    def __init__(self, *, id = 0, note_number = 60, midi_channel = 0, gate_time = 1, name = ''):
        self.id = id
        self.note_number = note_number
        self.midi_channel = midi_channel
        self.gate_time = gate_time
        self.name = name

    def __repr__(self):
        return r"{{rhythm_instrument: {{id: {}, name: {}, midi_channel: {}, note_number: {}, gate_time: {}}}".format(
            self.id, self.name, self.midi_channel, self.note_number, self.gate_time)

class RhythmPattern:
    def __init__(self, *, id = 0, bar_length = 192, events = []):
        self.id = id + 1
        self.bar_length = bar_length
        self.events = events

    def __repr__(self):
        return r"{{id: {}, rhythm_pattern: {{bar_length: {}, events: {}}}".format(self.id, self.bar_length, self.events)

class Rhythm:
    NUM_INSTRUMENTS = 32
    NUM_VELOCITIES = 8
    def __init__(self, *,
                 master_midi_channel = 15,
                 instruments = [RhythmInstrument() for _ in range(NUM_INSTRUMENTS)],
                 velocities = [127] * NUM_VELOCITIES,
                 events = [],
                 patterns = []):
        self.master_midi_channel = master_midi_channel
        self.instruments = instruments
        self.velocities = velocities
        self.events = events
        self.patterns = patterns

    def __repr__(self):
        return r"{{rhythm: {{master_midi_channel: {}, instruments: {}, velocities: {}, events: {}, patterns: {}}}".format(
            self.master_midi_channel, self.instruments, self.velocities, self.events, self.patterns)

class Song:
    NUM_TRACKS = 16
    def __init__(self, *,
                 title = '',
                 time_base = 48,
                 tempo = 120,
                 time_signature_numerator = 4, time_signature_deniminator = 4,
                 tracks = [Track() for _ in range(NUM_TRACKS)],
                 rhythm = Rhythm()):
        self.title = title
        self.time_base = time_base
        self.tempo = tempo
        self.time_signature_numerator = time_signature_numerator
        self.time_signature_deniminator = time_signature_deniminator
        self.tracks = tracks
        self.rhythm = rhythm

    def __repr__(self):
        return r"{{song: {{title:{}, time_base:{}, tempo:{}, time_signature:'{}/{}', tracks: {}, rhythm: {}}}".format(
            self.title, self.time_base, self.tempo, self.time_signature_numerator, self.time_signature_deniminator, self.tracks, self.rhythm)
