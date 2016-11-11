"""
This is the track widget, it paints the piano roll and the controls inside
the tracks tab for each pattern.
"""

import gtk

from PianoRollWidget import (
    PianoRollWidget,
    VIRTUAL_KEYBOARD,
    KEY_WIDTH, KEY_HEIGHT, KEY_SPACE,
    BEAT_WIDTH, TICKS_PER_BEAT,
    CURSOR_WIDTH, CURSOR_HEIGHT
)

class TrackWidget:
    """
    Track widget object
    Contains all the controls for a track. Most of the work is done by the
    PianoRollWidget included as piano_roll and many controls just tweak 
    piano_roll's attributes.
    """

    def __init__(self, track, container):
        
        #Parent object
        self.container = container

        #Player Object
        self.player = self.container.container.player_pattern

        #Pattern data
        self.pat = self.container.pat
                
        #Track data
        self.track = track
        
        self.window = self.container.window
        
        #HERE WE START DRAWING THE USER INTERFACE
        self.vbox = gtk.VBox(False,0)

        hbox_menu = gtk.HBox(False,0)
        
        btn_play = gtk.Button('Play')
        btn_play.connect('clicked', self.btn_play_clicked)
        btn_play.show()
        hbox_menu.pack_start(btn_play, False, False, 2)
        
        btn_stop = gtk.Button('Stop')
        btn_stop.connect('clicked', self.btn_stop_clicked)
        btn_stop.show()
        hbox_menu.pack_start(btn_stop, False, False, 2)

        #Grid Length
        lbl_grid = gtk.Label("Grid:")
        lbl_grid.show()
        hbox_menu.pack_start(lbl_grid, False, False, 0)
        self.cbo_grid = gtk.combo_box_new_text()
        for t in ['1/1', '1/2', '1/3', '1/4', '1/6', '1/8']: self.cbo_grid.append_text(t)
        self.cbo_grid.set_active(0)
        self.cbo_grid.connect('changed', self.cbo_grid_changed)
        self.cbo_grid.show()
        hbox_menu.pack_start(self.cbo_grid, False, False, 4)        
        
        #Step Length
        lbl_step = gtk.Label("Step:")
        lbl_step.show()
        hbox_menu.pack_start(lbl_step, False, False, 0)
        self.cbo_step= gtk.combo_box_new_text()
        for i in range(1,16): self.cbo_step.append_text(str(i))
        self.cbo_step.set_active(0)
        self.cbo_step.connect('changed', self.cbo_step_changed)
        self.cbo_step.show()
        hbox_menu.pack_start(self.cbo_step, False, False, 4)        
        
        #Octave
        lbl_oct = gtk.Label("Octave:")
        lbl_oct.show()
        hbox_menu.pack_start(lbl_oct, False, False, 0)
        self.cbo_oct = gtk.combo_box_new_text()
        for t in ['3', '2', '1', '0', '-1', '-2', '-3']: self.cbo_oct.append_text(t)
        self.cbo_oct.set_active(3)
        self.cbo_oct.connect('changed', self.cbo_oct_changed)
        self.cbo_oct.show()
        hbox_menu.pack_start(self.cbo_oct, False, False, 4)        
        
        #Volume
        lbl_vol = gtk.Label("Volume:")
        lbl_vol.show()
        hbox_menu.pack_start(lbl_vol, False, False, 0)
        self.cbo_vol = gtk.combo_box_new_text()
        for t in ['Fixed 1', 'Fixed 2', 'Fixed 3', 'Fixed 4', 'Fixed 5', 'Fixed 6', 'Fixed 7', 'Fixed 8', 'Free']: self.cbo_vol.append_text(t)
        self.cbo_vol.set_active(7)
        self.cbo_vol.connect('changed', self.cbo_vol_changed)
        self.cbo_vol.show()
        hbox_menu.pack_start(self.cbo_vol, False, False, 4)        

        #Scale
        lbl_scale = gtk.Label("Scale:")
        lbl_scale.show()
        hbox_menu.pack_start(lbl_scale, False, False, 0)
        self.cbo_scale = gtk.combo_box_new_text()
        for t in ['Free', 'C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']: self.cbo_scale.append_text(t)
        self.cbo_scale.set_active(0)
        self.cbo_scale.connect('changed', self.cbo_scale_changed)
        self.cbo_scale.show()
        hbox_menu.pack_start(self.cbo_scale, False, False, 4)        

        #ScaleVar
        self.cbo_scale_var = gtk.combo_box_new_text()
        for t in ['Maj', 'Min']: self.cbo_scale_var.append_text(t)
        self.cbo_scale_var.set_active(0)
        self.cbo_scale_var.connect('changed', self.cbo_scale_var_changed)
        self.cbo_scale_var.show()
        hbox_menu.pack_start(self.cbo_scale_var, False, False, 4)        

        self.chk_recording = gtk.CheckButton("Rec")
        self.chk_recording.set_active(True)
        self.chk_recording.connect("toggled", self.chk_recording_toggled)
        self.chk_recording.show()
        hbox_menu.pack_start(self.chk_recording, False, False, 4)        

        self.chk_mono = gtk.CheckButton("Mono")
        self.chk_mono.set_active(False)
        self.chk_mono.connect("toggled", self.chk_mono_toggled)
        self.chk_mono.show()
        hbox_menu.pack_start(self.chk_mono, False, False, 4)        
        
        self.chk_mute_track = gtk.CheckButton("Mute")
        self.chk_mute_track.set_active(not self.track.enabled)
        self.chk_mute_track.connect("toggled", self.chk_mute_track_toggled)
        self.chk_mute_track.show()
        hbox_menu.pack_start(self.chk_mute_track, False, False, 4)        
        
        hbox_menu.show()
        
        self.vbox.pack_start(hbox_menu, False, False, 0)

        #Box for elements
        self.piano_roll = PianoRollWidget(self)

        """
        self.area_piano_sw = piano_roll.keyboard_sw
        self.area_piano = piano_roll.keyboard_area
        self.sw = piano_roll.notes_sw
        self.area = piano_roll.notes_area

        """

        self.piano_roll.show()

        self.vbox.pack_start(self.piano_roll, True, True, 0)

        self.vbox.show()
        
        #Start with focus on the piano roll
        self.piano_roll.notes_area.grab_focus()

    #Retrieve the widget
    def get(self):
        return self.vbox
        
    #Record checkbox clicked Event
    def chk_recording_toggled(self, widget, data=None):
        self.piano_roll.recording =  self.chk_recording.get_active()
        self.piano_roll.notes_area.grab_focus()
        
    #Monophonic record checkbox clicked Event
    def chk_mono_toggled(self, widget, data=None):
        self.piano_roll.rec_mono =  self.chk_mono.get_active()
        self.piano_roll.notes_area.grab_focus()
    
    #Mute checkbox clicked Event
    def chk_mute_track_toggled(self, widget, data=None):
        if widget.get_active():
            self.track.disable()
        else:
            self.track.enable()
        self.piano_roll.notes_area.grab_focus()

    #Play button clicked Event
    def btn_play_clicked(self, widget):
        self.player.set_pos(self.piano_roll.cursor_pos)
        self.player.play(self.pat, self.container.container.song.bpm, True)
        self.piano_roll.notes_area.grab_focus()        
    
    #Stop button clicked Event
    def btn_stop_clicked(self, widget):
        if self.player.playing():
            self.player.stop()

            #Complete cursor movement.
            if (self.piano_roll.cursor_pos % self.piano_roll.note_size):
                self.piano_roll.move_cursor(self.piano_roll.cursor_pos + self.piano_roll.note_size - (self.piano_roll.cursor_pos % self.piano_roll.note_size))
            else:
                self.piano_roll.move_cursor(self.piano_roll.cursor_pos)

            self.piano_roll.notes_area.grab_focus()
    
    #Grid size changed Event
    def cbo_grid_changed(self, widget, data=None):
        widths = (1, 2, 3, 4, 6, 8)
        self.piano_roll.grid_tick = widths[widget.get_active()]
        
        self.piano_roll.note_size = TICKS_PER_BEAT / self.piano_roll.grid_tick

        if (self.piano_roll.cursor_pos % self.piano_roll.note_size) and not self.player.playing():
            self.piano_roll.move_cursor(self.piano_roll.cursor_pos - (self.piano_roll.cursor_pos % self.piano_roll.note_size))

        self.piano_roll.paint_roll()
        self.piano_roll.notes_area.grab_focus()
    
    #Step size changed Event
    def cbo_step_changed(self, widget, data=None):
        self.piano_roll.step_size = int(widget.get_active())+1
        self.piano_roll.paint_roll()
        self.piano_roll.notes_area.grab_focus()

    #Octave changed Event
    def cbo_oct_changed(self, widget, data=None):
        self.piano_roll.octave = 12 * -(widget.get_active()-3)
        self.piano_roll.notes_area.grab_focus()

    #Volume changed Event
    def cbo_vol_changed(self, widget, data=None):
        if widget.get_active() < 7:
            self.piano_roll.volume = 16 * (widget.get_active()+1) - 1
        else:
            self.piano_roll.volume = 127

        if self.piano_roll.recording:
            self.piano_roll.vol_selection()
        
        self.piano_roll.notes_area.grab_focus()

    #Scale note changed Event
    def cbo_scale_changed(self, widget, data=None):
        self.piano_roll.scale = widget.get_active()
        self.piano_roll.notes_area.grab_focus()

    #Scale variant changed Event
    def cbo_scale_var_changed(self, widget, data=None):
        self.piano_roll.scale_var = widget.get_active()
        self.piano_roll.notes_area.grab_focus()

    def load_track(self, track):
        self.track = track
        self.chk_mute_track.set_active(not self.track.enabled)
        self.piano_roll.load_track(self)
        self.piano_roll.paint_roll()
        
    def grab_focus(self):
        self.piano_roll.notes_area.grab_focus()
        return False
