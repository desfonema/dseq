#
#      This program is free software; you can redistribute it and/or modify
#      it under the terms of the GNU General Public License as published by
#      the Free Software Foundation; either version 2 of the License, or
#      (at your option) any later version.
#
#      This program is distributed in the hope that it will be useful,
#      but WITHOUT ANY WARRANTY; without even the implied warranty of
#      MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#      GNU General Public License for more details.
#
#      You should have received a copy of the GNU General Public License
#      along with this program; if not, write to the Free Software
#      Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#

#This is the Track object, which has all the track properties and a note, controller and pitchbend list
#Also has a Sequence object and keeps it updated for playing the midi events.

from models.Sequence import *

TICKS_PER_BEAT = 24

class Track:
	def __init__(self, pat_len = 32):
		self.name = ''
		self.volume = 64
		self.len = pat_len
		self.notes = []
		self.controllers = []
		self.pitchbends = []
		self.synth = ''
		self.port = 0
		self.enabled = True

		#Sequence data for playing
		self.sequence = Sequence(self.len*TICKS_PER_BEAT)

	def set_name(self, name):
		self.name = name
		
	def get_name(self):
		return self.name

	# Adds a note. overlap give us the posibility of inserting two identical notes
	# and that's useful while working with selected notes
	def add_note(self, note, time, duration=1, volume=127, overlap=False):
		if overlap:
			self.notes.append( (note, time, duration, volume) )
			self.sequence.add_note(note, time, duration, volume)
		else:
			exists = False
			snotes = self.notes
			#Let's see if already exists
			for i in range(len(snotes)):
				(snote, stime, sduration, svolume) = snotes[i]
				if (note, time, duration) == (snote, stime, sduration):
					exists = True
					break
					
			if exists:
				self.del_note(stime, snote, sduration)
				self.sequence.del_note(note, time, duration)

			self.notes.append( (note, time, duration, volume) )
			self.sequence.add_note(note, time, duration, volume)
	
	def del_note(self, pos, note, duration=0):
		if duration:
			for (dnote, dtime, dduration, dvolume) in self.notes:
				if dnote == note and dtime == pos and dduration == duration:
					self.notes.remove((dnote, dtime, dduration, dvolume))
					self.sequence.del_note(dnote, dtime, dduration)
					break
		else:
			for (dnote, dtime, dduration, dvolume) in self.notes:
				if dnote == note and dtime == pos:
					self.notes.remove((dnote, dtime, dduration, dvolume))
					self.sequence.del_note(dnote, dtime, dduration)
	
	def get_notes(self):
		return self.notes
		
	def set_control(self, pos, param, value):
		for (opos, oparam, ovalue) in self.controllers:
			if (opos == pos) and (oparam == param):
				self.controllers.remove((opos, oparam, ovalue))
				break
				
		self.controllers.append((pos, param, value))
		self.sequence.set_control(pos, param, value)

	def del_control(self, pos, param, value):
		self.controllers.remove((pos, param, value))
		self.sequence.del_control(pos, param, value)
		
	def get_controllers(self):
		return self.controllers
		
	def set_pitchbend(self, pos, value):
		for (opos, ovalue) in self.pitchbends:
			if opos == pos:
				self.pitchbends.remove((opos, ovalue))
				break

		self.pitchbends.append((pos, value))
		self.sequence.set_pitchbend(pos, value)

	def del_pitchbend(self, pos, value):
		self.pitchbends.remove((pos, value))
		self.sequence.del_pitchbend(pos, value)
		
	def get_pitchbends(self):
		return self.pitchbends
		
	def set_volume(self,volume):
		self.volume = volume
		
	def get_volume(self):
		return self.volume
		
	def set_len(self, pat_len):
		self.len = pat_len
		self.sequence = Sequence(self.len*TICKS_PER_BEAT)
		for (note, time, duration, volume) in self.notes:
			self.sequence.add_note(note, time, duration, volume)
	
	def get_len(self):
		return self.len
		
	def set_synth(self, synth):
		self.synth = synth

	def get_synth(self):
		return self.synth
		
	def set_port(self, port):
		self.port = port
		
	def get_port(self):
		return self.port
		
	def enable(self):
		self.enabled = True
	
	def disable(self):
		self.enabled = False
	
	def get_sequence(self):
		return self.sequence.get_sequence()
