#!/usr/bin/env python3
import sys
import argparse
import math
import mido

class XMessage:
	def __init__(self, msg, track, pitch, program):
		self.msg = msg
		self.track = track
		self.pitch = pitch
		self.program = program

	def eqNote(self, target):
		return self.msg.channel == target.msg.channel \
			and self.msg.note == target.msg.note and self.track == target.track

	def eqAllNote(self, target):
		return self.msg.channel == target.msg.channel and self.track == target.track


class Notes:
	def __init__(self, inputFile):
		midi = mido.MidiFile(inputFile)
		self.tpb = midi.ticks_per_beat
		self.notes = self.__noteEvents(midi)
		self.results = None

	def save(self, output_name):
		if self.results is None:
			raise Exception('Result is None')

		tracks = None if output_name is None else []
		for i in range(len(self.results) - 1):
			self.__save(tracks, self.results[i], self.results[i+1])

		if tracks is not None:
			track = mido.MidiTrack()
			prevtick = 0
			for xmsg in tracks:
				# 元のtickを採用するとトラック間の整合が取れないのでこうする
				tick = mido.second2tick(xmsg.msg.time, self.tpb, 500000)
				xmsg.msg.time = int(tick - prevtick)
				xmsg.msg.channel = 0
				prevtick = tick
				track.append(xmsg.msg)
			output = mido.MidiFile()
			output.tracks.append(track)
			output.ticks_per_beat = self.tpb
			output.save(output_name)

	@staticmethod
	def __noteEvents(midi):
		events = []
		for idx, track in enumerate(midi.tracks):
			tempo = 500000
			basetime = 0
			pitches = [0] * 16
			program = 0
			for msg in track:
				if msg.time > 0:
					msg.time = mido.tick2second(msg.time, midi.ticks_per_beat, tempo)
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

	@staticmethod
	def __save(output, p, n):
		if output is not None:
			if p.msg.type == 'note_on' and n.msg.type == 'note_off':
				output.append(p)
				output.append(n)
		else:
			hz = None
			if p.msg.type == 'note_off' and n.msg.type == 'note_on':
				hz = 0
			elif p.msg.type == 'note_on' and n.msg.type == 'note_off':
				hz = 440 * (2 ** (((p.msg.note - 69) / 12.0) + (p.pitch/(4096*12))))
			duration = int((n.msg.time - p.msg.time) * 1000)
			if hz is not None and duration > 0:
				print('%s|%d' % (str(hz)[0:5].rjust(5), duration))


class Algorithm:
	def simple(events):
		results = []
		for ev in events:
			prev = None if len(results) == 0 else results[-1]
			if ev.msg.type == 'note_on':
				if len(results) == 0 or prev.msg.type == 'note_off':
					results.append(ev)
			elif ev.msg.type == 'note_off':
				if prev.msg.type == 'note_on' and prev.eqNote(ev):
					results.append(ev)
			elif ev.msg.type == 'aftertouch':
				if ev.msg.value == 0 and prev.msg.type == 'note_on' and prev.eqAllNote(ev):
					ev.msg = mido.Message('note_off', channel=ev.msg.channel, note=prev.msg.note, velocity=127, time=ev.msg.time)
					results.append(ev)
		return results


	def skyline(events):
		results = []
		events.sort(key=lambda ev: (ev.msg.time, -ev.msg.note))
		for ev in events:
			prev = None if len(results) == 0 else results[-1]
			if ev.msg.type == 'note_on':
				if len(results) == 0 or prev.msg.type == 'note_off':
					results.append(ev)
				elif prev.msg.type == 'note_on' and ev.msg.note > prev.msg.note:
					msg = mido.Message('note_off', channel=prev.msg.channel, note=prev.msg.note, velocity=127, time=ev.msg.time)
					results.append(XMessage(msg, prev.track, prev.pitch, prev.program))
					results.append(ev)
			elif ev.msg.type == 'note_off':
				if prev.msg.type == 'note_on' and prev.eqNote(ev):
					results.append(ev)
			elif ev.msg.type == 'aftertouch':
				if ev.msg.value == 0 and prev.msg.type == 'note_on' and prev.eqAllNote(ev):
					ev.msg = mido.Message('note_off', channel=ev.msg.channel, note=prev.msg.note, velocity=127, time=ev.msg.time)
					results.append(ev)
		return results


	def bestk(events, weight=[]):
		import numpy as np
		from scipy.cluster.hierarchy import linkage, fcluster

		notes = {}
		for ev in events:
			key = '%d-%d'% (ev.track, ev.msg.channel)
			if key not in notes:
				notes[key] = []
			notes[key].append(ev)
		for key in notes.keys():
			notes[key] = Algorithm.skyline(notes[key])
			if len(notes[key]) == 0:
				del notes[key]
		if len(notes) == 1:
			return notes[list(notes.keys())[0]]

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
			histograms[key] = [ 0 ] * 12
			for ev in notes[key]:
				if ev.msg.type == 'note_on':
					histograms[key][ev.msg.note % 12] += 1

		hbar = [ len(notes) ] * 12
		hwbar = [ 1 ] * 12 if len(weight) != 12 else weight
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

		results = []
		best = [ min(clusters[i], key=lambda k: -xs[k]) for i in range(len(clusters)) ]
		for ev in events:
			key = '%d-%d'% (ev.track, ev.msg.channel)
			if key in best:
				results.append(ev)

		return Algorithm.skyline(results)


	def sudha07(events):
		def selectTrackOrChannel(trch):
			for key in trch.keys():
				trch[key] = Algorithm.skyline(trch[key])
				if len(trch[key]) == 0:
					del trch[key]

			params = {}
			params['max'] = [ 0, 0, 0 ]
			for key in trch.keys():
				notes = [ ev.msg.note for ev in trch[key] if ev.msg.type == 'note_on' ]
				count = len(notes)
				mean = sum(notes) / count
				distinct = len(list(set(notes)))

				cross = 0
				plus = None
				for ev in trch[key]:
					if ev.msg.type != 'note_on':
						continue
					tmp = ev.msg.note > mean
					if plus is not None:
						cross += int(plus != tmp)
					plus = tmp

				params[key] = [ count, cross, distinct ]
				for i in range(3):
					params['max'][i] = max(params[key][i], params['max'][i])

			w = [ 0.4, 0.4, 0.2 ]
			rank = {}
			for key in trch.keys():
				rank[key] = sum([ w[i] * (params[key][i] / params['max'][i]) ])
			return max(rank.items(), key=lambda x:x[1])[0]


		notes = {}
		for ev in events:
			key = '%d-%d' % (ev.track, ev.msg.channel)
			if key not in notes:
				notes[key] = []

			if ev.msg.type == 'note_off' or (ev.msg.type == 'aftertouch' and ev.msg.velocity == 0):
				target = None
				for i in reversed(range(len(notes[key]))):
					if notes[key][i].msg.type != 'note_on':
						continue
					if (ev.msg.type == 'note_off' and notes[key][i].msg.note == ev.msg.note) \
						or (ev.msg.type == 'aftertouch' and notes[key][i].channel == ev.msg.channel):
						target = i
						break
				if target is not None:
					duration = ev.msg.time - notes[key][target].msg.time
					if duration < 0.2 or duration > 2:
						del notes[key][target]
						continue
			notes[key].append(ev)


		tracks = {}
		for key in notes.keys():
			id = key.split('-')[0]
			if id not in tracks:
				tracks[id] = []
			tracks[id].extend(notes[key])
		track = selectTrackOrChannel(tracks)

		channels = {}
		for key in notes.keys():
			id = key.split('-')
			if id[0] != track:
				continue
			if id[1] not in channels:
				channels[id[1]] = []
			channels[id[1]].extend(notes[key])
		channel = selectTrackOrChannel(channels)

		extract = []
		for ev in events:
			if int(track) == ev.track or int(channel) == ev.msg.channel:
				extract.append(ev)
		return Algorithm.skyline(extract)



if __name__ == '__main__':
	parser = argparse.ArgumentParser()
	parser.add_argument('inputFile')
	parser.add_argument('outputFile', nargs='?', default=None)
	parser.add_argument('-m', '--method', default='skyline')
	args = parser.parse_args()

	notes = Notes(args.inputFile)
	if args.method == 'simple':
		notes.results = Algorithm.simple(notes.notes)
	elif args.method == 'skyline':
		notes.results = Algorithm.skyline(notes.notes)
	elif args.method == 'bestk':
		notes.results = Algorithm.bestk(notes.notes)
	elif args.method == 'sudha07':
		notes.results = Algorithm.sudha07(notes.notes)
	notes.save(args.outputFile)
