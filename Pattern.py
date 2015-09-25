#Pattern object, a collection of tracks

from Track import Track

class Pattern:

	def __init__(self, i = 0, tracks = 0):
		self.num = i
		self.name = ''
		self.len = 1
		self.enabled = False
		self.tracks = []
		for i in range(tracks):
			self.add_track()
		
	def set_num(self, num):
		self.num = num
		
	def get_num(self):
		return self.num
		
	def set_name(self, name):
		self.name = name
	
	def get_name(self):
		return self.name
	
	def set_len(self, len):
		self.len = len
		for track in self.tracks:
			track.set_len(len)

	def get_len(self):
		return self.len
	
	def add_track(self):
		track = Track(self.len)
		self.tracks.append(track)
		return track
	
	def del_track(self, track):
		self.tracks.remove(track)
		
	def get_track(self, i):
		return self.tracks[i]

	def get_tracks(self):
		return self.tracks
		
	def get_tracks_count(self):
		return len(self.tracks)
		
	def enable(self):
		self.enabled = True
	
	def disable(self):
		self.enabled = False
		
	def get_enabled(self):
		return self.enabled
