from . import mmcstruct
from . import track_event_to_tuple

def _bin2str(bin):
    return bin.decode('utf-8', 'backslashreplace').replace('\0', '')

def _iout(outf, level, str):
    outf.write("{}{}\n".format(' '*(level*2), str))

def song_to_yaml(outf, level, song):
    _iout(outf, level, "song:")
    level += 1
    _iout(outf, level, "title: '{}'".format(_bin2str(song.title)))
    _iout(outf, level, 'tempo: {}'.format(song.tempo))
    _iout(outf, level, "time_base: {}".format(song.time_base))
    _iout(outf, level, "time_signature: {}/{}".format(song.time_signature_numerator, song.time_signature_deniminator))
    _iout(outf, level, "tracks:")
    for tr in song.tracks:
        _track_to_yaml(outf, level+1, tr)
    _iout(outf, level, "rhythm:")
    _rhythm_to_yaml(outf, level+1, song.rhythm)

def _track_to_yaml(outf, level, track):
    _iout(outf, level, "- track_no: {}".format(track.id+1))
    level += 1
    _iout(outf, level, "comment: '{}'".format(_bin2str(track.comment)))
    _iout(outf, level, "midi_channel: {}".format(track.midi_channel+1))
    _iout(outf, level, "key_signature: {}".format(track.key_signature))
    _iout(outf, level, "events:")
    conv = track_event_to_tuple.TrackEventToTuple(track.key_signature.is_flat)
    for ev in track.events:
        t = conv.to_tuple(ev)
        _iout(outf, level+1, "- [ {:>3}, {} ]".format(ev.step_time, ', '.join(map(str, t))))

def _rhythm_to_yaml(outf, level, rhythm):
    _iout(outf, level, "master_midi_channel: {}".format(rhythm.master_midi_channel))
    _iout(outf, level, "instruments:")
    for inst in rhythm.instruments:
        _rhythm_instrument_to_yaml(outf, level+1, inst)
    _iout(outf, level, "velocities:")
    for vel in rhythm.velocities:
        _iout(outf, level+1, "- {}".format(vel))
    _iout(outf, level, "events:")
    for ev in rhythm.events:
        _iout(outf, level+1, "- {}".format(ev))
    _iout(outf, level, "patterns:")
    for pat in rhythm.patterns:
        _rhythm_pattern_to_yaml(outf, level+1, pat)

def _rhythm_instrument_to_yaml(outf, level, inst):
    _iout(outf, level, "- instrument_no: {}".format(inst.id))
    level += 1
    _iout(outf, level, "name: '{}'".format(_bin2str(inst.name)))
    _iout(outf, level, "midi_channel: {}".format(inst.midi_channel))
    _iout(outf, level, "note_number: {}".format(inst.note_number))
    _iout(outf, level, "gate_time: {}".format(inst.gate_time))

def _rhythm_pattern_to_yaml(outf, level, pat):
    _iout(outf, level, "- pattern_no: {}".format(pat.id))
    level += 1
    _iout(outf, level, "bar_length: {}".format(pat.bar_length))
    _iout(outf, level, "events:")
    for ev in pat.events:
        _iout(outf, level+1, "- [{:>3}, {}, {}]".format(ev[0], ev[1], ev[2]))
