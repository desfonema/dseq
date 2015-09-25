from os import popen, getpid
from alsaseq import alsaseq
import re

#Class to manage MIDI Connections
class Connections:
	def __init__(self, input_device=''):
		self.conn_ports = []
		self.conn_names = []

		self.midi_port_name = 'Desfonema Sequencer (' + str(getpid()) + ')'
		self.seq = alsaseq(self.midi_port_name)

		self.input_device = input_device
		self.seq.create_input()
		self.refresh_connections()

	def midi_input_event_pending(self):
		return self.seq.event_input_pending()

	def get_midi_input_event(self):
		return self.seq.event_input()
		
	def get_port(self, name):
		try:
			return self.conn_ports[self.conn_names.index(name)]
		except:
			return None
	
	def get_output_list(self):
		return self.conn_names
		
	def refresh_connections(self):

		#Get MIDI Output ports LIST
		outputs = getports('o')
		for conn_name in outputs:
			self.create_port(conn_name)
									
		inputs = getports('i')
		for port in inputs[self.midi_port_name][1]:
			if port in outputs:
				#Connect it
				tmp = popen("aconnect %s:%s %s" % (inputs[self.midi_port_name][0], inputs[self.midi_port_name][1][port], outputs[port][0]))
				tmp.close()

	def create_port(self, conn_name):
		if conn_name != self.midi_port_name:
			if conn_name not in self.conn_names:
				#Create Output MIDI port
				seq_port = ConnectionPort(self.seq, self.seq.create_output(conn_name))
				#Save Conn Data
				self.conn_ports.append(seq_port)
				self.conn_names.append(conn_name)				

	def change_input_device(self, input_device):
		if self.input_device:
			tmp = popen("aconnect -d '%s' '%s'" % (self.input_device, self.midi_port_name))
			tmp.close()

		tmp = popen("aconnect '%s' '%s'" % (input_device, self.midi_port_name))
		tmp.close()
		
		self.input_device = input_device		

	def get_input_devices(self):
		input_devices = getports('i')
		idevs = []
		for idev in input_devices:
			if idev != self.midi_port_name:
				idevs.append(idev)
		return idevs

	def connect_input_device(self,input_device):
		input_devices = getports('i')
		for idev in input_devices:
			if idev != self.midi_port_name:
				print idev

def getports(s):
	#Get MIDI Input ports LIST
	f = popen('aconnect -' + s)
	inputs = {}
	port_name = ''
	line = f.readline()
	while line:
		m = re.search("client (\d+): '(.*)' .*", line)
		if m:
			if port_name:
				inputs[port_name] = (port_number, port_channels)
			port_channels = {}
			port_number = m.group(1)
			port_name = m.group(2).strip()
		else:
			m = re.search(" *(\d+) '(.*)'", line)
			if m:
				port_channels[m.group(2).strip()] = m.group(1)

		line = f.readline()
	f.close()
	if port_name:
		inputs[port_name] = (port_number, port_channels)
	return inputs

class ConnectionPort:
	def __init__(self, seq, port):
		self.seq = seq
		self.port = port
		
	def note_on(self, note, channel=0, vol=127):
		self.seq.note_on(self.port,note,channel,vol)

	def note_off(self, note, channel=0):
		self.seq.note_off(self.port,note,channel)
		
	def set_control(self, value, param, channel=0):
		self.seq.set_control(self.port,value, param, channel)
		
	def set_pitchbend(self, value, channel=0):
		self.seq.set_pitchbend(self.port,value, channel)
