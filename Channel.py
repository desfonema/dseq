#Channel Object. Actually 1 channel only for each song, but in the future 
#the idea is to have an abritrary channel list to play different patterns
#at the same time 

class Channel:
	def __init__(self):
		self.playlist = []
		self.name = ''
		
	def set_name(self, name):
		self.name = name
		
	def get_name(self):
		return self.name
	
	def add_pattern(self, pattern=None):
		self.playlist.append(pattern)
	
	def change_pattern(self, pattern, pos):
		self.playlist[pos] = pattern
	
	def del_pattern(self, pattern):
		while pattern in self.playlist:
			self.playlist.remove(pattern)
	
	def insert_pattern(self, pattern, pos):
		self.playlist.insert(pos, pattern)

	def remove_pattern(self, pos):
		self.playlist.pop(pos)

	def get_patterns(self):
		return self.playlist
