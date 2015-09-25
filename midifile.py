from midi.MidiOutStream import MidiOutStream
from midi.MidiInFile import MidiInFile
from Song import Song
from Pattern import Pattern
from Track import Track

GUIDE = 12

class NoteOnPrinter(MidiOutStream):

	"Prints all note_on events on channel 0"
	def set_song(self, song):
		self.song = song

	def get_song(self):
		return self.song
		
	def note_on(self, channel=0, note=0x40, velocity=0x40):
		self.note_on_time += self.rel_time()
		self.track.add_note(note, self.note_on_time / GUIDE, 2, velocity)
    
	def note_off(self, channel=0, note=0x40, velocity=0x40):
		self.note_on_time += self.rel_time()
    
	def sequence_name(self, text):
		self.pattern = Pattern()
		self.song.add_pattern(self.pattern)
		
		self.track = self.pattern.add_track()
		
		self.pattern.set_name(text)
		self.pattern.set_len(64)
		
		self.track.set_name(text)

	def start_of_track(self, n_track=0):
		self.note_on_time = 0
		self.note_off_time = 0
		
	def end_of_track(self):
		self.pattern.set_len((self.note_on_time / GUIDE+7) /8)
		
