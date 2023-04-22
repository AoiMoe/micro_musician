from . import mmcstruct
import struct
import sys

def _put_delta(blob, delta):
    if delta < 0x80:
        blob.append(delta)
    elif delta < 0x4000:
        blob.append(0x80 | (delta >> 7))
        blob.append(delta & 0x7F)
    elif delta < 0x200000:
        blob.append(0x80 | (delta >> 14))
        blob.append(0x80 | ((delta >> 7) & 0x7F))
        blob.append(delta & 0x7F)
    else:
        blob.append(0x80 | (delta >> 21))
        blob.append(0x80 | ((delta >> 14) & 0x7F))
        blob.append(0x80 | ((delta >> 7) & 0x7F))
        blob.append(delta & 0x7F)

class _TrackBuffer:
    def __init__(self, blob = None):
        self.blob = blob if blob else bytearray()
        self.last_tick = 0
    def put_event(self, event_bytes, *, at = None):
        delta = at - self.last_tick if at is not None else 0
        if delta < 0: raise RuntimeError()
        self.last_tick += delta
        _put_delta(self.blob, delta)
        self.blob.extend(event_bytes)
    def put_eot(self, *, at = None):
        self.put_event([0xFF, 0x2F, 0x00], at=at)

class _Gate:
    def __init__(self, midi_channel, note, tick):
        self.key = (midi_channel, note)
        self.tick = tick
    def __lt__(self, other):
        return self.tick < other.tick

class _Converter:
    def __lt__(self, other):
        if other.next_tick is None:
            return True
        if self.next_tick is None:
            return False
        return self.next_tick < other.next_tick

    def __init__(self):
        self.next_event_tick = 0
        self.next_tick = 0
        self.gate_map = dict()
        self.next_gate = None

    def _process_event_hook(self):
        return NotImplemented

    def generate(self):
        if self.next_tick is None:
            return
        if self.next_event_tick == self.next_tick:
            self._process_event_hook()
        elif self.next_gate is not None:
            # note off
            g = self.next_gate
            del self.gate_map[g.key]
            self.out_buffer.put_event([0x80 + g.key[0], g.key[1], 0], at=self.next_tick)
            self._reset_next_gate()
        self._reset_next_tick()

    def _reset_next_tick(self):
        if self.next_gate is not None:
            if self.next_event_tick is not None:
                self.next_tick = min(self.next_gate.tick, self.next_event_tick)
            else:
                self.next_tick = self.next_gate.tick
        else:
            self.next_tick = self.next_event_tick

    def _reset_next_gate(self):
        self.next_gate = min([x for x in self.gate_map.values()]) if self.gate_map else None


class _TrackConverter(_Converter):
    def _process_event_hook(self):
        if self.current_event >= len(self.track.events):
            self.next_event_tick = None
            return
        ev = self.track.events[self.current_event]
        self.current_event += 1
        self._cls2fun[type(ev)](self, ev)
        self.next_event_tick += ev.step_time

    def _note(self, ev):
        g = _Gate(self.midi_channel, ev.note.code, self.next_tick + ev.gate_time)
        if g.key not in self.gate_map:
            self.out_buffer.put_event([0x90 + self.midi_channel, ev.note.code, ev.velocity], at=self.next_tick)
        self.gate_map[g.key] = g
        self._reset_next_gate()
        self._reset_next_tick()

    def _none(self, ev):
        pass

    def _program_change(self, ev):
        self.out_buffer.put_event([0xC0 + self.midi_channel, ev.number], at=self.next_tick)

    def _after_touch(self, ev):
        self.out_buffer.put_event([0xD0 + self.midi_channel, ev.intensity], at=self.next_tick)

    def _control_change(self, ev):
        self.out_buffer.put_event([0xB0 + self.midi_channel, ev.number, ev.value], at=self.next_tick)

    def _key_pressure(self, ev):
        self.out_buffer.put_event([0xA0 + self.midi_channel, ev.note, ev.intensity], at=self.next_tick)

    def _pitch_bend(self, ev):
        v = ev.intensity + 0x2000
        self.out_buffer.put_event([0xE0 + self.midi_channel, v & 0x7F, v >> 7], at=self.next_tick)

    _cls2fun = {
        mmcstruct.NoteEvent: _note,
        mmcstruct.RestEvent: _none,
        mmcstruct.BarEvent: _none,
        mmcstruct.ProgramChangeEvent: _program_change,
        mmcstruct.AfterTouchEvent: _after_touch,
        mmcstruct.ControlChangeEvent: _control_change,
        mmcstruct.KeyPressureEvent: _key_pressure,
        mmcstruct.PitchBendEvent: _pitch_bend,
        mmcstruct.MidiChannelEvent: _none, # FIXME
        mmcstruct.TempoChangeEvent: _none, # FIXME
        mmcstruct.RepeatEvent: _none, # FIXME
        mmcstruct.BeginRepeatRegionEvent: _none, # FIXME
        mmcstruct.DalSegnoEvent: _none, # FIXME
        mmcstruct.SegnoEvent: _none, # FIXME
        mmcstruct.ToCodaEvent: _none, # FIXME
        mmcstruct.CodaEvent: _none, # FIXME
        mmcstruct.RepeatFirstTimeEvent: _none, # FIXME
        mmcstruct.RepeatSecondTimeEvent: _none, # FIXME
        mmcstruct.FineEvent: _none, # FIXME
        mmcstruct.ExclusiveMessageEvent: _none, # FIXME
    }

    def __init__(self, track, out_buffer):
        super().__init__()
        self.track = track
        self.out_buffer = out_buffer
        self.midi_channel = track.midi_channel
        self.current_event = 0

class _RhythmConverter(_Converter):
    def _next(self):
        while not self.pattern_event_queue:
            self.current_pattern_origin_tick += self.current_pattern_bar_length
            self.next_event_tick = self.current_pattern_origin_tick
            if self.current_track_event_index >= len(self.rhythm.events):
                self.pattern_event_queue = None
                return
            p = self.rhythm.patterns[self.rhythm.events[self.current_track_event_index]-1]
            self.current_track_event_index += 1
            self.current_pattern_bar_length = p.bar_length
            self.pattern_event_queue = list(p.events)
        self.next_event_tick = self.pattern_event_queue[0].tick + self.current_pattern_origin_tick
        self._reset_next_tick()

    def _process_event_hook(self):
        if self.pattern_event_queue is None:
            self.next_event_tick = None
            return
        ev = self.pattern_event_queue.pop(0)
        inst = self.rhythm.instruments[ev.instrument]
        velocity = self.rhythm.velocities[ev.velocity]
        g = _Gate(self.midi_channel, inst.note_number, self.next_tick + inst.gate_time)
        if g.key in self.gate_map:
            self.out_buffer.put_event([0x80 + g.key[0], g.key[1], 0], at=self.next_tick)
        self.out_buffer.put_event([0x90 + g.key[0], g.key[1], velocity], at=self.next_tick)
        self.gate_map[g.key] = g
        self._reset_next_gate()
        self._next()

    def __init__(self, rhythm, out_buffer):
        super().__init__()
        self.rhythm = rhythm
        self.out_buffer = out_buffer
        self.midi_channel = rhythm.master_midi_channel
        self.current_track_event_index = 0
        self.current_pattern_origin_tick = 0
        self.current_pattern_bar_length = 0
        self.pattern_event_queue = None
        self._next()

def _make_smf_header_chunk(num_tracks, time_base):
    return bytearray(struct.pack('>4sIIH', b'MThd', 6, num_tracks, time_base))

def _make_track_chunk(blob):
    return struct.pack('>4sI', b'MTrk', len(blob)) + blob

def _put_song_metadata(out_buffer, song):
    title = bytes(song.title.replace(b'\0', b''))
    out_buffer.put_event([0xFF, 0x01, len(title)])
    out_buffer.blob += title
    tempo = 60000000 // song.tempo
    out_buffer.put_event([0xFF, 0x51, 3, tempo >> 16, (tempo >> 8) & 0xFF, tempo & 0xFF])
    d = song.time_signature_deniminator
    ln2d = 0
    while (d & 1) == 0:
        d >>= 1
        ln2d += 1
    out_buffer.put_event([0xFF, 0x58, 0x04, song.time_signature_numerator, ln2d, 0x18, 8])

def _smf0(song):
    out_buffer = _TrackBuffer()
    _put_song_metadata(out_buffer, song)
    convs = [_TrackConverter(tr, out_buffer) for tr in song.tracks]
    convs.append(_RhythmConverter(song.rhythm, out_buffer))
    last_tick = None
    while (next := min(convs)).next_tick is not None:
        last_tick = next.next_tick
        next.generate()
    out_buffer.put_eot(at=last_tick)
    return _make_smf_header_chunk(1, song.time_base) + _make_track_chunk(out_buffer.blob)

def _smf1(song):
    blob = _make_smf_header_chunk(18, song.time_base)
    # tempo track
    out_buffer = _TrackBuffer()
    _put_song_metadata(out_buffer, song)
    out_buffer.put_eot(at=192)
    blob += _make_track_chunk(out_buffer.blob)
    tracks = [(_TrackConverter, tr, tr.comment) for tr in song.tracks]
    tracks.append((_RhythmConverter, song.rhythm, b'rhythm'))
    for (cls, tr, comment) in tracks:
        out_buffer = _TrackBuffer()
        comment = bytes(comment.replace(b'\0', b''))
        out_buffer.put_event([0xFF, 0x03, len(comment)])
        out_buffer.blob += bytes(comment)
        conv = cls(tr, out_buffer)
        last_tick = None
        while conv.next_tick is not None:
            last_tick = conv.next_tick
            conv.generate()
        out_buffer.put_eot(at=last_tick)
        blob += _make_track_chunk(out_buffer.blob)
    return blob

def song_to_smf(song, mode):
    if mode == 0:
        return _smf0(song)
    elif mode == 1:
        return _smf1(song)
    else:
        raise RuntimeError()
