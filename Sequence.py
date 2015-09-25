# This is the Sequence object, which handles midi event list for playing for each track.

NOTE_OFF = 0
NOTE_ON = 1
CONTROL = 2
PITCHBEND = 3

class Sequence:
	def __init__(self, length):
	
		#Sequence data
		self.sequence = [[]]*length

		#Due to some reason the previous consturctor makes a shared list for all items.
		#Here we fix that
		for i in range(length):
			self.sequence[i] = []
		
		self.len = length
	
	def add_note(self, note, pos, duration, volume):
		self.sequence[pos % self.len].append( (NOTE_ON, note, volume) )
		self.sequence[(pos+duration) % self.len].insert( 0, (NOTE_OFF, note, 0) )

	def del_note(self, note, pos, duration):
		for (devent, dnote, dvolume) in self.sequence[pos % self.len]:
			if (devent, dnote) == (NOTE_ON, note):
				self.sequence[pos % self.len].remove( (NOTE_ON, note, dvolume) )
				if (NOTE_OFF, note, 0) in self.sequence[(pos+duration) % self.len]:
					self.sequence[(pos+duration) % self.len].remove( (NOTE_OFF, note, 0) )

	def set_control(self, pos, param, value):
		for (event, oparam, ovalue) in self.sequence[pos % self.len]:
			if event == CONTROL and oparam == param:
				self.del_control(pos, oparam, ovalue)
				break
				
		self.sequence[pos % self.len].append( (CONTROL, param, value) )

	def del_control(self, pos, param, value):
		try:
			self.sequence[pos % self.len].remove((CONTROL, param, value))
		except:
			pass

	def set_pitchbend(self, pos, value):
		for (event, ovalue, foo) in self.sequence[pos % self.len]:
			if event == CONTROL:
				self.del_pitchbend(pos, ovalue)
				break

		self.sequence[pos % self.len].append( (PITCHBEND, value, 0) )
		

	def del_pitchbend(self, pos, value):
		try:
			self.sequence[pos % self.len].remove( (PITCHBEND, value, 0) )
		except:
			pass
		
	def add_track(self, track):
		for (note, pos, duration, volume) in track.get_notes():
			self.sequence[pos % self.len].append( (NOTE_ON, note, volume) )
			self.sequence[(pos+duration) % self.len].insert( 0, (NOTE_OFF, note, 0) )

	def get_sequence(self):
		return self.sequence
