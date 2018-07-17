#!/usr/bin/env python3
import sys
import math
import mido
import numpy as np
from scipy.cluster.hierarchy import linkage, fcluster

class XMessage:
	def __init__(self, msg, track, pitch, program):
		self.msg = msg
		self.track = track
		self.pitch = pitch
		self.program = program

def noteEvents(input):
	events = []
	for idx, track in enumerate(input.tracks):
		tempo = 500000
		basetime = 0
		pitches = [0] * 16
		program = 0
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
			elif msg.type == 'pitchwheel':
				pitches[msg.channel] = msg.pitch
			elif msg.type == 'program_change':
				program = msg.program

			if program in [52, 53] or program >= 112:
				continue
			elif msg.type in [ 'note_on', 'note_off', 'aftertouch' ] and msg.channel != 9:
				xmsg = XMessage(msg, idx, pitches[msg.channel], program)
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
	for ev in events:
		prev = None if len(results) == 0 else results[-1]
		if ev.msg.type == 'note_on':
			if len(results) == 0 or prev.msg.type == 'note_off':
				results.append(ev)
		elif ev.msg.type == 'note_off':
			if prev.msg.type == 'note_on' and prev.msg.channel == ev.msg.channel and prev.msg.note == ev.msg.note and prev.track == ev.track:
				results.append(ev)
		elif ev.msg.type == 'aftertouch':
			if ev.msg.value == 0 and prev.msg.type == 'note_on' and prev.msg.channel == ev.msg.channel and prev.track == ev.track:
				ev.msg = mido.Message('note_off', channel=ev.msg.channel, note=prev.msg.note, velocity=127, time=ev.msg.time)
				results.append(ev)
	return results

def skyline(events):
	results = []
	events.sort(key=lambda ev: (ev.msg.time, -ev.msg.note))
	for idx, ev in enumerate(events):
		prev = None if len(results) == 0 else results[-1]
		if ev.msg.type == 'note_on':
			if len(results) == 0 or prev.msg.type == 'note_off':
				results.append(ev)
			elif prev.msg.type == 'note_on' and ev.msg.note > prev.msg.note:
				msg = mido.Message('note_off', channel=prev.msg.channel, note=prev.msg.note, velocity=127, time=ev.msg.time)
				results.append(XMessage(msg, prev.track, prev.pitch, prev.program))
				results.append(ev)
		elif ev.msg.type == 'note_off':
			if prev.msg.type == 'note_on' and prev.msg.channel == ev.msg.channel and prev.msg.note == ev.msg.note and prev.track == ev.track:
				results.append(ev)
				while events[idx] != prev:
					if events[idx].msg.type == 'note_on' and events[idx].msg.note > prev.msg.note:
						msg = mido.Message('note_on', channel=events[idx].msg.channel, note=events[idx].msg.note, velocity=127, time=ev.msg.time)
						results.append(XMessage(msg, events[idx].track, events[idx].pitch, events[idx].program))
						break
					idx -= 1
		elif ev.msg.type == 'aftertouch':
			if ev.msg.value == 0 and prev.msg.type == 'note_on' and prev.msg.channel == ev.msg.channel and prev.track == ev.track:
				ev.msg = mido.Message('note_off', channel=ev.msg.channel, note=prev.msg.note, velocity=127, time=ev.msg.time)
				results.append(ev)
	return results

def bestk(events):
	notes = {}
	for ev in events:
		key = '%d-%d'% (ev.track, ev.msg.channel)
		if key not in notes:
			notes[key] = []
		notes[key].append(ev)
	for key in notes.keys():
		notes[key] = skyline(notes[key])

	xs = {}
	for key in notes.keys():
		s = 0
		counts = [0] * 128
		for ev in notes[key]:
			if ev.msg.type == 'note_on':
				s += ev.msg.note
				counts[ev.msg.note] += 1
		c = sum(counts)
		avg = s / c
		entropy = 0
		nz = 0
		for i in range(128):
			if counts[i] == 0:
				continue
			p = counts[i] / c
			entropy -= p * math.log2(p)
			nz += 1
		entropy = entropy / -math.log2(1/nz)
		xs[key] = avg + entropy * 128

	histograms = {}
	for key in notes.keys():
		tmp = [ 0 ] * 12
		for ev in notes[key]:
			if ev.msg.type == 'note_on':
				tmp[ev.msg.note % 12] += 1
		histograms[key] = [ v / sum(tmp) for v in tmp ]
	hbar = [ len(notes) ] * 12
	hwbar = [ 1 ] * 12
	for i in range(12):
		s = sum([ histograms[k][i] for k in notes.keys() ])
		hbar[i] = s / hbar[i]
		hwbar[i] = s * hwbar[i]
	threshold = np.linalg.norm(np.array(hbar)-np.array(hwbar)) / 2

	aggregate = linkage([ histograms[k] for k in notes.keys() ], method='ward', metric='euclidean')
	cluster = fcluster(aggregate, threshold, criterion='distance')
	clusters = [ None ] * max(cluster)
	for idx, id in enumerate(cluster):
		if clusters[id-1] is None:
			clusters[id-1] = []
		clusters[id-1].append(list(notes.keys())[idx])

	best = [ min(clusters[i], key=lambda k: -xs[k]) for i in range(len(clusters)) ]
	results = []
	for ev in events:
		key = '%d-%d'% (ev.track, ev.msg.channel)
		if key in best:
			results.append(ev)

	return skyline(results)

def zeroskyline(events):
	keys = []
	for ev in events:
		key = '%d-%d'% (ev.track, ev.msg.channel)
		if key not in keys:
			keys.append(key)
	keys.sort()
	return skyline(list(filter(lambda ev:('%d-%d'% (ev.track, ev.msg.channel)) == keys[0], events)))


if __name__ == '__main__':
	input_name = sys.argv[1]
	output_name = None if len(sys.argv) < 3 else sys.argv[2]
	input = mido.MidiFile(input_name)
	tracks = None if output_name is None else []

	events = noteEvents(input)
	#results = simple(events)
	#results = skyline(events)
	#results = bestk(events)
	results = zeroskyline(events)

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
			xmsg.msg.channel = 0
			prevtick = tick
			track.append(xmsg.msg)
		output = mido.MidiFile()
		output.tracks.append(track)
		output.ticks_per_beat = input.ticks_per_beat
		output.save(output_name)
