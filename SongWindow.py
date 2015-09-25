#Main widget, with the song window (main window), player thread, etc...

import gtk
import time
import midifile
import gobject

import Config
from FileFormat import DSeq1
from Song import Song
from Pattern import Pattern

from Connections import Connections
from PlayerThread import PlayerThread
from PlayerThreadSong import PlayerThreadSong

from PatternWindow import PatternWindow

VERSION = '0.4.0'
gtk.gdk.threads_init()

class SongWindow(gtk.Window):

	def __init__(self):
		gtk.Window.__init__(self)

		self.conf = Config.Config()

		#MIDI Connections Object
		self.conn = Connections()
		if 'input_device' in self.conf.value:
			self.conn.change_input_device(self.conf.value['input_device'])
			
		self.player = PlayerThreadSong(self.conn)
		self.player.start()
		self.player_pattern = PlayerThread(self.conn)
		self.player_pattern.start()

		self.set_title("Desfonema Sequencer " + VERSION)
		self.set_icon_from_file("dseq.png")
		self.filename = ''

		self.song = Song()

		self.set_default_size(900,500)
		self.set_size_request(900,500)
		
		#Close, destroy!
		self.connect("delete_event", self.quit_program)

		# A vBox to contain my own drawing and a menu
		vbox = gtk.VBox(False, 0)

		#File Menu (much like seq24)
		file_menu = gtk.MenuItem("_File")

		# We create the menu widget
		menu = gtk.Menu()
		
		#And keyboard Shortcuts
		accel_group = gtk.AccelGroup()
		self.add_accel_group(accel_group)

		#New Menu
		menu_items = gtk.ImageMenuItem(gtk.STOCK_NEW)
		menu_items.connect('activate', self.new_file)
		menu_items.add_accelerator("activate", accel_group, ord('N'), gtk.gdk.CONTROL_MASK, gtk.ACCEL_VISIBLE)
		menu.append(menu_items)
		menu_items.show()

		#Open Menu
		menu_items = gtk.ImageMenuItem(gtk.STOCK_OPEN)
		menu_items.connect('activate', self.menu_open)
		menu_items.add_accelerator("activate", accel_group, ord('O'), gtk.gdk.CONTROL_MASK, gtk.ACCEL_VISIBLE)
		menu.append(menu_items)
		menu_items.show()

		separator = gtk.SeparatorMenuItem()
		separator.show()
		menu.append(separator)

		#Save Menu
		menu_items = gtk.ImageMenuItem(gtk.STOCK_SAVE)
		menu_items.connect('activate', self.menu_save)
		menu_items.add_accelerator("activate", accel_group, ord('S'), gtk.gdk.CONTROL_MASK, gtk.ACCEL_VISIBLE)
		menu.append(menu_items)
		menu_items.show()

		#Save As Menu
		menu_items = gtk.ImageMenuItem(gtk.STOCK_SAVE_AS)
		menu_items.connect('activate', self.menu_save_as)
		menu_items.add_accelerator("activate", accel_group, ord('A'), gtk.gdk.CONTROL_MASK, gtk.ACCEL_VISIBLE)
		menu.append(menu_items)
		menu_items.show()

		#Import Patterns
		menu_items = gtk.MenuItem('_Import Patterns...')
		menu_items.connect('activate', self.menu_import_patterns)
		menu_items.add_accelerator("activate", accel_group, ord('I'), gtk.gdk.CONTROL_MASK, gtk.ACCEL_VISIBLE)
		menu.append(menu_items)
		menu_items.show()

		#Seq24 Import
		menu_items = gtk.MenuItem('Import Seq24 Sequences...')
		menu_items.connect('activate', self.menu_import_seq24)
		menu.append(menu_items)
		menu_items.show()

		separator = gtk.SeparatorMenuItem()
		separator.show()
		menu.append(separator)

		#Quit Menu
		menu_items = gtk.ImageMenuItem(gtk.STOCK_QUIT)
		menu_items.connect('activate', self.quit_program)
		menu.append(menu_items)
		menu_items.show()

		file_menu.set_submenu(menu)
		file_menu.show()

		#Song Menu 
		song_menu = gtk.MenuItem("_Song")

		# We create the menu widget
		menu = gtk.Menu()

		#Add Pattern Menu
		menu_items = gtk.MenuItem('Add _Pattern')
		menu_items.connect('activate', self.add_pattern)
		menu_items.add_accelerator("activate", accel_group, ord('P'), gtk.gdk.CONTROL_MASK, gtk.ACCEL_VISIBLE)
		menu.append(menu_items)
		menu_items.show()

		#Paste Pattern Menu
		menu_items = gtk.MenuItem('Paste Pattern')
		menu_items.connect('activate', self.paste_pattern)
		menu_items.add_accelerator("activate", accel_group, ord('V'), gtk.gdk.CONTROL_MASK, gtk.ACCEL_VISIBLE)
		menu.append(menu_items)
		menu_items.show()

		#Add Channel Menu
		menu_items = gtk.MenuItem('Add _Channel')
		menu_items.connect('activate', self.add_channel)
		menu_items.add_accelerator("activate", accel_group, ord('C'), gtk.gdk.CONTROL_MASK, gtk.ACCEL_VISIBLE)
		menu.append(menu_items)
		#menu_items.show()

		song_menu.set_submenu(menu)
		song_menu.show()
		
		# Create a menu-bar to hold the menus and add it to our main window
		menu_bar = gtk.MenuBar()
		menu_bar.append(file_menu)
		menu_bar.append(song_menu)
		menu_bar.show()
		
		#Add menubar to the VBox
		vbox.pack_start(menu_bar, False, False, 2)

		#ToolBox

		hbox_toolbox = gtk.HBox(False, 0)

		#Pattern Tools
		btn_create_pattern = gtk.Button('Add Pattern')
		btn_create_pattern.connect("clicked", self.add_pattern)
		btn_create_pattern.show()
		hbox_toolbox.pack_start(btn_create_pattern, False, False, 0)

		btn_paste_pattern = gtk.Button('Paste Pattern')
		btn_paste_pattern.connect("clicked", self.paste_pattern)
		btn_paste_pattern.show()
		hbox_toolbox.pack_start(btn_paste_pattern, False, False, 0)

		#BPM/Position
		lbl_bpm = gtk.Label("Bpm:")
		lbl_bpm.show()
		hbox_toolbox.pack_start(lbl_bpm, False, False, 0)
		self.adj_bpm = gtk.Adjustment(value=self.song.get_bpm(), lower=45, upper=240, step_incr=1)
		self.adj_bpm.connect("value_changed", self.adj_bpm_changed)
		spn_bpm = gtk.SpinButton(self.adj_bpm, 0, 0)
		spn_bpm.show()		
		hbox_toolbox.pack_start(spn_bpm, False, False, 4)

		lbl_pos = gtk.Label("Pos:")
		lbl_pos.show()
		hbox_toolbox.pack_start(lbl_pos, False, False, 0)
		self.adj_pos = gtk.Adjustment(value=self.player.get_pos(), lower=0, upper=999, step_incr=1)
		self.adj_pos.connect("value_changed", self.adj_pos_changed)
		spn_pos = gtk.SpinButton(self.adj_pos, 0, 0)
		spn_pos.show()		
		hbox_toolbox.pack_start(spn_pos, False, False, 4)

		btn_play_song = gtk.Button('Play Song')
		btn_play_song.connect("clicked", self.btn_play_song_clicked)
		btn_play_song.show()
		
		hbox_toolbox.pack_start(btn_play_song, False, False, 0)

		hbox_toolbox.show()
		
		vbox.pack_start(hbox_toolbox, False, False, 2)

		# Song items (patterns and channels)
		hpaned_song = gtk.HPaned()

		# Patterns
		frame = gtk.Frame('Patterns')
		frame.set_size_request(700,400)
		#Scroll, to see complete Pattern List
		sw = gtk.ScrolledWindow()

		self.vbox_patterns = gtk.VBox(False, 0)
		self.vbox_patterns.show()

		sw.add_with_viewport(self.vbox_patterns)
		
		sw.show()
		
		frame.add(sw)
		frame.show()
		hpaned_song.add1(frame)
		
		# Channels
		frame = gtk.Frame('Song')
		vbox_channels = gtk.VBox(False,0)

		#Scroll, to see complete Song
		sw = gtk.ScrolledWindow()

		self.hbox_channels = gtk.HBox(False, 0)
		self.hbox_channels.show()
		
		sw.add_with_viewport(self.hbox_channels)
		
		sw.show()
		vbox_channels.pack_start(sw, True, True, 0)
		
		vbox_channels.show()

		frame.add(vbox_channels)
		frame.show()
		
		hpaned_song.add2(frame)

		hpaned_song.show()
		vbox.pack_start(hpaned_song, True, True, 0)


		channels = self.song.get_channels()
		if len(channels): 
			channel = channels[0]
		else:
			channel = self.song.add_channel()
		
		ChannelWidget(self, channel)

		channels = self.song.get_channels()

		if len(channels) == 0:
			return
			
		channel = channels[0]

		#self.player.set_pos(int(self.adj_pos.get_value()))
		self.player.set_data(channel)
		self.player.set_bpm(self.song.get_bpm())
		#self.playing_pos = gobject.timeout_add(500, self.update_playing_pos)

		vbox.show()
		self.add(vbox)
		self.save_state = True
		
	def menu_open(self, widget, data=None):
		if self.save_state:
			response = gtk.RESPONSE_YES
		else:
			dialog = gtk.MessageDialog(self, gtk.DIALOG_MODAL , gtk.MESSAGE_WARNING, gtk.BUTTONS_YES_NO,
					"Open another song?\nUnsaved changes will be lost.")

			response = dialog.run()
			dialog.destroy()

		if response == gtk.RESPONSE_YES:
			filename = self.file_dialog('open')
			if filename:
				#Clean previous data
				self.vbox_patterns.foreach(self.vbox_patterns.remove)
					
				dseq = DSeq1()
				self.song = dseq.open(filename)
				self.adj_bpm.set_value(self.song.get_bpm())

				for pattern in self.song.get_patterns():
					PatternWidget(self, pattern)
					for track in pattern.get_tracks():
						self.conn.create_port(track.synth)

				if len(self.song.get_channels()) == 0:
					self.song.add_channel()
				self.refresh_channels()

				channels = self.song.get_channels()

				if len(channels) > 0:
					channel = channels[0]
					self.player.set_data(channel)
					self.player.set_bpm(self.song.get_bpm())
						
				self.filename = filename
				self.save_state = True
		
	def menu_save(self, widget, data=None):
		if self.filename:
			dseq = DSeq1()
			dseq.save(self.filename, self.song)
			self.save_state = True
		else:
			filename = self.file_dialog('save')
			if filename:
				if filename[-5:] != '.dseq':
					filename = filename + '.dseq'
				self.filename = filename
				dseq = DSeq1()
				dseq.save(self.filename, self.song)
				self.save_state = True
		
	def menu_save_as(self, widget, data=None):
		filename = self.file_dialog('saveas')
		if filename:
			if filename[-5:] != '.dseq':
				filename = filename + '.dseq'
			self.filename = filename
			dseq = DSeq1()
			dseq.save(self.filename, self.song)
			self.save_state = True
			
	def menu_import_patterns(self, widget, data=None):
		filename = self.file_dialog('import')
		if filename:				
			dseq = DSeq1()
			imported_song = dseq.open(filename)
			
			for pattern in imported_song.get_patterns():
				self.song.add_pattern(pattern)
				PatternWidget(self, pattern)
				
			self.filename = filename
			self.refresh_channels()
			self.save_state = False

			
	def menu_import_seq24(self, widget, data=None):
		


		filename = self.file_dialog('import_seq24')
		if filename:				
			imported_song = Song()
			event_handler = midifile.NoteOnPrinter()
			event_handler.set_song(imported_song)
			midi_in = midifile.MidiInFile(event_handler, filename)
			midi_in.read()

			for pattern in imported_song.get_patterns():
				self.song.add_pattern(pattern)
				PatternWidget(self, pattern)
				
			self.filename = filename
			self.refresh_channels()
			self.save_state = False
		
	def file_dialog(self, data=None):
		if data == "open":
			title = 'Open...'
			action = gtk.FILE_CHOOSER_ACTION_OPEN
		elif data == "save":
			title = 'Save...'
			action = gtk.FILE_CHOOSER_ACTION_SAVE
		elif data == 'saveas':
			title = 'Save As...'
			action = gtk.FILE_CHOOSER_ACTION_SAVE
		elif data == "import":
			title = 'Import Patterns From...'
			action = gtk.FILE_CHOOSER_ACTION_OPEN
		elif data == "import_seq24":
			title = 'Import Patterns From Seq24'
			action = gtk.FILE_CHOOSER_ACTION_OPEN
		
		if action == gtk.FILE_CHOOSER_ACTION_OPEN:
			dialog = gtk.FileChooserDialog(title, None, action,
							(gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL, gtk.STOCK_OPEN, gtk.RESPONSE_OK))
		else:
			dialog = gtk.FileChooserDialog(title, None, action,
							(gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL, gtk.STOCK_SAVE, gtk.RESPONSE_OK))
			
		dialog.set_default_response(gtk.RESPONSE_OK)
		
		if 'last_dir' in self.conf.value:
			dialog.set_current_folder(self.conf.value['last_dir'])

		filter = gtk.FileFilter()
		if data != "import_seq24":
			filter.set_name("Desfonema Sequence")
			filter.add_pattern("*.dseq")
		else:
			filter.set_name("Seq24 Sequence")
			filter.add_pattern("*.s24")
			filter.add_pattern("*.seq24")
			filter.add_pattern("*.mid")
		
		dialog.add_filter(filter)

		filter = gtk.FileFilter()
		filter.set_name("All files")
		filter.add_pattern("*")
		dialog.add_filter(filter)

		response = dialog.run()
		
		filename = ''
		if response == gtk.RESPONSE_OK:
			filename = dialog.get_filename()
			self.conf.value['last_dir'] = dialog.get_current_folder()
			
		dialog.destroy()
		
		return filename
		
	def quit_program(self, widget, data=None):
		if self.save_state:
			response = gtk.RESPONSE_YES
		else:
			dialog = gtk.MessageDialog(self, gtk.DIALOG_MODAL , gtk.MESSAGE_WARNING, gtk.BUTTONS_YES_NO,
					"Do you really wanna quit?\nUnsaved changes will be lost.")
					
			response = dialog.run()
			dialog.destroy()
		
		if response == gtk.RESPONSE_YES:
			self.player.quit()
			self.conf.save()
			gtk.main_quit()
			return False
		else:
			return True

	def new_file(self, widget, data=None):
		if self.save_state:
			response = gtk.RESPONSE_YES
		else:
			dialog = gtk.MessageDialog(self, gtk.DIALOG_MODAL , gtk.MESSAGE_WARNING, gtk.BUTTONS_YES_NO,
					"Create new song?\nUnsaved changes will be lost.")
					
			response = dialog.run()
			dialog.destroy()
		
		if response == gtk.RESPONSE_YES:
			self.vbox_patterns.foreach(self.vbox_patterns.remove)
			self.song = Song()
			self.song.add_channel()
			self.refresh_channels()
			self.filename = ''
			self.save_state = True
			

	def add_pattern(self, widget, data=None):
		if data == None:
			pattern = self.song.add_pattern()
			pattern.set_len(8)
			pattern.add_track()
			pw = PatternWindow(self, pattern)
			pw.show()
			pw.maximize()
		else:
			pattern = data
			
		PatternWidget(self, pattern)
		self.refresh_channels()
		self.save_state = False

	def add_channel(self, widget, data=None):
		if data == None:
			channel = self.song.add_channel()
		else:
			channel = data
			
		ChannelWidget(self, channel)
		self.save_state = False
		
	def adj_bpm_changed(self, widget, data= None):
		self.song.set_bpm(widget.get_value())
		self.player.set_bpm(self.song.get_bpm())
		self.save_state = False

	def adj_pos_changed(self, widget, data= None):
		self.player.set_pos(int(self.adj_pos.get_value()))

	def btn_play_song_clicked(self, widget, data=None):
		
		if self.player.playing():
			self.player.stop()
			if self.playing_pos:
				gobject.source_remove(self.playing_pos)			
		else:
			channels = self.song.get_channels()

			if len(channels) == 0:
				return
				
			channel = channels[0]

			#self.player.set_pos(int(self.adj_pos.get_value()))
			self.player.set_data(channel)
			self.player.set_bmp(self.song.get_bpm())
			self.playing_pos = gobject.timeout_add(500, self.update_playing_pos)
		
	def update_playing_pos(self):
		pos = self.player.get_pos()
		self.adj_pos.set_value(int(pos))
		return True
		
	def paste_pattern(self, widget, data=None):
		clipboard = gtk.clipboard_get(gtk.gdk.SELECTION_CLIPBOARD)
		clipboard.request_text(self.paste_pattern_clipboard_text_received)
		
    # signal handler called when the clipboard returns text data
	def paste_pattern_clipboard_text_received(self, clipboard, text, data):
		if not text or text == '':
			return
			
		lines = text.split("\n")
		if not len(lines):
			return
			
		if lines[0] != 'Pattern':
			return

		pattern = Pattern()
		self.song.add_pattern(pattern)

		level = 0
		for line in lines:
			if line == "Pattern":
				level = 1

			if line == "Track":
				track = pattern.add_track()
				level = 2
			
			if line == "Notes":
				level = 3

			if level == 1:
				#On Pattern Data
				if line[:5] == "Num: ":
					pattern.set_num(int(line[5:]))
				elif line[:5] == "Len: ":
					pattern.set_len(int(line[5:]))
				elif line[:6] == "Name: ":
					pattern.set_name(line[6:])
			elif level == 2:
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

		pattern.set_name("Copy of " + pattern.get_name())
		PatternWidget(self, pattern)
		self.refresh_channels()
		self.save_state = False
		return
		
	def refresh_channels(self):
		self.hbox_channels.foreach(self.hbox_channels.remove)
		for channel in self.song.get_channels():
			ChannelWidget(self, channel)		

class PatternWidget:
	def __init__(self, container, pattern):
		
		self.container = container
		self.synth_list = self.container.conn.get_output_list()

		hbox = gtk.HBox(False,0)

		separator = gtk.HSeparator()
		separator.show()

		btn_pattern_edit = gtk.Button("Edit Pattern")
		btn_pattern_edit.connect("clicked", self.btn_pattern_edit_clicked, pattern)
		btn_pattern_edit.show()
		hbox.pack_start(btn_pattern_edit, False, False, 4)

		btn_pattern_copy = gtk.Button("Copy Pattern")
		btn_pattern_copy.connect("clicked", self.btn_pattern_copy_clicked, pattern)
		btn_pattern_copy.show()
		hbox.pack_start(btn_pattern_copy, False, False, 4)
		
		btn_pattern_del = gtk.Button("Del Pattern")
		btn_pattern_del.connect("clicked", self.btn_pattern_del_clicked, (pattern, hbox, separator))
		btn_pattern_del.show()
		hbox.pack_start(btn_pattern_del, False, False, 4)
		
		#Pattern Name
		lbl_pattern_name = gtk.Label('Name:')
		lbl_pattern_name.show()
		hbox.pack_start(lbl_pattern_name, False, False, 4)
		txt_pattern_name = gtk.Entry()
		txt_pattern_name.set_text(pattern.get_name())
		txt_pattern_name.set_max_length(30)
		txt_pattern_name.connect("changed", self.txt_pattern_name_changed, pattern)
		txt_pattern_name.connect("focus-out-event", self.txt_pattern_name_focus_out)
		txt_pattern_name.show()
		hbox.pack_start(txt_pattern_name, True, True, 4)

		#Play Pattern
		btn_play = gtk.Button("Play")
		btn_play.connect("clicked", self.btn_play_clicked, pattern)
		btn_play.show()
		hbox.pack_start(btn_play, False, False, 4)
				
		hbox.show()
		self.container.vbox_patterns.pack_start(hbox, False, False, 4)
		self.container.vbox_patterns.pack_start(separator, False, False, 4)
		
	def btn_pattern_del_clicked(self, widget, data=None):
		(pattern, hbox, separator) = data

		dialog = gtk.MessageDialog(self.container, gtk.DIALOG_MODAL , gtk.MESSAGE_WARNING, gtk.BUTTONS_YES_NO,
				"Delete pattern " + pattern.get_name() + "?")
				
		response = dialog.run()
		dialog.destroy()
		
		if response != gtk.RESPONSE_YES:
			return
			
		self.container.vbox_patterns.remove(separator)
		self.container.vbox_patterns.remove(hbox)
		self.container.song.del_pattern(pattern)
		self.container.refresh_channels()
		self.container.save_state = False

	def btn_pattern_copy_clicked(self, widget, data=None):
		pattern = data
	
		text = ''
		text += "Pattern\n"
		text += "Num: " + str(pattern.get_num()) + "\n"
		text += "Len: " + str(pattern.get_len()) + "\n"
		text += "Name: " + pattern.get_name() + "\n"
		text += "Enabled: " + str(pattern.get_enabled()) + "\n"
		
		for track in pattern.get_tracks():
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
		text += "EndPattern\n"
		
		clipboard = gtk.clipboard_get(gtk.gdk.SELECTION_CLIPBOARD)
		clipboard.set_text(text)
		
	def btn_pattern_edit_clicked(self, widget, data=None):
		pw = PatternWindow(self.container, data)
		pw.show()
		pw.maximize()


	def txt_pattern_name_changed(self, widget, data=None):
		data.set_name(widget.get_text())
		self.container.save_state = False

	def txt_pattern_name_focus_out(self,widget, event):
		self.container.refresh_channels()
		
		
	def btn_play_clicked(self, widget, data=None):
		self.container.player.set_pos(0)
		#self.container.player.play(data, self.container.song.get_bpm())

class ChannelWidget:
	def __init__(self, container, channel):
		vbox = gtk.VBox(False,0)
		
		hbox_toolbox = gtk.HBox(False,0)
		
		btn_add_pattern = gtk.Button('Add')
		btn_add_pattern.connect('clicked', self.add_pattern, (container, vbox, channel))
		btn_add_pattern.show()
		hbox_toolbox.pack_start(btn_add_pattern, True, True, 0)

		#btn_play_channel = gtk.Button('Play')
		#btn_play_channel.connect('clicked', self.btn_play_channel_clicked, (container, channel))
		#btn_play_channel.show()
		
		#hbox_toolbox.pack_start(btn_play_channel, True, True, 0)
		
		hbox_toolbox.show()
		
		vbox.pack_start(hbox_toolbox, False, False, 0)
		
		vbox.show()
		container.hbox_channels.pack_start(vbox, True, True, 2)
		
		i = 0
		for pattern in channel.get_patterns():
			ChannelPatternWidget(container, vbox, channel, None, pattern, i)
			i = i + 1
	
	def add_pattern(self, widget, data = None):
		(container, vbox, channel) = data
		patterns = container.song.get_patterns()
		if len(patterns):
			ChannelPatternWidget(container, vbox, channel, None, None, len(channel.get_patterns()))

class ChannelPatternWidget(gtk.HBox):
	def __init__(self, container, vbox, channel, after=None, pattern=None, pos=0):

		gtk.HBox.__init__(self,False,0)
	
		self.lbl_pos = gtk.Label(str(pos))
		self.lbl_pos.show()
		self.pack_start(self.lbl_pos, True, True, 0)
	
		patterns = container.song.get_patterns()
		cbo_patterns = gtk.combo_box_new_text()
		self.container = container
		for pat in patterns:
			cbo_patterns.append_text(pat.get_name())
			if pattern != None:
				if pattern == pat:
					cbo_patterns.set_active(patterns.index(pat))
					self.pattern = pattern
					
		if pattern == None:
			if len(patterns):
				cbo_patterns.set_active(0)
				self.pattern = patterns[0]
			else:
				self.pattern = None
		
		cbo_patterns.connect('changed', self.cbo_patterns_changed, (container, channel, vbox))
		
		cbo_patterns.show()
		self.pack_start(cbo_patterns, True, True, 0)

		vbox_controls = gtk.VBox(False, 0)
		
		btn_del = gtk.Button('Del')
		btn_del.connect('clicked', self.btn_del_clicked, (vbox, channel))
		btn_del.show()
		vbox_controls.pack_start(btn_del, True, True, 0)
		
		btn_ins = gtk.Button('Ins')
		btn_ins.connect('clicked', self.btn_ins_clicked, (container, vbox, channel))
		btn_ins.show()
		vbox_controls.pack_start(btn_ins, True, True, 0)
		
		vbox_controls.show()
		self.pack_start(vbox_controls, True, True, 0)
		
		self.show()
		
		if after == None:
			vbox.pack_start(self, False, False, 0)
			
			#New Pattern
			if pattern == None:
				channel.add_pattern(self.pattern)
		else:
			i = 0
			for widget in vbox.get_children():
				if widget.get_name() == "ChannelPatternWidget":
					widget.lbl_pos.set_text(str(i))
					if widget == after:
						i = i + 1
						vbox.pack_start(self, False, False, 0)
						vbox.reorder_child(self, i+1)
						channel.insert_pattern(self.pattern, i)
						self.lbl_pos.set_text(str(i))

					i = i + 1

	def get_name(self):
		return "ChannelPatternWidget"
		
	def btn_del_clicked(self, widget, data=None):
		(vbox, channel) = data

		self.container.save_state = False

		i = 0
		for widget in vbox.get_children():
			if widget == self:
				channel.remove_pattern(i-1)
			i = i + 1
		vbox.remove(self)
	
	def btn_ins_clicked(self, widget, data=None):
		(container, vbox, channel) = data
		ChannelPatternWidget(container, vbox, channel, self, self.pattern)
		self.container.save_state = False
		
	def cbo_patterns_changed(self, widget, data=None):
		(container, channel, vbox) = data
		self.container.save_state = False

		patterns = container.song.get_patterns()
		self.pattern = patterns[widget.get_active()]

		i = 0
		for widget in vbox.get_children():
			if widget == self:
				channel.change_pattern(self.pattern, i-1)
			i = i + 1		
		
