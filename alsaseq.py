import alsamidi

EVENT_NOTE = 6
EVENT_CONTROLLER = 10
EVENT_PITCH = 13

class alsaseq:
	def __init__(self, name):
		alsamidi.seq_open(name)
		types = alsamidi.seq_event_type_values()
		self.type_note_on = types[0]
		self.type_note_off = types[1]
		self.type_controller = types[2]
		self.type_pitchbend = types[3]
	
	def create_input(self):
		return alsamidi.seq_create_input_port()
	
	def create_output(self, name):
		return alsamidi.seq_create_output_port(name)
	
	def event_input_pending(self):
		return alsamidi.seq_event_input_pending()
	
	def event_input(self):
		return alsamidi.seq_event_input()
	
	def send_output(self, port, ev):
		alsamidi.seq_event_output(
			port,
			ev['type'],
			ev['flags'],
			ev['tag'],
			ev['queue'],
			ev['time']['tick'],
			ev['time']['time']['tv_sec'],
			ev['time']['time']['tv_nsec'],
			ev['source']['client'],
			ev['source']['port'],
			ev['dest']['client'],
			ev['dest']['port'],
			ev['data']['note']['channel'],
			ev['data']['note']['note'],
			ev['data']['note']['velocity'],
			ev['data']['note']['off_velocity'],
			ev['data']['note']['duration'],
			ev['data']['control']['channel'],
			ev['data']['control']['param'],
			ev['data']['control']['value'])
	
	#Cretes an empty event to be modified
	def empty_event(self):
		return {'dest': {'client': 0, 'port': 0}, 'data': {'note': {'note': 0, 'velocity': 0, 'duration': 0, 'off_velocity': 0, 'channel': 0}, 'control': {'value': 0, 'param': 0, 'channel': 0}}, 'queue': 0, 'source': {'client': 0, 'port': 0}, 'tag': 0, 'flags': 0, 'time': {'tick': 0, 'time': {'tv_sec': 0, 'tv_nsec': 0}}, 'type': 0}

	def note_on(self, port, note, channel, velocity):
		ev = self.empty_event()
		ev['type'] = self.type_note_on
		ev['queue'] = 253
		ev['data']['note']['note'] = note
		ev['data']['note']['channel'] = channel
		ev['data']['note']['velocity'] = velocity
		ev['data']['control']['channel'] = channel
		self.send_output(port,ev)
		
	def note_off(self, port, note, channel):
		ev = self.empty_event()
		ev['type'] = self.type_note_off
		ev['queue'] = 253
		ev['data']['note']['note'] = note
		ev['data']['note']['channel'] = channel
		ev['data']['control']['channel'] = channel
		self.send_output(port,ev)
		
	def set_control(self, port, value, param, channel):
		ev = self.empty_event()
		ev['type'] = self.type_controller
		ev['queue'] = 253
		ev['data']['note']['note'] = 0
		ev['data']['note']['channel'] = channel
		ev['data']['control']['channel'] = channel
		ev['data']['control']['value'] = value
		ev['data']['control']['param'] = param
		self.send_output(port,ev)
		
	def set_pitchbend(self, port, value, channel):
		ev = self.empty_event()
		ev['type'] = self.type_pitchbend
		ev['queue'] = 253
		ev['data']['note']['note'] = 0
		ev['data']['note']['channel'] = channel
		ev['data']['control']['channel'] = channel
		ev['data']['control']['value'] = value
		ev['data']['control']['param'] = 0
		self.send_output(port,ev)
