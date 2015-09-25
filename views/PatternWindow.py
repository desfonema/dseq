import gtk
import gobject
from views.TrackWidget import TrackWidget
from views.ControllerEditorWidget import ControllerEditorWidget
from views.PitchbendEditorWidget import PitchbendEditorWidget

KEY_WIDTH = 14
KEY_HEIGHT = 7
KEY_SPACE = 1
BEAT_WIDTH = 24
TICKS_PER_BEAT = 24

class PatternWindow(gtk.Window):
	def __init__(self, container, pat):
		gtk.Window.__init__(self, gtk.WINDOW_TOPLEVEL)

		#Clean MIDI Input
		while container.conn.midi_input_event_pending():
			container.conn.get_midi_input_event()
				
		self.container = container
		self.container.conn.refresh_connections()
		self.synth_list = self.container.conn.get_output_list()
		self.pat = pat
		
		self.set_title("Edit Pattern " + pat.get_name())
		self.set_resizable(True)
		self.connect("destroy", self.close_dialog)

		# A vBox to contain the pattern menu and track list
		self.vbox = gtk.VBox(False, 0)

		#HBox for the pattern options
		hbox = gtk.HBox(False,0)

		#Add new Track
		btn_add_track = gtk.Button("Add _Track")
		btn_add_track.connect("clicked", self.add_track, None)
		btn_add_track.show()
		hbox.pack_start(btn_add_track, True, True, 4)
		
		#Paste new Track
		btn_paste_track = gtk.Button("_Paste Track")
		btn_paste_track.connect("clicked", self.paste_track, None)
		btn_paste_track.show()
		hbox.pack_start(btn_paste_track, True, True, 4)
	
		#MIDI Input
		lbl_midi_input = gtk.Label("MIDI Input:")
		lbl_midi_input.show()
		hbox.pack_start(lbl_midi_input, False, False, 0)
		self.cbo_midi_input = gtk.combo_box_new_text()
		i = 0
		for t in self.container.conn.get_input_devices():
			self.cbo_midi_input.append_text(t)
			if t == self.container.conn.input_device:
				self.cbo_midi_input.set_active(i)
			i = i + 1
		self.cbo_midi_input.connect('changed', self.cbo_midi_input_changed)
		self.cbo_midi_input.show()
		hbox.pack_start(self.cbo_midi_input, False, False, 4)
	
		#Pattern Length
		lbl_len = gtk.Label("Len:")
		lbl_len.show()
		hbox.pack_start(lbl_len, False, False, 0)
		self.adj_len = gtk.Adjustment(value=pat.get_len(), lower=1, upper=64, step_incr=1)
		spn_len = gtk.SpinButton(self.adj_len, 0, 0)
		spn_len.show()
		hbox.pack_start(spn_len, False, False, 4)
				
		#Traditional Change Length
		btn_len = gtk.Button("Change Length")
		btn_len.connect("clicked", self.btn_len_clicked, None)
		btn_len.show()
		hbox.pack_start(btn_len, True, True, 4)
	
		#Expand Track
		btn_expand = gtk.Button("Expand Track")
		btn_expand.connect("clicked", self.btn_expand_clicked, None)
		btn_expand.show()
		hbox.pack_start(btn_expand, True, True, 4)
	
		hbox.show()
		self.vbox.pack_start(hbox, False, False, 0)
		
		#GUI for Tracks

		self.ntb_tracks = gtk.Notebook()
		self.ntb_tracks.connect("switch-page", self.nbt_tracks_switch_page, None)
		self.ntb_tracks.set_tab_pos(gtk.POS_TOP)
		
		self.tw = TrackWidget(pat.get_tracks()[0], self)
		
		for track in pat.get_tracks():
			track_gui = self.draw_track(track)
			if track.get_name():
				lbl_track_name = gtk.Label(track.get_name())
			else:
				lbl_track_name = gtk.Label('Untitled')
			lbl_track_name.show()
			self.ntb_tracks.append_page(track_gui, lbl_track_name)
			track_gui.show()


		self.ntb_tracks.show()

		self.vbox.pack_start(self.ntb_tracks, False, False, 0)

		self.vbox.pack_start(self.tw.get(), True, True, 0)

		self.controller_editor_widget = ControllerEditorWidget(self)
		self.controller_editor_widget.show()
		self.vbox.pack_start(self.controller_editor_widget, False, False, 0)
		
		self.pitchbend_editor_widget = PitchbendEditorWidget(self)
		self.pitchbend_editor_widget.show()
		self.vbox.pack_start(self.pitchbend_editor_widget, False, False, 0)

		self.vbox.show()

		self.add(self.vbox)
		self.tw.area.grab_focus()

	def close_dialog(self, widget, data=None):
		self.tw.btn_stop_clicked(None)
		if self.tw.midi_keyboard_listen:
			gobject.source_remove(self.tw.midi_keyboard_listen)

		self.destroy()
		
	#Callback for Add Track Button
	def add_track(self, widget, data=None):
		track = self.pat.add_track()
		track_gui = self.draw_track(track)
		lbl_track_name = gtk.Label('Untitled')
		lbl_track_name.show()
		self.ntb_tracks.append_page(track_gui, lbl_track_name)
		track_gui.show()
		self.ntb_tracks.set_current_page(self.ntb_tracks.get_n_pages()-1)
		self.tw.area.grab_focus()
		
		self.container.save_state = False
		
	#Callback for Paste Track Button

	def paste_track(self, widget, data=None):
		clipboard = gtk.clipboard_get(gtk.gdk.SELECTION_CLIPBOARD)
		clipboard.request_text(self.paste_track_clipboard_text_received)
		
    # signal handler called when the clipboard returns text data
	def paste_track_clipboard_text_received(self, clipboard, text, data):
		if not text or text == '':
			return
			
		lines = text.split("\n")
		if not len(lines):
			return
			
		if lines[0] != 'Track':
			return

		track = self.pat.add_track()

		level = 0
		for line in lines:

			if line == "Track":
				level = 2
			
			if line == "Notes":
				level = 3

			if level == 2:
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
					(note, pos, duration, volume) = line.split(', ')
					track.add_note(int(note),int(pos),int(duration), int(volume))

		track.set_name("Copy of " + track.get_name())
		track_gui = self.draw_track(track)
		if track.get_name():
			lbl_track_name = gtk.Label(track.get_name())
		else:
			lbl_track_name = gtk.Label('Untitled')
		lbl_track_name.show()
		self.ntb_tracks.append_page(track_gui, lbl_track_name)
		track_gui.show()
		self.ntb_tracks.set_current_page(self.ntb_tracks.get_n_pages()-1)
		self.tw.area.grab_focus()
		self.container.save_state = False

	def cbo_midi_input_changed(self, widget, data= None):
		input_device = widget.get_active_text()
		self.container.conn.change_input_device(input_device)
		self.container.conf.value['input_device'] = input_device
		
	def btn_len_clicked(self, widget, data=None):
		self.pat.set_len(int(self.adj_len.get_value()))
		self.tw.area.set_size_request(self.pat.get_len() * (BEAT_WIDTH + KEY_SPACE * TICKS_PER_BEAT)+32, 128 * (KEY_HEIGHT + KEY_SPACE))
		self.tw.paint_roll()
		self.tw.paint_selection()
		
		self.controller_editor_widget.area_resize()
		self.pitchbend_editor_widget.area_resize()
				
		self.container.save_state = False
		
	def btn_expand_clicked(self, widget, data=None):
		old_len = self.pat.get_len()
		new_len = int(self.adj_len.get_value())

		
		if new_len > old_len:
			self.pat.set_len(new_len)
			for track in self.pat.get_tracks():
				for (note, time, duration, volume) in track.get_notes():
					if time < ((new_len-old_len)*TICKS_PER_BEAT):
						track.add_note(note, time+old_len*TICKS_PER_BEAT, duration, volume)
					
		else:
			for track in self.pat.get_tracks():
				del_notes = []
				for (note, time, duration, volume) in track.get_notes():
					if time >= (new_len*TICKS_PER_BEAT):
						del_notes.append((time, note, duration))
						
				for (time, note, duration) in del_notes:
					track.del_note(time, note, duration)
						
			self.pat.set_len(new_len)
						
		self.tw.area.set_size_request(self.pat.get_len() * (BEAT_WIDTH + KEY_SPACE * TICKS_PER_BEAT)+32, 128 * (KEY_HEIGHT + KEY_SPACE))
		self.tw.paint_roll()
		self.tw.paint_selection()

		self.controller_editor_widget.area_resize()
		self.pitchbend_editor_widget.area_resize()
				
		self.container.save_state = False
		
	#Creates a line for a track
	def draw_track(self, track):
		hbox = gtk.HBox(False,0)
		
		btn_track_copy = gtk.Button("Copy Track")
		btn_track_copy.connect("clicked", self.btn_track_copy_clicked, track)
		btn_track_copy.show()
		hbox.pack_start(btn_track_copy, False, False, 4)
		
		btn_track_del = gtk.Button("Del Track")
		btn_track_del.connect("clicked", self.del_track, (track, hbox))
		btn_track_del.show()
		hbox.pack_start(btn_track_del, False, False, 4)
		
		#track Name
		lbl_track_name = gtk.Label('Name:')
		lbl_track_name.show()
		hbox.pack_start(lbl_track_name, False, False, 4)
		txt_track_name = gtk.Entry()
		txt_track_name.set_text(track.get_name())
		txt_track_name.set_max_length(30)
		txt_track_name.connect("changed", self.txt_track_name_change, track, hbox)
		txt_track_name.show()
		hbox.pack_start(txt_track_name, True, True, 4)
		
		lbl_track_synth = gtk.Label("Synth:")
		lbl_track_synth.show()
		hbox.pack_start(lbl_track_synth, False, False, 4)
		cbo_track_synth = gtk.combo_box_new_text()
		
		i = 0
		for t in self.synth_list:
			cbo_track_synth.append_text(t)
			if t == track.get_synth():
				cbo_track_synth.set_active(i)
			i = i + 1
		
		cbo_track_synth.connect('changed', self.cbo_track_synth_change, track)
		
		cbo_track_synth.show()
		hbox.pack_start(cbo_track_synth, False, False, 4)

		lbl_track_port = gtk.Label("Port:")
		lbl_track_port.show()
		hbox.pack_start(lbl_track_port, False, False, 0)
		adj_track_port = gtk.Adjustment(value=track.get_port(), lower=0, upper=32, step_incr=1)
		adj_track_port.connect("value_changed", self.adj_track_port_change, track)
		spn_track_port = gtk.SpinButton(adj_track_port, 0, 0)
		spn_track_port.show()
		hbox.pack_start(spn_track_port, False, False, 4)

		hbox.show()
		
		return hbox

	def btn_track_copy_clicked(self, widget, data=None):
		track = data
	
		text = ''
		text += "Track\n"
		text += "Len: " + str(track.get_len()) + "\n"
		text += "Name: " + track.get_name() + "\n"
		text += "Volume: " + str(track.get_volume()) + "\n"
		text += "Synth: " + track.get_synth() + "\n"
		text += "Port: " + str(track.get_port()) + "\n"
		
		text += "Notes\n"
		for note_descriptor in track.get_notes():
			text += "%i, %i, %i, %i\n" % note_descriptor
		text += "EndNotes\n"
		
		text += "EndTrack\n"
		
		clipboard = gtk.clipboard_get(gtk.gdk.SELECTION_CLIPBOARD)
		clipboard.set_text(text)		
		self.tw.area.grab_focus()

	def txt_track_name_change(self, widget, data, child):
		data.set_name(widget.get_text())
		self.ntb_tracks.set_tab_label_text(child, data.get_name())
		self.container.save_state = False

	def cbo_track_synth_change(self, widget, data=None):
		#Silence Please... we are changing synth
		synth_conn = self.container.conn.get_port(data.get_synth())
		if synth_conn != None: 
			port = data.get_port()
			for note in range(128):
				synth_conn.note_off(note, port)

		data.set_synth(self.synth_list[widget.get_active()])
		self.container.save_state = False
		self.tw.area.grab_focus()
		#self.tw.area.grab_focus()
				
	def adj_track_port_change(self, widget, data=None):
		if data.get_port() != int(widget.get_value()):
			#Silence Please... we are changing port
			synth_conn = self.container.conn.get_port(data.get_synth())
			if synth_conn != None: 
				port = data.get_port()
				for note in range(128):
					synth_conn.note_off(note, port)
			data.set_port(int(widget.get_value()))
			self.container.save_state = False
			#self.area.grab_focus()
		
	#Callback for Del Track Button
	def del_track(self, widget, data=None):
		
		if len(self.pat.get_tracks()) == 1:
			dialog = gtk.MessageDialog(self, gtk.DIALOG_MODAL , gtk.MESSAGE_ERROR, gtk.BUTTONS_OK,
					"Can't delete last track in pattern.")			
			dialog.run()
			dialog.destroy()
			return
			
		(track, track_gui) = data

		dialog = gtk.MessageDialog(self, gtk.DIALOG_MODAL , gtk.MESSAGE_WARNING, gtk.BUTTONS_YES_NO,
				"Delete track " + track.get_name() + "?")
				
		response = dialog.run()
		dialog.destroy()
		
		if response != gtk.RESPONSE_YES:
			return
		page = self.ntb_tracks.get_current_page()	
		self.ntb_tracks.remove_page(page)
		self.pat.del_track(track)
		page = self.ntb_tracks.get_current_page()	
		self.tw.load_track(self.pat.get_tracks()[page])
		self.controller_editor_widget.redraw()
		self.pitchbend_editor_widget.redraw()
		self.container.save_state = False
		
	def nbt_tracks_switch_page(self, notebook, page, page_num, data):
		self.tw.load_track(self.pat.get_tracks()[page_num])
		#Dirty trick to avoid an error when controller widget still not loaded
		try:
			self.controller_editor_widget.redraw()
			self.pitchbend_editor_widget.redraw()
		except:
			pass
		#Nasty grab focus for tabs.
		gobject.timeout_add(0,self.tw.grab_focus)
