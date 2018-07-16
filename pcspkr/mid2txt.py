#!/usr/bin/env python3
import mido
import sys

class XMessage:
	def __init__(self, msg, track, pitch):
		self.msg = msg
		self.track = track
		self.pitch = pitch

def noteEvents(input):
	events = []
	for idx, track in enumerate(input.tracks):
		tempo = 500000
		basetime = 0
		pitches = [0] * 16
		for msg in track:
			if msg.time > 0:
				msg.time = mido.tick2second(msg.time, input.ticks_per_beat, tempo)
			msg.time += basetime
			basetime = msg.time

			if msg.type == 'note_on':
				if msg.velocity == 0:
					msg = mido.Message('note_off', channel=msg.channel, note=msg.note, velocity=127, time=msg.time)
			elif msg.type == 'polytouch':
				if msg.velocity == 0:
					msg = mido.Message('note_off', channel=msg.channel, note=msg.note, velocity=127, time=msg.time)
				else:
					msg = mido.Message('note_on', channel=msg.channel, note=msg.note, velocity=msg.velocity, time=msg.time)
			elif msg.type == 'control_change':
				if msg.control == 0x79:
					pitches = [0] * 16
				if msg.control in [0x78, 0x79, 0x7b]:
					msg = mido.Message('aftertouch', channel=msg.channel, value=0, time=msg.time)
			elif msg.type == 'set_tempo':
				tempo = msg.tempo

			if msg.type == 'pitchwheel':
				pitches[msg.channel] = msg.pitch
			elif msg.type in [ 'note_on', 'note_off', 'aftertouch' ]:
				xmsg = XMessage(msg, idx, pitches[msg.channel])
				events.append(xmsg)

	events.sort(key=lambda xmsg: xmsg.msg.time)
	return events

def save(output, prev, next):
	if prev.msg.type == 'note_off' and next.msg.type == 'note_on':
		hz = 0
	elif prev.msg.type == 'note_on' and next.msg.type == 'note_off':
		hz = 440 * (2 ** (((prev.msg.note - 69) / 12.0) + (prev.pitch/(4096*12))))
	else:
		return

	if output is None:
		duration = int((next.msg.time - prev.msg.time) * 1000)
		if duration > 0:
			print('%s|%d' % (str(hz)[0:5].rjust(5), duration))
	elif prev.msg.type == 'note_on' and next.msg.type == 'note_off':
		output.append(prev)
		output.append(next)


def simple(events):
	results = []
	for event in events:
		prev = None if len(results) == 0 else results[-1]
		if event.msg.type == 'note_on':
			if len(results) == 0 or prev.msg.type == 'note_off':
				results.append(event)
		elif event.msg.type == 'note_off':
			if prev.msg.type == 'note_on' and prev.msg.channel == event.msg.channel and prev.msg.note == event.msg.note and prev.track == event.track:
				results.append(event)
		elif event.msg.type == 'aftertouch':
			if event.msg.value == 0 and prev.msg.type == 'note_on' and prev.msg.channel == event.msg.channel and prev.track == event.track:
				event.msg = mido.Message('note_off', channel=event.msg.channel, note=prev.msg.note, velocity=127, time=event.msg.time)
				results.append(event)
	return results


if __name__ == '__main__':
	input_name = sys.argv[1]
	output_name = None if len(sys.argv) < 3 else sys.argv[2]
	input = mido.MidiFile(input_name)
	tracks = None if output_name is None else []

	events = noteEvents(input)
	results = simple(events)

	for i in range(len(results) - 1):
		prev = results[i]
		next = results[i+1]
		save(tracks, prev, next)

	if output_name is not None:
		track = mido.MidiTrack()
		prevtick = 0
		for xmsg in tracks:
			# 元のtickを採用するとトラック間の整合が取れないのでこうする
			tick = mido.second2tick(xmsg.msg.time, input.ticks_per_beat, 500000)
			xmsg.msg.time = int(tick - prevtick)
			prevtick = tick
			track.append(xmsg.msg)
		output = mido.MidiFile()
		output.tracks.append(track)
		output.ticks_per_beat = input.ticks_per_beat
		output.save(output_name)
