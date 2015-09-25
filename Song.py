from Pattern import Pattern
from Channel import Channel

class Song:
	def __init__(self):
		self.patterns = []
		self.channels = []
		self.bpm = 90
		
	def set_bpm(self, bpm):
		self.bpm = bpm
	
	def get_bpm(self):
		return self.bpm
	
	def add_pattern(self, data = None):
		if data == None:
			pattern = Pattern()
		else:
			pattern = data
		self.patterns.append(pattern)
		return pattern
	
	def del_pattern(self, pattern):
		
		for channel in self.channels:
			channel.del_pattern(pattern)
			
		self.patterns.remove(pattern)
	
	def get_pattern_by_name(self, name):
		pattern = None
		for pat in self.patterns:
			if pat.get_name() == name:
				pattern = pat
		
		return pattern
		
	def get_patterns(self):
		return self.patterns
		
	def add_channel(self, data=None):
		if data == None:
			channel = Channel()
		else:
			channel = data
		self.channels.append(channel)
		return channel
		
	def del_channel(self, channel):
		self.channels.remove(channel)
		
	def get_channels(self):
		return self.channels
		
