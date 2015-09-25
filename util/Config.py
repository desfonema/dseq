import os

class Config:
	def __init__(self):
		self.last_used_dir = ''
		self.midi_input = ''
		self.filename = ''
		self.value = {}
		
		if os.path.exists(os.path.expanduser('~/.config/dseq/dseq.conf')):
			self.filename = os.path.expanduser('~/.config/dseq/dseq.conf')
		else:
			if not os.path.exists(os.path.expanduser('~/.config')):
				os.mkdir(os.path.expanduser('~/.config'))
				
			if not os.path.exists(os.path.expanduser('~/.config/dseq/')):
				os.mkdir(os.path.expanduser('~/.config/dseq'))
				
			if not os.path.exists(os.path.expanduser('~/.config/dseq/dseq.conf')):
				try:
					f = open(os.path.expanduser('~/.config/dseq/dseq.conf'), 'w')
					f.close()
					self.filename = os.path.expanduser('~/.config/dseq/dseq.conf')
				except:
					pass
					
		if self.filename:
			f = open(os.path.expanduser('~/.config/dseq/dseq.conf'), 'r')
			line = f.readline()
			while line:
				line = line.split('=')
				self.value[line[0].strip()] = line[1].strip()
				line = f.readline()
	
	def save(self):
		if self.filename:
			f = open(os.path.expanduser('~/.config/dseq/dseq.conf'), 'w')
			for key in self.value:
				f.write(key + '=' + self.value[key] + '\n')
			f.close()
