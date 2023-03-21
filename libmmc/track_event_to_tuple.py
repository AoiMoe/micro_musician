from . import mmcstruct

class TrackEventToTuple:
    def _note(self, ev):
        return ('Note', '{}({})'.format(ev.note.to_symbol(self.isflat), ev.note.code), ev.gate_time, ev.velocity)
    def _rest(self, ev):
        return ('Rest', )
    def _bar(self, ev):
        self.nbar += 1
        return ('------ {:>3} ------'.format(self.nbar), )
    def _program_change(self, ev):
        return ('Prog', ev.number)
    def _after_touch(self, ev):
        return ('After', ev.instruments)
    def _control_change(self, ev):
        return ('CC', ev.number, ev.value)
    def _key_pressure(self, ev):
        return ('Pressure', ev.note, ev.value)
    def _pitch_bend(self, ev):
        return ('Bend', ev.intensity)
    def _midi_channel(self, ev):
        return ('MIDI', ev.number)
    def _tempo_change(self, ev):
        return ('Tempo', ev.value)
    def _repeat(self, ev):
        return (':|', ev.times)
    def _begin_repeat_region(self, ev):
        return ('|:', )
    def _dal_segno(self, ev):
        return ('D.S.', )
    def _segno(self, ev):
        return ('Segno', )
    def _to_coda(self, ev):
        return ('To Coda', )
    def _coda(self, ev):
        return ('Coda', )
    def _repeat_first_time(self, ev):
        return ('|----> 1', )
    def _repeat_second_time(self, ev):
        return ('|----> 2', )
    def _fine(self, ev):
        return ('Fine', )
    def _exclusive_message(self, ev):
        return ('Excl', ev.number)
    _cls2fun = {
        mmcstruct.NoteEvent: _note,
        mmcstruct.RestEvent: _rest,
        mmcstruct.BarEvent: _bar,
        mmcstruct.ProgramChangeEvent: _program_change,
        mmcstruct.AfterTouchEvent: _after_touch,
        mmcstruct.ControlChangeEvent: _control_change,
        mmcstruct.KeyPressureEvent: _key_pressure,
        mmcstruct.PitchBendEvent: _pitch_bend,
        mmcstruct.MidiChannelEvent: _midi_channel,
        mmcstruct.TempoChangeEvent: _tempo_change,
        mmcstruct.RepeatEvent: _repeat,
        mmcstruct.BeginRepeatRegionEvent: _begin_repeat_region,
        mmcstruct.DalSegnoEvent: _dal_segno,
        mmcstruct.SegnoEvent: _segno,
        mmcstruct.ToCodaEvent: _to_coda,
        mmcstruct.CodaEvent: _coda,
        mmcstruct.RepeatFirstTimeEvent: _repeat_first_time,
        mmcstruct.RepeatSecondTimeEvent: _repeat_second_time,
        mmcstruct.FineEvent: _fine,
        mmcstruct.ExclusiveMessageEvent: _exclusive_message
    }
    def to_tuple(self, ev):
        return self._cls2fun[type(ev)](self, ev)
    def __init__(self, isflat):
        self.isflat = isflat
        self.nbar = 0
