"""
This is the track widget, it paints the piano roll and the controls inside
the tracks tab for each pattern.
"""

import pygtk
import gtk
from gtk import keysyms as key
import time
import gobject

from util import nanosleep
from audio import alsaseq

time.sleep = nanosleep.nanosleep

KEY_WIDTH = 14
KEY_HEIGHT = 7
KEY_SPACE = 1

BEAT_WIDTH = 24
TICKS_PER_BEAT = 24

# My virtual keyboard config
VIRTUAL_KEYBOARD = [
    key.z, key.s, key.x, key.d, key.c, key.v, key.g, key.b, key.h, key.n, key.j, key.m,
    key.q, key._2, key.w, key._3, key.e, key.r, key._5, key.t, key._6, key.y, key._7,
    key.u, key.i, key._9, key.o, key._0
]

SCALE_MAJ = [0,2,4,5,7,9,11]
SCALE_MIN = [0,2,3,5,7,9,11]

EVENT_MODIFIER_NONE = 0
EVENT_MODIFIER_SHIFT = gtk.gdk.SHIFT_MASK
EVENT_MODIFIER_CTRL = gtk.gdk.CONTROL_MASK
EVENT_MODIFIER_CTRL_SHIFT = gtk.gdk.SHIFT_MASK | gtk.gdk.CONTROL_MASK

class KeyEventHook:
    """
    Define a Keyboard event hook when keys in property keys are pressed
    and all modifiers are present.
    """

    modifiers = EVENT_MODIFIER_NONE
    keys = []

    def activate(self, widget, keycode):
        """
        Here is the code when this is activated (key down)
        :param widget: is the widget that received the event
        :param keycode: key code
        """
        pass

    def deactivate(self, widget, keycode):
        """
        Here is the code when this is deactivated (key up).
        :param widget: is the widget that received the event
        :param keycode: key code
        """
        pass

class KeyMoveCursor(KeyEventHook):
    """
    Move cursor with the keyboard
    """
    keys = [key.Left, key.Right, key.Up, key.Down]

    def activate(self, widget, keycode):
        #Move cursor
        if keycode in [key.Left, key.Right]:
            widget.move_cursor(
                widget.cursor_pos +
                (widget.cursor_pos % widget.note_size or widget.note_size) *
                (1 if keycode == key.Right else -1)
            )
            selection_y = widget.selection_y
        else:
            selection_y = widget.selection_y + (1 if keycode == key.Up else -1)

        widget.update_selection(widget.cursor_pos, selection_y, 1, 1)
                    
class TrackWidget:
    """
    Track widget object
    """

    # Which events are handled by hooks for the piano roll area
    piano_roll_key_event_hooks = [
        KeyMoveCursor()
    ]

    def __init__(self, track, container):
        
        #Parent object
        self.container = container

        #Player Object
        self.player = self.container.container.player_pattern
                
        #Here i put some variables needed for edition and playing
        
        #Grid tick
        self.grid_tick = 1
        # Note size is TICKS_PER_BEAT/self.grid_tick. Divide by 1... to keep formula present
        self.note_size = TICKS_PER_BEAT / self.grid_tick

        #Step size
        self.step_size = 1
        
        #Pattern data
        self.pat = self.container.pat

        #Record flag
        self.recording = 1

        #Selective deletion flag
        self.deleting = 0
        
        self.volume = 127
        
        self.scale = 0
        self.scale_var = 0
        
        #Track data
        self.track = track
        
        #Virtual Keyboard Status initialized on Zero
        #Used to avoid key repeat and also to count release events for chords
        self.vk_space = 0
        self.vk_status = [0]*len(VIRTUAL_KEYBOARD)
        self.vk_count = 0

        #Octave (for virtual keyboard)
        self.octave = 0

        #Start Reading MIDI Keyboard 
        self.midi_keyboard_listen = 0
        self.midi_keyboard_count = 0
        
        #This handles when a note was pressed (in virt keyb or midi keyb) for note insert in live recording
        self.notes_start_position_velocity = [(-1,0)]*127

        #Cursor position
        self.cursor_pos = 0
        
        #Selection is the tool to move, copy, paste and delete notes
        self.selection_x = 0
        self.selection_y = 60
        self.selection_width = 1
        self.selection_height = 1
        self.selection = []
        self.mouse_selection = 0
        
        #Mouse input variables
        self.mouse_pos = 0
        self.mouse_note = 0
        self.mouse_painting = 0
        
        self.piano_note = 0
        
        #Some calculated values that we use all over this piano roll painting routine
        self.cursor_width = BEAT_WIDTH/TICKS_PER_BEAT + KEY_SPACE
        self.cursor_height = KEY_HEIGHT + KEY_SPACE

        self.gc_foreground = None
        self.gc_background = None
        
        #MIDI Synth Connection        
        self.conn = self.container.container.conn
        
        self.window = self.container.window
        
        #HERE WE START DRAWING THE USER INTERFACE
        #VBox for Toolbar / ScrolledWindow
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
        
        self.chk_mute_track = gtk.CheckButton("Mute")
        self.chk_mute_track.set_active(not self.track.enabled)
        self.chk_mute_track.connect("toggled", self.chk_mute_track_toggled)
        self.chk_mute_track.show()
        hbox_menu.pack_start(self.chk_mute_track, False, False, 4)        
        
        hbox_menu.show()
        
        self.vbox.pack_start(hbox_menu, False, False, 0)

        #Box for elements
        hbox = gtk.HBox(False,0)

        #Scroll, to see complete Piano
        self.area_piano_sw = gtk.ScrolledWindow()
        self.area_piano_sw.set_policy(gtk.POLICY_NEVER, gtk.POLICY_ALWAYS)
        self.area_piano_sw.set_placement(gtk.CORNER_TOP_RIGHT)

        #Piano roll picture
        self.area_piano = gtk.DrawingArea()
        self.area_piano.set_size_request(KEY_WIDTH + KEY_SPACE + KEY_SPACE, 128 * self.cursor_height)
        self.area_piano.show()
        
        self.area_piano_sw.add_with_viewport(self.area_piano)
        hbox.pack_start(self.area_piano_sw, False, False, 0)

        #Scroll, to see complete Piano
        self.sw = gtk.ScrolledWindow()
        
        #Note zone
        self.area = gtk.DrawingArea()
        
        self.area.set_flags(gtk.CAN_FOCUS)
        self.area.set_size_request(self.pat.get_len() * TICKS_PER_BEAT * self.cursor_width + 32, 128 * self.cursor_height)
        self.area.show()
        self.pangolayout = self.area.create_pango_layout("")

        self.sw.add_with_viewport(self.area)
        hbox.pack_start(self.sw, True, True, 0)

        hbox.show()

        self.vbox.pack_start(hbox, True, True, 0)

        self.vbox.show()
        
        #EVENT HANDLING FOR THE PIANO ROLL
        
        self.area_piano.connect("expose-event", self.area_piano_expose_cb)
        self.area_piano.connect("motion_notify_event", self.area_piano_motion_notify)
        self.area_piano.connect("button_press_event", self.area_piano_button_press_event)
        self.area_piano.set_events(
            gtk.gdk.BUTTON_PRESS_MASK | 
            gtk.gdk.BUTTON_RELEASE_MASK |
            gtk.gdk.POINTER_MOTION_MASK )

        self.area.set_events(
            gtk.gdk.BUTTON_PRESS_MASK | 
            gtk.gdk.BUTTON_RELEASE_MASK |
            gtk.gdk.POINTER_MOTION_MASK |
            gtk.gdk.KEY_PRESS_MASK |
            gtk.gdk.KEY_RELEASE_MASK |
            gtk.gdk.FOCUS_CHANGE_MASK |
            gtk.gdk.ENTER_NOTIFY_MASK |
            gtk.gdk.LEAVE_NOTIFY_MASK |
            gtk.gdk.SCROLL_MASK)

        self.area.add_events(gtk.gdk.POINTER_MOTION_MASK)
        
        self.area.set_flags(gtk.CAN_FOCUS)
        #Connect keyboard events
        self.area.connect("key-press-event", self.window_key_press_event)
        self.area.connect("key-release-event", self.window_key_release_event)

        self.area.connect("expose-event", self.area_expose_cb)
        self.area.connect("motion_notify_event", self.area_motion_notify)
        self.area.connect("button_press_event", self.area_button_press_event)
        self.area.connect("button_release_event", self.area_button_release_event)

        self.vadj_piano = self.area_piano_sw.get_vadjustment()
        self.area_piano_sw.show()
        self.hadj = self.sw.get_hadjustment()
        self.vadj = self.sw.get_vadjustment()
        self.adjust = 1

        self.vadj_piano.connect('value_changed', self.area_vertical_value_changed)
        self.vadj.connect('value_changed', self.area_vertical_value_changed)
        self.hadj.connect('value_changed', self.area_horizontal_value_changed)
        self.sw.show()
        
        #Start with focus on the piano roll
        self.area.grab_focus()

    #Retrieve the widget
    def get(self):
        return self.vbox

    def area_horizontal_value_changed(self, adj):
        value = adj.get_value()
        self.container.controller_editor_widget.set_scroll_pos(value)
        self.container.pitchbend_editor_widget.set_scroll_pos(value)

    def area_vertical_value_changed(self, adj):
        value = adj.get_value()
        self.vadj_piano.set_value(value)
        self.vadj.set_value(value)
        
    #Paint Piano Keys on expose event
    def area_piano_expose_cb(self, area, event):
        self.style = self.area_piano.get_style()
        self.gc = self.style.fg_gc[gtk.STATE_NORMAL]

        colormap = self.area_piano.get_colormap()

        color_foreground = colormap.alloc_color('#C0C0C0', True, True)
        self.gc_foreground = self.area_piano.window.new_gc()
        self.gc_foreground.set_foreground(color_foreground)

        color_background = colormap.alloc_color('#FFFFFF', True, True)
        self.gc_background = self.area_piano.window.new_gc()
        self.gc_background.set_foreground(color_background)

        self.area_piano.window.draw_rectangle(self.gc_background, True, 0, 0, KEY_WIDTH + KEY_SPACE + KEY_SPACE, 128 * self.cursor_height)

        for i in range(128):
            self.area_piano.window.draw_rectangle(self.gc, False, 
                        0, i * self.cursor_height, 
                        KEY_WIDTH + KEY_SPACE, self.cursor_height)
            if i % 12 in [5, 7, 10, 0 , 2]:
                self.area_piano.window.draw_rectangle(self.gc, True, 
                            0, i * self.cursor_height + 2, 
                            KEY_WIDTH + KEY_SPACE - 1, KEY_HEIGHT - KEY_SPACE - 1)
        return True

    #Handles mouse movement for the Piano Keys
    def area_piano_motion_notify(self, widget, event):
        note = 128 -  int(event.y / self.cursor_height)

        self.paint_piano_note(self.mouse_note, self.gc_background)

        if event.state & gtk.gdk.BUTTON1_MASK:

            if self.mouse_note != note:
                synth_conn = self.conn.get_port(self.track.get_synth())

                if synth_conn != None: 
                    synth_conn.note_on(note, self.track.get_port(), self.volume)
                    time.sleep(0.025)
                    synth_conn.note_off(note, self.track.get_port())

        self.mouse_note = note
        self.paint_piano_note(self.mouse_note, self.gc_cursor)

    #Handles mouse buttons for Piano Keys
    def area_piano_button_press_event(self, widget, event):
        self.area.grab_focus()

        note = 128 -  int(event.y / self.cursor_height)
        synth_conn = self.conn.get_port(self.track.get_synth())

        if synth_conn != None: 
            synth_conn.note_on(note, self.track.get_port(), self.volume)
            time.sleep(0.025)
            synth_conn.note_off(note, self.track.get_port())

    #Paints a single note in the piano keyboard
    def paint_piano_note(self, note, color):

        i = 128 - note 
        self.area_piano.window.draw_rectangle(color, True, 
                    0, i * self.cursor_height, 
                    KEY_WIDTH + KEY_SPACE, self.cursor_height)
        self.area_piano.window.draw_rectangle(self.gc, False, 
                    0, i * self.cursor_height, 
                    KEY_WIDTH + KEY_SPACE, self.cursor_height)
        if i % 12 in [5, 7, 10, 0 , 2]:
            self.area_piano.window.draw_rectangle(self.gc, True, 
                        0, i * self.cursor_height + 2, 
                        KEY_WIDTH + KEY_SPACE - 1, KEY_HEIGHT - KEY_SPACE - 1)

    #Handles Expose event on piano roll (where the notes are)
    def area_expose_cb(self, area, event):
        self.style = self.area.get_style()
        self.gc = self.style.fg_gc[gtk.STATE_NORMAL]

        #Set variables needed for paging
        alloc = self.area.get_allocation()
        self.scroll_size = alloc.width-alloc.x-32
        alloc = self.sw.get_allocation()
        self.page_size = (alloc.width-alloc.x)-(BEAT_WIDTH*4)
        pages = self.scroll_size / self.page_size
        if self.scroll_size % self.page_size:
            pages = pages + 1
        self.pages = pages
        
        self.paint_roll()
        self.paint_selection()
        
    #Paints the piano roll (Where the notes are)
    def paint_roll(self):
        if self.area.window == None:
            return
        
        colormap = self.area.get_colormap()

        if self.gc_background == None:
            color_background = colormap.alloc_color('#FFFFFF', True, True)
            self.gc_background = self.area.window.new_gc()
            self.gc_background.set_foreground(color_background)

        if self.gc_foreground == None:
            color_foreground = colormap.alloc_color('#C0C0C0', True, True)
            self.gc_foreground = self.area.window.new_gc()
            self.gc_foreground.set_foreground(color_foreground)

        color_grid = colormap.alloc_color('#E0E0FF', True, True)
        self.gc_grid = self.area.window.new_gc()
        self.gc_grid.set_foreground(color_grid)

        color_note = colormap.alloc_color('#ffa235', True, True)
        self.gc_note = self.area.window.new_gc()
        self.gc_note.set_foreground(color_note)

        color_cursor = colormap.alloc_color('#0000FF', True, True)
        self.gc_cursor = self.area.window.new_gc()
        self.gc_cursor.set_foreground(color_cursor)

        alloc = self.area.get_allocation()
        
        len = self.pat.get_len() * self.grid_tick

        #We calculate the screensize for beat ticks, based on a 1/8 max subdiv
        beat_size = ((BEAT_WIDTH + KEY_SPACE * TICKS_PER_BEAT) - KEY_SPACE * self.grid_tick) / self.grid_tick + KEY_SPACE
        self.area.window.draw_rectangle(self.gc_foreground, True, len * beat_size, 0, alloc.width-alloc.x, alloc.height-alloc.y)

        self.area.window.draw_rectangle(self.gc_background, True, 0, 0, len * beat_size, 128 * self.cursor_height)
        
        for i in range(128):
            self.area.window.draw_line(self.gc_grid, 0, i * self.cursor_height, len * beat_size, i * self.cursor_height)

        for i in range(len):
            if i % self.grid_tick:
                self.area.window.draw_line(self.gc_grid, i * beat_size, 0, i * beat_size ,128 * self.cursor_height)
            else:
                self.area.window.draw_line(self.gc_foreground, i * beat_size, 0, i * beat_size,128 * self.cursor_height)

        self.area.window.draw_line(self.gc_grid, len * beat_size, 0, len * beat_size,128 * self.cursor_height)

        for (note, time, duration, volume) in self.track.get_notes():
            self.paint_note(note, time, duration)
            
        if self.adjust:
            self.vadj.set_value(32*(KEY_HEIGHT+KEY_SPACE))
            if self.midi_keyboard_listen:
                gobject.source_remove(self.midi_keyboard_listen)
                self.midi_keyboard_listen = 0
            self.midi_keyboard_listen = gobject.timeout_add(25, self.handle_midi_input)
            self.adjust = 0
        
        self.move_cursor(self.cursor_pos)

        return True

    #Paint a note in the piano roll
    def paint_note(self, note, pos, duration=1):
        self.paint_note_sound(self.gc_note, note, pos, duration)
        
    #Clear a note in the piano roll
    def clear_note(self, note, pos, duration=1):
        self.paint_note_space(self.gc_background, note, pos, duration)
        self.paint_grid(note, note, pos, duration)        
                
    #Move edit cursor
    def move_cursor(self, pos):
        #We calculate the screensize for beat ticks, based on a 1/8 max subdiv
        cursor_pos_x = self.cursor_pos * self.cursor_width
        piano_height = 128 * self.cursor_height

        #Warp around (both directions)
        pos = pos % (self.pat.get_len()*TICKS_PER_BEAT)
        pos_x = pos * self.cursor_width

        
        #Adjust scrollbar to see the notes playing
        if (cursor_pos_x/self.page_size) != (pos_x/self.page_size):
            mypage = (pos_x/self.page_size)
            if mypage == 0:
                self.hadj.set_value(0) 
            elif mypage >= (self.pages-1):
                #print scroll_size, page_size
                self.hadj.set_value(self.scroll_size-self.page_size-BEAT_WIDTH*4)
            else:
                self.hadj.set_value((self.page_size)*(mypage-1)) 

        #Draw hard beat on black
        if (self.cursor_pos % TICKS_PER_BEAT) == 0:
            self.area.window.draw_line(self.gc_foreground, cursor_pos_x, 0, cursor_pos_x, piano_height)
        elif (self.cursor_pos % self.note_size) == 0:
            self.area.window.draw_line(self.gc_grid, cursor_pos_x, 0, cursor_pos_x, piano_height)
        else:
            #Clear old cursor pos and draw grid points cleaned
            self.area.window.draw_line(self.gc_background, cursor_pos_x, 0, cursor_pos_x, piano_height)
            for i in range(128):
                self.area.window.draw_point(self.gc_grid, cursor_pos_x, i * self.cursor_height)

        #If notes on cursor pos, redraw them
        for (note, npos, duration, volume) in self.track.get_notes():
            if self.cursor_pos > npos and self.cursor_pos < npos+duration:
                self.paint_note(note, npos, duration)
                
        #Cursor line in cursor color
        self.area.window.draw_line(self.gc_cursor, pos_x, 0, pos_x, piano_height)
        
        self.cursor_pos = pos
    

    def paint_selection(self):
        note_start = 128 - self.selection_y
        note_end = 128 - (self.selection_y + self.selection_height)

        self.area.window.draw_rectangle(self.gc_cursor, False, 
                self.selection_x * self.cursor_width, 
                note_start * self.cursor_height,
                (self.selection_width) * self.cursor_width * self.note_size,
                self.selection_height * self.cursor_height)

        
    def clear_selection(self):
        note_start = 128 - self.selection_y
        note_end = 128 - (self.selection_y + self.selection_height)

        self.area.window.draw_rectangle(self.gc_grid, False, 
                self.selection_x * self.cursor_width, 
                note_start * self.cursor_height,
                (self.selection_width * self.note_size) * self.cursor_width,
                self.selection_height * self.cursor_height)

        for pos in [self.selection_x, self.selection_x + (self.selection_width * self.note_size)]:

            #Draw hard beat on black
            if (pos % TICKS_PER_BEAT) == 0:
                self.area.window.draw_line(self.gc_foreground, 
                        pos * self.cursor_width, 
                        note_start * self.cursor_height, 
                        pos * self.cursor_width,
                        (note_start + self.selection_height) * self.cursor_height)

            #Cursor
            if self.cursor_pos == pos:
                self.area.window.draw_line(self.gc_cursor, 
                        pos * self.cursor_width, 
                        note_start * self.cursor_height, 
                        pos * self.cursor_width,
                        (note_start + self.selection_height) * self.cursor_height)
        
    #On mouse button click
    def area_button_press_event(self, widget, event):
        self.area.grab_focus()
        
        pos = int(event.x / self.cursor_width)
        diff = pos % self.note_size
        pos = pos - diff

        note = 128 -  int(event.y / self.cursor_height)
        synth_conn = self.conn.get_port(self.track.get_synth())


        if event.button == 3:

            #Add it to track
            if self.recording:
                self.mouse_painting = 1
                self.paint_note(note, pos, self.note_size)
                if synth_conn != None: 
                    synth_conn.note_on(note, self.track.get_port(), self.volume)
                    time.sleep(0.05)
                    synth_conn.note_off(note, self.track.get_port())

        elif event.button == 1:
            state = event.state
            if not (state & (gtk.gdk.SHIFT_MASK | gtk.gdk.CONTROL_MASK)):
                
                self.update_selection(pos, note, 1, 1)
                
        elif event.button == 2:
            self.move_cursor(pos)
        
    def area_button_release_event(self, widget, event):
        state = event.state

        if self.mouse_painting:
            self.add_note(self.mouse_note, self.mouse_pos, self.note_size, self.volume)
            
        self.mouse_painting = 0
        
    def area_motion_notify(self, widget, event):
        synth_conn = self.conn.get_port(self.track.get_synth())
        
        micropos = int(event.x / self.cursor_width)
        diff = micropos % self.note_size
        pos = micropos - diff

        note = 128 -  int(event.y / self.cursor_height)
        
        state = event.state
        
        if state & gtk.gdk.BUTTON1_MASK:
            if state & gtk.gdk.SHIFT_MASK:
                pos_diff =  pos - self.mouse_pos
                note_diff =  note - self.mouse_note            
                if pos_diff or note_diff:
                    self.move_selection(self.selection_x + pos_diff, self.selection_y + note_diff)
            elif state & gtk.gdk.CONTROL_MASK:
                if micropos - self.mouse_micropos:
                    self.resize_selection(micropos - self.mouse_micropos)
            else:
                width =  (pos - self.selection_x)/self.note_size + 1
                height = self.selection_y - note

                if width < 1: width = 1
                if height < 1: height = 1

                self.update_selection(self.selection_x, self.selection_y, 
                    width, height)
                    
        elif self.mouse_painting:

            if pos != self.mouse_pos:
                self.add_note(self.mouse_note, self.mouse_pos, self.note_size, self.volume)
                if synth_conn != None: 
                    synth_conn.note_on(self.mouse_note, self.track.get_port(), self.volume)
                    time.sleep(0.1)
                    synth_conn.note_off(self.mouse_note, self.track.get_port())
                    
                self.paint_note(note,pos, self.note_size)
            elif note != self.mouse_note:
                self.clear_note(self.mouse_note,self.mouse_pos, self.note_size)
                for (snote, stime, sduration, svolume) in self.track.get_notes():
                    if snote == self.mouse_note and stime == pos:
                        self.paint_note(snote, stime, sduration)
                    
                self.paint_note(note, pos, self.note_size)

        self.paint_piano_note(self.mouse_note, self.gc_background)
        
        self.mouse_micropos = micropos
        self.mouse_pos = pos
        self.mouse_note = note

        self.paint_piano_note(self.mouse_note, self.gc_cursor)

    #Keyboard Handling
    def window_key_press_event(self, widget, event):
        #local alias, to make things more readable (and writeable)

        if self.player.playing():
            self.move_cursor(self.player.get_pos())
            
        val = event.keyval
        state = event.state
        synth_conn = self.conn.get_port(self.track.get_synth())

        # Check for hooks on this key/modifier combination
        for hook in self.piano_roll_key_event_hooks:
            if state == hook.modifiers and val in hook.keys:
                # If found, run hook and exit returning True
                hook.activate(self, val)
                return True
        
        #Control mask, to get shortcuts and avoid having to go with the mouse
        if state == gtk.gdk.CONTROL_MASK:
            grid_keys = [key._1, key._2, key._3, key._4, key._5, key._6]
            #Grid size
            if val in grid_keys:
                self.cbo_grid.set_active(grid_keys.index(val))
            #Octave Up    
            elif val == key.Up:
                if self.cbo_oct.get_active() > 0:
                    self.cbo_oct.set_active(self.cbo_oct.get_active()-1)
            #Octave Down
            elif val == key.Down:
                if self.cbo_oct.get_active() < 6:
                    self.cbo_oct.set_active(self.cbo_oct.get_active()+1)
            #Selection downsize
            elif val == key.Left:
                self.resize_selection(-1)
            #Selection upsize
            elif val == key.Right:
                self.resize_selection(1)
            #Cut Selection
            elif val == key.x:
                self.cut_selection()
            #Copy Selection
            elif val == key.c:
                self.copy_selection()
            #Paste Selection
            elif val == key.v:
                self.paste_selection()
            #Play/Stop
            elif val == key.p:
                if self.player.playing():
                    self.btn_stop_clicked(None)
                else:
                    self.btn_play_clicked(None)
            #Stop
            elif val == key.s:
                self.btn_stop_clicked(None)
            #Rec on/off
            elif val == key.r:
                if self.recording:
                    self.chk_recording.set_active(0)
                    self.recording = 0
                else:
                    self.chk_recording.set_active(1)
                    self.recording = 1
            #Mute trakcs
            elif val == key.m:
                #Muted track is NOT enabled... 
                self.chk_mute_track.set_active(self.track.enabled)

        #Control mask, to get shortcuts and avoid having to go with the mouse
        elif state == gtk.gdk.SHIFT_MASK:
            if val in [key.Left, key.Right, key.Up, key.Down]:
                diff_width = 0
                diff_height = 0

                #Change selection size
                if val == key.Up and self.selection_height > 1:
                    diff_height = -1
                elif val == key.Down:
                    diff_height = 1
                elif val == key.Left and self.selection_width > 1:
                    diff_width = -1
                #horrible formula to avoid going too far... must think about this and make it clear
                elif val == key.Right and self.selection_x + self.selection_width * self.note_size < self.pat.get_len()*TICKS_PER_BEAT:
                    diff_width = 1
                            
                #Update Selection
                self.update_selection(self.selection_x, self.selection_y, 
                                        self.selection_width + diff_width, self.selection_height + diff_height)
                
        elif state == gtk.gdk.MOD1_MASK:
            if val in [key.Page_Up, key.Page_Down, key.Left, key.Right, key.Up, key.Down]:
                #Modifiers
                note_diff = 0
                pos_diff = 0
                if val == key.Page_Up:
                    note_diff = 12
                elif val == key.Page_Down:
                    note_diff = -12
                if val == key.Up:
                    note_diff = 1
                elif val == key.Down:
                    note_diff = -1
                elif val == key.Left:
                    pos_diff = -self.note_size
                elif val == key.Right:
                    pos_diff = self.note_size
                    
                self.move_selection(self.selection_x + pos_diff, self.selection_y + note_diff)

        else:
            if val == key.space:
                if self.vk_space == 0:

                    pos = self.cursor_pos
                        
                    #Add it to track
                    if self.recording:
                        self.add_note(self.selection_y, pos, self.note_size, self.volume)
                    
                    if synth_conn != None: synth_conn.note_on(self.selection_y, self.track.get_port(), self.volume)
                    self.vk_space = 1
            #Volume Down    
            elif val == key.KP_Subtract:
                if self.cbo_vol.get_active() > 0:
                    self.cbo_vol.set_active(self.cbo_vol.get_active()-1)
            #Volume Up
            elif val == key.KP_Add:
                if self.cbo_vol.get_active() < 8:
                    self.cbo_vol.set_active(self.cbo_vol.get_active()+1)
                                    
            elif val in VIRTUAL_KEYBOARD:
                key_index = VIRTUAL_KEYBOARD.index(val)
                if self.scale:
                    if self.scale_var:
                        scale = [(x+(self.scale-1))%12 for x in SCALE_MIN]
                    else:
                        scale = [(x+(self.scale-1))%12 for x in SCALE_MAJ]

                    if not (key_index % 12) in scale:
                        return True
                        
                #If not key already pressed
                if self.vk_status[key_index] == 0:
                    note = (self.octave+60) + key_index
                    
                    #Are we making changes?
                    if self.recording:
                    
                        #In case Del is pressed
                        if self.deleting:
                            #Remember that we are "selected" deleting
                            self.deleting = 2
                            
                            #If not in playing mode Delete note now, else we wait the cursor to do the work
                            if not self.player.playing():
                                for (dnote, dpos, dduration, dvolume) in self.track.get_notes():
                                    if dpos == self.cursor_pos and dnote == note:
                                        self.del_note(dnote, dpos, dduration)
                        else:
                            if self.player.playing():
                                #if we are playing, we must qantize
                                beat_size = self.note_size
                                diff = self.cursor_pos % beat_size
                                pos = self.cursor_pos - diff
                                pat_len = self.pat.get_len()*TICKS_PER_BEAT
                                #Live recording. Save position, velocity and paint the start
                                self.notes_start_position_velocity[note] = (pos, self.volume)
                                self.paint_note(note, pos % pat_len , self.note_size)
                                    
                            else:
                                pos = self.cursor_pos
                                #Add it to track
                                self.add_note(note, pos, self.note_size, self.volume)
                                                        
                            #Update Selection
                            self.update_selection(pos, note, self.selection_width, self.selection_height)
                            
                    #If not Deleting let's make noise
                    if not self.deleting:
                        if synth_conn != None: synth_conn.note_on(note, self.track.get_port(), self.volume)
                    
                    #Keyboard status, to avoid repetition.
                    self.vk_status[key_index] = 1
                    self.vk_count = self.vk_count + 1

            if val == key.Delete:
                if not self.deleting:
                    self.deleting = 1
                    
            elif val == key.BackSpace:
                #Delete only if recording and don't delete here if playing
                if not self.player.playing() and self.recording:

                    #Move cursor manually 
                    if (self.cursor_pos % self.note_size):
                        self.move_cursor(self.cursor_pos - (self.cursor_pos % self.note_size))
                    else:
                        self.move_cursor(self.cursor_pos - self.note_size * self.step_size)

                    #Delete
                    del_notes = []
                    for item in self.track.get_notes(): del_notes.append(item)
                    for (dnote, dpos, dduration, dvolume) in del_notes:
                        if dpos == self.cursor_pos:
                            self.del_note(dnote, dpos, dduration)

                    #I have drink a lot of wine now... so i'm in lazy mode. repainting cursor the bad way
                    self.move_cursor(self.cursor_pos)

                    self.update_selection(self.cursor_pos, self.selection_y, 1, 1)
                    
        return True

    def window_key_release_event(self, widget, event):
        #local alias, to make things more readable (and writeable)

        if self.player.playing():
            self.move_cursor(self.player.get_pos())

        val = event.keyval
        state = event.state
        synth_conn = self.conn.get_port(self.track.get_synth())
        
        if state == gtk.gdk.CONTROL_MASK:
            #Shortucts have nothing to do here
            pass
        else:
            if val == key.space:
                if synth_conn != None: synth_conn.note_off(self.selection_y, self.track.get_port())
                self.vk_space = 0
            elif val in VIRTUAL_KEYBOARD:
                key_index = VIRTUAL_KEYBOARD.index(val)

                if self.scale:
                    if self.scale_var:
                        scale = [(x+(self.scale-1))%12 for x in SCALE_MIN]
                    else:
                        scale = [(x+(self.scale-1))%12 for x in SCALE_MAJ]

                    if not (key_index % 12) in scale:
                        return True

                note = (self.octave+60) + key_index
                
                #Update Keyboard Status
                self.vk_status[key_index] = 0
                
                if self.vk_count > 0:
                    self.vk_count = self.vk_count - 1

                if not self.deleting:

                    #Stop the noise
                    if synth_conn != None: synth_conn.note_off(note, self.track.get_port())
                
                    if self.recording:
                        if self.player.playing():
                            (pos, velocity) = self.notes_start_position_velocity[note]
                            duration = self.cursor_pos - (self.cursor_pos % self.note_size) - pos
                            #Cut note duration at end of pattern
                            if duration < 0:
                                duration = self.pat.get_len()*TICKS_PER_BEAT - pos
                            #Minimal size is note size (grid size)
                            if duration < self.note_size: 
                                duration = self.note_size
                            
                            #Delete original temorary note    
                            self.del_note(note,pos)
                            #Add new real note
                            self.add_note(note, pos, duration, velocity)
                        else:
                            #If not playing move cursor manually and recording
                            if self.vk_count == 0:
                                if (self.cursor_pos % self.note_size):
                                    self.move_cursor(self.cursor_pos + self.note_size - (self.cursor_pos % self.note_size))
                                else:
                                    self.move_cursor(self.cursor_pos + self.note_size * self.step_size)
                                    
                                self.update_selection(self.cursor_pos, self.selection_y, 1, 1)
                    
            elif val == key.Delete:
                #Delete only if recording and don't delete here if playing
                if not self.player.playing() and self.recording:
                    #Full delete?
                    if self.deleting == 1:
                        del_notes = []
                        for item in self.track.get_notes(): del_notes.append(item)
                        for (dnote, dpos, dduration, dvolume) in del_notes:
                            if dpos == self.cursor_pos:
                                self.del_note(dnote, dpos, dduration)

                    #Move cursor manually 
                    if (self.cursor_pos % self.note_size):
                        self.move_cursor(self.cursor_pos + self.note_size - (self.cursor_pos % self.note_size))
                    else:
                        self.move_cursor(self.cursor_pos + self.note_size)

                    self.update_selection(self.cursor_pos, self.selection_y, 1, 1)
                
                #Always clear delete note
                self.deleting = 0
    
    #This is the MIDI Input handler, runs on the scheduled timer self.midi_keyboard_listen
    def handle_midi_input(self):
        
        #Sync player cursor with screen cursor if playing
        if self.player.playing():
            self.move_cursor(self.player.get_pos())
        
        synth_conn = self.conn.get_port(self.track.get_synth())

        #MIDI Input
        while self.container.container.conn.midi_input_event_pending():
            event = self.container.container.conn.get_midi_input_event()
            
            if event['type'] == alsaseq.EVENT_NOTE:
                #Check if we are using a scale filter for notes
                do_note = True
                if self.scale and event['data']['note']['note']:
                    note = event['data']['note']['note']
                    if self.scale_var:
                        scale = [(x+(self.scale-1))%12 for x in SCALE_MIN]
                    else:
                        scale = [(x+(self.scale-1))%12 for x in SCALE_MAJ]

                    if not (note % 12) in scale:
                        do_note = False

                #Case note on (has velocity)
                if do_note and event['data']['note']['note'] and event['data']['note']['velocity']:
                    #How many keys pressed? Used for step editing chords
                    self.midi_keyboard_count += 1
                    
                    note = event['data']['note']['note']

                    #Are we making changes?
                    if self.recording:
                        #In case we are playing we qantize the note
                        pos = self.cursor_pos - (self.cursor_pos % self.note_size)

                        pat_len = self.pat.get_len()*TICKS_PER_BEAT
                        
                        #If we are playing, we wait to add the note on key release
                        if self.player.playing():
                            #We still don't add that note, but paint the start of if and record velocity and pos
                            if self.cbo_vol.get_active() > 7:
                                self.notes_start_position_velocity[note] = (pos, event['data']['note']['velocity'])
                            else:
                                self.notes_start_position_velocity[note] = (pos, self.volume)

                            #Paint it
                            self.paint_note(note, pos % pat_len , self.note_size)
                        else:
                            #If not playing, we add the note right now
                            if self.cbo_vol.get_active() > 7:
                                self.add_note(note, pos, self.note_size, event['data']['note']['velocity'])
                            else:
                                self.add_note(note, pos, self.note_size, self.volume)

                    if self.cbo_vol.get_active() > 7:
                        if synth_conn != None: synth_conn.note_on(note, self.track.get_port(), event['data']['note']['velocity'])
                    else:
                        if synth_conn != None: synth_conn.note_on(note, self.track.get_port(), self.volume)
                        
                #Note off event
                elif do_note and event['data']['note']['note']:
                    self.midi_keyboard_count -= 1
                    
                    if self.recording:
                        if self.player.playing():
                            note = event['data']['note']['note']
                            (pos, velocity) = self.notes_start_position_velocity[note]
                            duration = self.cursor_pos - (self.cursor_pos % self.note_size) - pos
                            #Cut note duration at end of pattern
                            if duration < 0:
                                duration = self.pat.get_len()*TICKS_PER_BEAT - pos
                            #Minimal size is note size (grid size)
                            if duration < self.note_size: 
                                duration = self.note_size
                            
                            #Add new real note
                            self.add_note(note, pos, duration, velocity)
                            
                        elif self.midi_keyboard_count == 0: 
                            #Move cursor if not playing and all notes are released
                            if (self.cursor_pos % self.note_size):
                                self.move_cursor(self.cursor_pos + self.note_size - (self.cursor_pos % self.note_size))
                            else:
                                self.move_cursor(self.cursor_pos + self.note_size * self.step_size)

                    if synth_conn != None: synth_conn.note_off(event['data']['note']['note'], self.track.get_port())
            elif event['type'] == alsaseq.EVENT_CONTROLLER:
                self.container.controller_editor_widget.handle_midi_input(self.cursor_pos, event['data']['control']['param'], event['data']['control']['value'])
            elif event['type'] == alsaseq.EVENT_PITCH:
                self.container.pitchbend_editor_widget.handle_midi_input(self.cursor_pos, event['data']['control']['value'])
        if self.player.playing():
            #Paint the cursor
            self.move_cursor(self.cursor_pos)
            #Repaint selection
            self.paint_selection()
        return True

    #Record checkbox clicked Event
    def chk_recording_toggled(self, widget, data=None):
        self.recording =  self.chk_recording.get_active()
        self.area.grab_focus()
    
    #Mute checkbox clicked Event
    def chk_mute_track_toggled(self, widget, data=None):
        if widget.get_active():
            self.track.disable()
        else:
            self.track.enable()
        self.area.grab_focus()

    #Play button clicked Event
    def btn_play_clicked(self, widget):
        self.player.set_pos(self.cursor_pos)
        self.player.play(self.pat, self.container.container.song.bpm, True)
        self.area.grab_focus()        
    
    #Stop button clicked Event
    def btn_stop_clicked(self, widget):
        if self.player.playing():
            self.player.stop()

            #Complete cursor movement.
            if (self.cursor_pos % self.note_size):
                self.move_cursor(self.cursor_pos + self.note_size - (self.cursor_pos % self.note_size))
            else:
                self.move_cursor(self.cursor_pos)

            self.area.grab_focus()
    
    #Grid size changed Event
    def cbo_grid_changed(self, widget, data=None):
        widths = (1, 2, 3, 4, 6, 8)
        self.grid_tick = widths[widget.get_active()]
        
        self.note_size = TICKS_PER_BEAT / self.grid_tick

        if (self.cursor_pos % self.note_size) and not self.player.playing():
            self.move_cursor(self.cursor_pos - (self.cursor_pos % self.note_size))

        self.paint_roll()
        self.area.grab_focus()
    
    #Step size changed Event
    def cbo_step_changed(self, widget, data=None):
        self.step_size = int(widget.get_active())+1
        self.paint_roll()
        self.area.grab_focus()

    #Octave changed Event
    def cbo_oct_changed(self, widget, data=None):
        self.octave = 12 * -(widget.get_active()-3)
        self.area.grab_focus()

    #Volume changed Event
    def cbo_vol_changed(self, widget, data=None):
        if widget.get_active() < 7:
            self.volume = 16 * (widget.get_active()+1) - 1
        else:
            self.volume = 127

        if self.recording:
            self.vol_selection()
        
        self.area.grab_focus()

    #Scale note changed Event
    def cbo_scale_changed(self, widget, data=None):
        self.scale = widget.get_active()
        self.area.grab_focus()

    #Scale variant changed Event
    def cbo_scale_var_changed(self, widget, data=None):
        self.scale_var = widget.get_active()
        self.area.grab_focus()

    #Update selected notes
    def update_selection(self, selection_x, selection_y, selection_width, selection_height):
        #Clear selection box
        self.clear_selection()

        #Update Selection Coords
        self.selection_x = selection_x
        self.selection_y = selection_y
        self.selection_width = selection_width
        self.selection_height = selection_height

        #Paint Selection
        self.paint_selection()

        #Update selected notes
        self.selection = []
        #Delete old notes
        for (note, pos, duration, volume) in self.track.get_notes():
            if (note <= self.selection_y and note > (self.selection_y - self.selection_height) and 
                    pos >= self.selection_x and 
                    pos < self.selection_x + (self.selection_width * self.note_size)):

                self.selection.append( (note, pos, duration, volume) )
    
    def move_selection(self, x, y):
        diff_pos = x - self.selection_x
        diff_note = y - self.selection_y 

        new_selection = []
        for (note, pos, duration, volume) in self.selection:
            self.del_note(note, pos, duration)
            new_selection.append( (note+diff_note, pos+diff_pos, duration, volume) )
            for (snote, spos, sduration, svolume) in self.track.get_notes():
                if note==snote: 
                    self.paint_note(snote, spos, sduration)
        
        self.selection = new_selection

        for (note, pos, duration, volume) in self.selection:
            self.add_note(note, pos, duration, volume, True)
        
        #Clear selection box
        self.clear_selection()
        
        self.selection_x = x
        self.selection_y = y

        self.paint_selection()

    
    def resize_selection(self, diff_duration):

        new_selection = []
        for (note, pos, duration, volume) in self.selection:
            if duration + diff_duration > 0:
                mydiff = diff_duration
            else:
                mydiff = 0
                
            self.del_note(note, pos, duration)
            new_selection.append( (note, pos, duration + mydiff, volume) )
            if (note, pos, duration, volume) in self.track.get_notes():
                self.paint_note(note, pos, duration)
        
        self.selection = new_selection
        for (note, pos, duration, volume) in self.selection:
            self.add_note(note, pos, duration, volume)
            
    def vol_selection(self):

        new_selection = []
        for (note, pos, duration, volume) in self.selection:
            self.del_note(note, pos, duration)
            new_selection.append( (note, pos, duration, self.volume) )
            if (note, pos, duration, volume) in self.track.get_notes():
                self.paint_note(note, pos, duration)
        
        self.selection = new_selection
        for (note, pos, duration, volume) in self.selection:
            self.add_note(note, pos, duration, volume)
            
    def cut_selection(self):
        text = "Notes\n"
        
        for (note, pos, duration, volume) in self.selection:
            self.del_note(note, pos, duration)
            text += "%i, %i, %i, %i\n" % (note-self.selection_y, pos-self.selection_x, duration, volume)
            
            if (note, pos, duration, volume) in self.track.get_notes():
                self.paint_note(note, pos, duration)

        text += "EndNotes\n"
        
        clipboard = gtk.clipboard_get(gtk.gdk.SELECTION_CLIPBOARD)
        clipboard.set_text(text)        

    def copy_selection(self):
        text = "Notes\n"
        
        for (note, pos, duration, volume) in self.selection:
            text += "%i, %i, %i, %i\n" % (note-self.selection_y, pos-self.selection_x, duration, volume)

        text += "EndNotes\n"
        
        clipboard = gtk.clipboard_get(gtk.gdk.SELECTION_CLIPBOARD)
        clipboard.set_text(text)        

    def paste_selection(self):
        clipboard = gtk.clipboard_get(gtk.gdk.SELECTION_CLIPBOARD)
        clipboard.request_text(self.paste_selection_clipboard_text_received)
        
    # signal handler called when the clipboard returns text data
    def paste_selection_clipboard_text_received(self, clipboard, text, data):
        if not text or text == '':
            return
            
        lines = text.split("\n")
        if not len(lines):
            return
            
        if lines[0] != 'Notes':
            return

        level = 0
        for line in lines:

            if line == "Notes":
                level = 3

            if level == 3:
                if line == "Notes":
                    pass
                elif line == "EndNotes":
                    level = 2
                else:
                    (note, pos, duration, volume) = line.split(', ')
                    self.add_note( int(note)+self.selection_y, int(pos)+self.selection_x, int(duration), int(volume) )

    def add_note(self, note, pos, duration=1, volume=127, overlap=False):
        len = self.pat.get_len()*TICKS_PER_BEAT
        
        #Paint it
        self.paint_note(note, pos % len , duration)
        #Add it to track
        self.track.add_note(note, pos % len, duration, volume, overlap)

    #Deletes a note from the grid, the track and the sequence, and stops it's sound
    def del_note(self, note, pos, duration=1):
        len = self.pat.get_len()*TICKS_PER_BEAT

        self.track.del_note(pos % len, note, duration)

        self.clear_note(note, pos % len, duration)
        
        synth_conn = self.conn.get_port(self.track.get_synth())
        if synth_conn != None: 
            port = self.track.get_port()
            synth_conn.note_off(note, port)
        
    #Paint the space of a note with a color
    def paint_note_space(self, color, note, time, duration=1):
        len = self.pat.get_len()*TICKS_PER_BEAT
        
        note = 128 - note
        self.area.window.draw_rectangle(color, True, 
                (time % len) * self.cursor_width + 1, 
                note * self.cursor_height + 1,
                duration * self.cursor_width,
                KEY_HEIGHT)
                
    #Paint the space of a note with a color
    def paint_note_sound(self, color, note, time, duration=1):
        pat_len = self.pat.get_len()*TICKS_PER_BEAT
        
        note = 128 - note
        self.area.window.draw_rectangle(color, True, 
                (time % pat_len) * self.cursor_width + 2, 
                note * self.cursor_height + 2,
                duration * self.cursor_width -2,
                KEY_HEIGHT-2)
                
    #Paint the grid on a range
    def paint_grid(self, note_from, note_to, pos, duration=1):
        note_from = 128 - note_from
        note_to = 128 - note_to + 1 #1 plus, to fill the end of the note
        
        note_width = self.cursor_width        
        note_height = self.cursor_height
        
        #Horizontal lines
        for i in range (note_from, note_to):
            self.area.window.draw_line(self.gc_grid, 
                    pos * note_width, i * note_height, 
                    pos + duration * note_width, i * note_height)

        #Vertical lines
        for tmp_pos in range(pos, pos+duration+1):

            #Draw hard beat on black
            if tmp_pos % TICKS_PER_BEAT == 0:
                self.area.window.draw_line(self.gc_foreground, 
                        tmp_pos * note_width, note_from * note_height, 
                        tmp_pos * note_width, note_to * note_height)
            elif tmp_pos % self.note_size == 0:
                self.area.window.draw_line(self.gc_grid, 
                        tmp_pos * note_width, note_from * note_height, 
                        tmp_pos * note_width, note_to * note_height)

    def load_track(self, track):
        self.track = track
        self.chk_mute_track.set_active(not self.track.enabled)
        self.paint_roll()
        
    def grab_focus(self):
        self.area.grab_focus()
        return False
