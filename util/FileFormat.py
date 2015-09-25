from models.Song import Song
from models.Channel import Channel
from models.Pattern import Pattern
from models.Track import Track

class DSeq1:
	def __init__(self):
		pass
	
	def open(self, filename):
		# Patterns Object
		song = Song()

		f = open(filename)
		line = f.readline()
		#f.write("Desfonema Sequencer File Format Version 1.1\n")
		version = line[40:-1]
		
		#Old version 1 format used 8 ticks for each beat instead of 24
		#so we need to compensate if it's an old format file.
		if version == '1':
			shifter = 3
		else:
			shifter = 1
		#Level Pattern(0) Track(1) or Notes(2)
		level = 0
		while line:
			line = line[:-1]
			if line == "Pattern":
				pattern = Pattern()
				song.add_pattern(pattern)
				level = 1

			if line == "Track":
				track = pattern.add_track()
				level = 2
			
			if line == "Notes":
				level = 3
				
			if line == "Controls":
				level = 5
				
			if line == "Pitchbends":
				level = 6

			if line == "Channel":
				channel = Channel()
				song.add_channel(channel)
				level = 4

			if level == 0:
				if line[:5] == "Bpm: ":
					song.set_bpm(int(line[5:]))
			if level == 1:
				#On Pattern Data
				if line[:5] == "Num: ":
					pattern.set_num(int(line[5:]))
				elif line[:5] == "Len: ":
					pattern.set_len(int(line[5:]))
				elif line[:6] == "Name: ":
					pattern.set_name(line[6:])
			elif level == 2:
				if line[:5] == "Len: ":
					track.set_len(int(line[5:]))
				elif line[:6] == "Name: ":
					track.set_name(line[6:])
				elif line[:8] == "Volume: ":
					track.set_volume(int(line[8:]))
				elif line[:7] == "Synth: ":
					track.set_synth(line[7:])
				elif line[:6] == "Port: ":
					track.set_port(int(line[6:]))
			elif level == 3:
				if line == "Notes":
					pass
				elif line == "EndNotes":
					level = 2
				else:
					line_data = line.split(', ')
					(note, pos, duration) = (line_data[0], line_data[1], line_data[2])
					if len(line_data) == 4:
						volume = int(line_data[3])
					else:
						volume = 127
					track.add_note(int(note),int(pos)*shifter,int(duration)*shifter, volume)
			elif level == 5:
				if line == "Controls":
					pass
				elif line == "EndControls":
					level = 2
				else:
					line_data = line.split(', ')
					(pos, param, value) = (line_data[0], line_data[1], line_data[2])
					track.set_control(int(pos), int(param), int(value))
					
			elif level == 5:
				if line == "Pitchbends":
					pass
				elif line == "EndPitchbends":
					level = 2
				else:
					line_data = line.split(', ')
					(pos, value) = (line_data[0], line_data[1])
					track.set_control(int(pos), int(value))
			elif level == 4:
				if line[:5] == "Pat: ":
					channel.add_pattern(song.get_pattern_by_name(line[5:]))
			
			line = f.readline()

		f.close()
		
		return song
		
	def save(self, filename, song):
		f = open(filename, 'w')
		f.write("Desfonema Sequencer File Format Version 1.1\n")
		f.write("Bpm: " + str(int(song.get_bpm())) + "\n")
		for pattern in song.get_patterns():
			f.write("Pattern\n")
			f.write("Num: " + str(pattern.get_num()) + "\n")
			f.write("Len: " + str(pattern.get_len()) + "\n")
			f.write("Name: " + pattern.get_name() + "\n")
			f.write("Enabled: " + str(pattern.get_enabled()) + "\n")
			
			for track in pattern.get_tracks():
				f.write("Track\n")
				f.write("Len: " + str(track.get_len()) + "\n")
				f.write("Name: " + track.get_name() + "\n")
				f.write("Volume: " + str(track.get_volume()) + "\n")
				f.write("Synth: " + track.get_synth() + "\n")
				f.write("Port: " + str(track.get_port()) + "\n")
				
				f.write("Notes\n")
				for note_descriptor in track.get_notes():
					f.write("%i, %i, %i, %i\n" % note_descriptor)
				f.write("EndNotes\n")
				
				f.write("Controls\n")
				for control_descriptor in track.get_controllers():
					f.write("%i, %i, %i\n" % control_descriptor)
				f.write("EndControls\n")
				
				f.write("Pitchbends\n")
				for pitch_descriptor in track.get_pitchbends():
					f.write("%i, %i\n" % pitch_descriptor)
				f.write("EndPitchbends\n")
				
				f.write("EndTrack\n")
			f.write("EndPattern\n")
		for channel in song.get_channels():
			f.write("Channel\n")
			for pattern in channel.get_patterns():
				f.write("Pat: " + pattern.get_name() + "\n")
				
			f.write("EndChannel\n")
		f.close()
