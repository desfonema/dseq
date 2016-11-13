import gtk
from gtk import keysyms as key
from gtk.gdk import color_parse
import gobject
import time
from audio import alsaseq
from util import nanosleep

time.sleep = nanosleep.nanosleep

KEY_WIDTH = 14
KEY_HEIGHT = 7
KEY_SPACE = 1

BEAT_WIDTH = 24
TICKS_PER_BEAT = 24

#Some calculated values that we use all over the piano roll painting routine
CURSOR_WIDTH = BEAT_WIDTH/TICKS_PER_BEAT + KEY_SPACE
CURSOR_HEIGHT = KEY_HEIGHT + KEY_SPACE

# My virtual keyboard config
VIRTUAL_KEYBOARD = [
    key.z, key.s, key.x, key.d, key.c, key.v, key.g, key.b, key.h, key.n, key.j, key.m,
    key.q, key._2, key.w, key._3, key.e, key.r, key._5, key.t, key._6, key.y, key._7,
    key.u, key.i, key._9, key.o, key._0
]

SCALE_MAJ = [0,2,4,5,7,9,11]
SCALE_MIN = [0,2,3,5,7,9,11]

EVENT_MODIFIER_FILTER = gtk.gdk.SHIFT_MASK | gtk.gdk.CONTROL_MASK

EVENT_MODIFIER_NONE = 0
EVENT_MODIFIER_SHIFT = gtk.gdk.SHIFT_MASK
EVENT_MODIFIER_CTRL = gtk.gdk.CONTROL_MASK
EVENT_MODIFIER_CTRL_SHIFT = gtk.gdk.SHIFT_MASK | gtk.gdk.CONTROL_MASK

EVENT_MOUSE = gtk.gdk.BUTTON1_MASK
EVENT_MOUSE_SHIFT = EVENT_MOUSE | EVENT_MODIFIER_SHIFT
EVENT_MOUSE_CTRL = EVENT_MOUSE | EVENT_MODIFIER_CTRL
EVENT_MOUSE_CTRL_SHIFT = EVENT_MOUSE | EVENT_MODIFIER_CTRL_SHIFT

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


"""
Here starts the Key Hooks definitions, which describe for each key shortcut
handled by the Piano Roll the routine that makes it work.
"""

class KeyMoveCursor(KeyEventHook):
    """
    Move cursor with the keyboard
    """
    keys = [key.Left, key.Right, key.Up, key.Down]

    def activate(self, widget, keycode):
        #Move cursor
        if keycode in [key.Left, key.Right]:
            # Left/Right keys moves insert/play cursor
            widget.move_cursor(widget.cursor_pos + widget.note_size * (1 if keycode == key.Right else -1))
            note_from = widget.sel_note_from
        else:
            note_from = widget.sel_note_from + (1 if keycode == key.Up else -1)

        
        widget.update_selection(widget.cursor_pos, note_from, widget.cursor_pos+widget.note_size, note_from)


class KeyDeletePiano(KeyEventHook):
    keys = [key.Delete, key.BackSpace]

    def deactivate(self, widget, keycode):
        if widget.recording and not widget.player.playing():
            if keycode == key.BackSpace:
                widget.move_cursor(widget.cursor_pos - widget.note_size * widget.step_size)

            for (note, pos, duration, volume) in list(widget.track.get_notes()):
                if pos == widget.cursor_pos:
                    widget.del_note(note, pos, duration)

            if keycode == key.Delete:
                widget.move_cursor(widget.cursor_pos + widget.note_size * widget.step_size)
        

class KeyGridSize(KeyEventHook):
    """
    Change Grid size.
    """

    modifiers = EVENT_MODIFIER_CTRL
    keys = [key._1, key._2, key._3, key._4, key._5, key._6]

    def activate(self, widget, keycode):
        #Grid size
        widget.track_widget.cbo_grid.set_active(self.keys.index(keycode))

class KeyOctaveShift(KeyEventHook):
    """
    Change input octave shift up and down
    """

    modifiers = EVENT_MODIFIER_CTRL
    keys = [key.Up, key.Down]

    def activate(self, widget, keycode):
        octave = widget.track_widget.cbo_oct.get_active()
        octave = max(0, octave-1) if keycode == key.Up else min(6, octave+1)
        widget.track_widget.cbo_oct.set_active(octave)


class KeyResizeSelection(KeyEventHook):
    """
    Resizes notes in selection
    """

    modifiers = EVENT_MODIFIER_CTRL
    keys = [key.Left, key.Right]

    def activate(self, widget, keycode):
        widget.resize_selection(1 if keycode==key.Right else -1)

class KeyCutCopyPaste(KeyEventHook):
    """
    Resizes notes in selection
    """

    modifiers = EVENT_MODIFIER_CTRL
    keys = [key.x, key.c, key.v]

    def activate(self, widget, keycode):
        #Cut Selection
        if keycode == key.x:
            widget.cut_selection()
        #Copy Selection
        elif keycode == key.c:
            widget.copy_selection()
        #Paste Selection
        else:
            widget.paste_selection()

class KeyPlayControls(KeyEventHook):
    """
    Controls pattern play, stop, rec, and mute.
    """

    modifiers = EVENT_MODIFIER_CTRL
    keys = [key.m, key.s, key.r, key.p, key.n]

    def activate(self, widget, keycode):
        #Play/Stop
        if keycode == key.p:
            if widget.player.playing():
                widget.track_widget.btn_stop_clicked(None)
            else:
                widget.track_widget.btn_play_clicked(None)
        #Stop
        elif keycode == key.s:
            widget.track_widget.btn_stop_clicked(None)
        #Rec on/off
        elif keycode == key.r:
            widget.track_widget.chk_recording.set_active(not widget.recording)
        #Mute trakcs
        elif keycode == key.m:
            #Muted track is NOT enabled... 
            widget.track_widget.chk_mute_track.set_active(widget.track.enabled)
        #Mono rec
        elif keycode == key.n:
            widget.track_widget.chk_mono.set_active(not widget.rec_mono)

class KeySelection(KeyEventHook):
    """
    Select notes on the piano roll with the keyboard
    """

    modifiers = EVENT_MODIFIER_SHIFT
    keys = [key.Left, key.Right, key.Up, key.Down]

    def activate(self, widget, keycode):
        diff_width = 0
        diff_height = 0

        if widget.sel_pos_start == -1:
            widget.sel_pos_start = widget.sel_pos_from
            widget.sel_note_start = widget.sel_note_from
            widget.sel_pos_end = widget.sel_pos_from + widget.note_size
            widget.sel_note_end = widget.sel_note_from

        #Change selection size
        if keycode == key.Up:
            widget.sel_note_end += 1
        elif keycode == key.Down:
            widget.sel_note_end += -1
        elif keycode == key.Left:
            widget.sel_pos_end += -widget.note_size
            if widget.sel_pos_end == widget.sel_pos_start:
                widget.sel_pos_end += -widget.note_size
        elif keycode == key.Right:
            widget.sel_pos_end += widget.note_size
            if widget.sel_pos_end == widget.sel_pos_start:
                widget.sel_pos_end += widget.note_size
                
                    
        #Update Selection
        widget.update_selection(
            widget.sel_pos_start,
            widget.sel_note_start, 
            widget.sel_pos_end,
            widget.sel_note_end
        )

class KeySelectionEnd(KeyEventHook):
    """
    End selection of notes on the piano roll with the keyboard
    """

    modifiers = EVENT_MODIFIER_SHIFT
    keys = [key.Shift_L, key.Shift_R]

    def deactivate(self, widget, keycode):
        widget.sel_pos_start = -1

class KeySelectionMove(KeyEventHook):
    """
    Move selected notes
    """

    modifiers = EVENT_MODIFIER_CTRL_SHIFT
    keys = [key.Page_Up, key.Page_Down, key.Left, key.Right, key.Up, key.Down]

    def activate(self, widget, keycode):
        note_shift = {key.Page_Up: 12, key.Page_Down: -12, key.Up: 1, key.Down: -1}
        pos_shift = {key.Left: -widget.note_size, key.Right: widget.note_size}
            
        widget.move_selection(
            widget.sel_pos_from + pos_shift.get(keycode, 0), 
            widget.sel_note_from + note_shift.get(keycode, 0)
        )
                
class KeyInputVolume(KeyEventHook):
    """
    Set input volume.
    """

    keys = [key.KP_Subtract, key.KP_Add]

    def activate(self, widget, keycode):
        volume = widget.track_widget.cbo_vol.get_active()
        widget.track_widget.cbo_vol.set_active(
            max(0, volume-1) if keycode == key.KP_Subtract else min(8, volume+1)
        )

class KeyInsertNote(KeyEventHook):
    """
    Insert note at cursor position
    """

    keys = [key.space]

    def activate(self, widget, keycode):
        if widget.vk_space == 0:

            pos = widget.cursor_pos
                
            #Add it to track
            if widget.recording:
                widget.add_note(widget.sel_note_from, pos, widget.note_size, widget.volume)
            
            synth_conn = widget.conn.get_port(widget.track.get_synth())
            if synth_conn != None: synth_conn.note_on(widget.sel_note_from, widget.track.get_port(), widget.volume)
            widget.vk_space = 1

    def deactivate(self, widget, keycode):
        synth_conn = widget.conn.get_port(widget.track.get_synth())
        if synth_conn != None: synth_conn.note_off(widget.sel_note_from, widget.track.get_port())
        widget.vk_space = 0
                
class KeyVirtualPiano(KeyEventHook):
    """
    Handle virtual keyboard emulation so people without a midi controller
    can have fun too.
    """
    keys = VIRTUAL_KEYBOARD

    def _gen_event(self, ev_type, note, velocity):
        """
        Create a midi event to pass to handle_midi_event
        """
        event = {'type': ev_type,
                 'data': {'note': {'note': note,
                                   'velocity': velocity}}}
        return event
        

    def activate(self, widget, keycode):
        #If not key already pressed
        key_index = VIRTUAL_KEYBOARD.index(keycode)
        if not widget.vk_status[key_index]:
            note = (widget.octave+60) + key_index
            event = self._gen_event(alsaseq.EVENT_NOTE_ON, note, widget.volume)
            
            #Keyboard status, to avoid repetition.
            widget.vk_status[key_index] = 1
            widget.vk_count = widget.vk_count + 1

            widget.handle_midi_event(event)

    def deactivate(self, widget, keycode):
        key_index = VIRTUAL_KEYBOARD.index(keycode)
        note = (widget.octave+60) + key_index
        event = self._gen_event(alsaseq.EVENT_NOTE_OFF, note, widget.volume)
        
        #Keyboard status
        widget.vk_status[key_index] = 0
        widget.vk_count = max(widget.vk_count -1, 0)
        widget.handle_midi_event(event)


class PianoRollWidget(gtk.HBox):

    # Which events are handled by hooks for the piano roll area
    piano_roll_key_event_hooks = [
        KeyMoveCursor(),
        KeyDeletePiano(),
        KeyGridSize(),
        KeyOctaveShift(),
        KeyResizeSelection(),
        KeyCutCopyPaste(),
        KeyPlayControls(),
        KeySelection(),
        KeySelectionEnd(),
        KeySelectionMove(),
        KeyInputVolume(),
        KeyInsertNote(),
        KeyVirtualPiano(),
    ]

    def __init__(self, track_widget):
        super(PianoRollWidget, self).__init__()

        self.debug = False
        self.load_track(track_widget)

        # Piano roll colors
        self.colors = {}

        # Virtual Keyboard Status initialized on Zero
        # Used to avoid key repeatitions and also to count release events for chords
        self.vk_space = 0
        self.vk_status = [0]*len(VIRTUAL_KEYBOARD)
        self.vk_count = 0

        # Octave transposition (for virtual keyboard)
        self.octave = 0
        
        # Grid tick (which is in direct relation to note size)
        self.grid_tick = 1

        # Note size is TICKS_PER_BEAT/self.grid_tick. Divide by 1... to keep formula present
        self.note_size = TICKS_PER_BEAT / self.grid_tick

        # Step size (How much we move forward in step mode)
        self.step_size = 1

        # Record flag
        self.recording = 1
        self.rec_mono = False

        # Input volume
        self.volume = 127
        
        # Scale helpers variables (Help prevent inserting notes out of scale)
        self.scale = 0
        self.scale_var = 0
        

        # Reading MIDI Keyboard variables
        self.midi_keyboard_listen = None
        self.midi_keyboard_count = 0
        
        # This handles when a note was pressed (in virt keyb or midi keyb) for
        # note insert in live recording by keeping track of the initial place
        # where the note was inserted.
        self.notes_insert_position_velocity = [(-1,0)]*127

        #Insert/Play cursor position
        self.cursor_pos = 0
        
        # Selection is the tool to move, copy, paste and delete notes
        self.sel_pos_from = 0
        self.sel_pos_to = self.note_size
        self.sel_pos_start = -1
        self.sel_pos_end = -1
        self.sel_note_from = 60
        self.sel_note_to = 60
        self.sel_note_start = -1
        self.sel_note_end = -1

        # We keep track of the selected notes
        self.selection = []
        # And of mouse in progress selection
        self.mouse_selection = 0
        
        # Mouse input variables
        self.mouse_pos = 0
        self.mouse_note = 0

        # Are we inserting notes with the mouse?
        self.mouse_painting = 0
        
        # Piano Notes drawing objects

        # Scrolling widget
        self.keyboard_sw = gtk.ScrolledWindow()
        self.keyboard_sw.set_policy(gtk.POLICY_NEVER, gtk.POLICY_ALWAYS)
        self.keyboard_sw.set_placement(gtk.CORNER_TOP_RIGHT)

        # Keyboard notes
        self.keyboard_area = gtk.DrawingArea()
        self.keyboard_area.set_size_request(KEY_WIDTH + KEY_SPACE + KEY_SPACE, 128 * CURSOR_HEIGHT)
        self.keyboard_area.show()
        
        self.keyboard_sw.add_with_viewport(self.keyboard_area)
        self.pack_start(self.keyboard_sw, False, False, 0)

        self.midi_keyboard_timeout = 0
        # Notes edition and visualization

        # Scrolling widget
        self.notes_sw = gtk.ScrolledWindow()
        
        # Note zone
        self.notes_area = gtk.DrawingArea()
        
        self.notes_area.set_flags(gtk.CAN_FOCUS)
        self.notes_area.set_size_request(self.pat.get_len() * TICKS_PER_BEAT * CURSOR_WIDTH + 32, 128 * CURSOR_HEIGHT)
        self.notes_area.show()

        self.notes_sw.add_with_viewport(self.notes_area)
        self.pack_start(self.notes_sw, True, True, 0)

        # Vertical and horizontal adjustments are weird GTK widgets to control
        # Scrolled areas and receice events.

        self.keyboard_vadj = self.keyboard_sw.get_vadjustment()
        self.keyboard_sw.show()
        self.notes_hadj = self.notes_sw.get_hadjustment()
        self.notes_vadj = self.notes_sw.get_vadjustment()

        # In the initialization first time we move the adjustment to the middle
        # and check midi input settings.
        self.notes_area_first_draw = True

        self.keyboard_vadj.connect('value_changed', self.notes_area_vertical_value_changed)
        self.notes_vadj.connect('value_changed', self.notes_area_vertical_value_changed)
        self.notes_hadj.connect('value_changed', self.notes_area_horizontal_value_changed)
        self.notes_sw.show()

        # Connect event handlers and set event receive masks
        self.keyboard_area.connect("expose-event", self.keyboard_area_expose)
        self.keyboard_area.connect("motion_notify_event", self.keyboard_area_motion_notify)
        self.keyboard_area.connect("button_press_event", self.keyboard_area_button_press)
        self.keyboard_area.set_events(
            gtk.gdk.BUTTON_PRESS_MASK | 
            gtk.gdk.BUTTON_RELEASE_MASK |
            gtk.gdk.POINTER_MOTION_MASK )


        self.notes_area.connect("key-press-event", self.notes_area_key_press)
        self.notes_area.connect("key-release-event", self.notes_area_key_release)
        self.notes_area.connect("expose-event", self.notes_area_expose)
        self.notes_area.connect("motion_notify_event", self.notes_area_motion_notify)
        self.notes_area.connect("button_press_event", self.notes_area_button_press)
        self.notes_area.connect("button_release_event", self.notes_area_button_release)
        self.notes_area.set_events(
            gtk.gdk.BUTTON_PRESS_MASK | 
            gtk.gdk.BUTTON_RELEASE_MASK |
            gtk.gdk.POINTER_MOTION_MASK |
            gtk.gdk.KEY_PRESS_MASK |
            gtk.gdk.KEY_RELEASE_MASK |
            gtk.gdk.FOCUS_CHANGE_MASK |
            gtk.gdk.ENTER_NOTIFY_MASK |
            gtk.gdk.LEAVE_NOTIFY_MASK |
            gtk.gdk.SCROLL_MASK |
            gtk.gdk.POINTER_MOTION_MASK)
        #self.notes_area.add_events(gtk.gdk.POINTER_MOTION_MASK)
        
        self.notes_area.set_flags(gtk.CAN_FOCUS)

    def load_track(self, track_widget):
        # Our parent T
        self.track_widget = track_widget

        # MIDI Synth Connection        
        self.conn = self.track_widget.container.container.conn

        # Player object
        self.player = self.track_widget.player

        # Pattern data object
        self.pat = self.track_widget.pat

        # Track data object
        self.track = self.track_widget.track


    def set_controller_editor_widget(self, widget):
        self.controller_editor_widget = widget

    def set_pitchbend_editor_widget(self, widget):
        self.pitchbend_editor_widget = widget

    """
    ********************************************************
    EVENT HANDLERS SECTION OF THE CLASS.
    ********************************************************
    """

    def _key_hook_handler(self, event, action='activate'):
        """
        Fitler event information and find the right event handler
        """

        # If we are playing the pattern, update position before anything else is done
        if self.player.playing():
            self.move_cursor(self.player.get_pos())
           
        # Get key value and state (modifiers, like CTRL, ALT, etc) 
        val = event.keyval
        state = event.state & EVENT_MODIFIER_FILTER

        # Check for hooks on this key/modifier combination
        for hook in self.piano_roll_key_event_hooks:
            if state == hook.modifiers and val in hook.keys:
                # If found, run hook and exit returning True
                if action == 'activate':
                    hook.activate(self, val)
                else:
                    hook.deactivate(self, val)
                return True

    def notes_area_key_press(self, widget, event):
        """
        Call the right Key Hook activate method for the pressed key
        """

        return self._key_hook_handler(event)
        
    def notes_area_key_release(self, widget, event):
        """
        Call the right Key Hook deactivate method for the pressed key
        """

        return self._key_hook_handler(event, action='deactivate')

    def notes_area_expose(self, notes_area, event):
        """
        Handles Expose event on piano roll (where the notes are)
        """
        self.paint_roll()
        self.notes_area_paint_selection()

    def keyboard_area_expose(self, area, event):
        """
        Paint Piano Keys on Expose event
        """

        area.window.draw_rectangle(self.colors['background'], True, 0, 0, KEY_WIDTH + KEY_SPACE + KEY_SPACE, 128 * CURSOR_HEIGHT)

        for i in range(128):
            area.window.draw_rectangle(self.colors['keyboard'], False, 
                        0, i * CURSOR_HEIGHT, 
                        KEY_WIDTH + KEY_SPACE, CURSOR_HEIGHT)
            if i % 12 in [5, 7, 10, 0 , 2]:
                area.window.draw_rectangle(self.colors['keyboard'], True, 
                            0, i * CURSOR_HEIGHT + 2, 
                            KEY_WIDTH + KEY_SPACE - 1, KEY_HEIGHT - KEY_SPACE - 1)
        return True

    def keyboard_area_motion_notify(self, widget, event):
        """
        Keep track of the note that the mouse is pointing on the piano
        by painting it blue. 
        """

        note = 128 -  int(event.y / CURSOR_HEIGHT)

        self.keyboard_paint_note(self.mouse_note, self.colors['background'])

        if event.state & gtk.gdk.BUTTON1_MASK:

            if self.mouse_note != note:
                synth_conn = self.track.conn.get_port(self.track.track.get_synth())

                if synth_conn != None: 
                    synth_conn.note_on(note, self.track.track.get_port(), self.track.volume)
                    time.sleep(0.025)
                    synth_conn.note_off(note, self.track.track.get_port())

        self.mouse_note = note
        self.keyboard_paint_note(self.mouse_note, self.colors['cursor'])

    def keyboard_area_button_press(self, widget, event):
        """
        Make a sound when you click on the keyboard on screen at the side
        of the piano roll
        """

        self.notes_area.grab_focus()

        note = 128 -  int(event.y / CURSOR_HEIGHT)
        synth_conn = self.conn.get_port(self.track.get_synth())

        if synth_conn != None: 
            synth_conn.note_on(note, self.track.get_port(), self.volume)
            time.sleep(0.025)
            synth_conn.note_off(note, self.track.get_port())

    def notes_area_button_press(self, widget, event):
        """
        Handle mouse input on the notes area
        """
        self.notes_area.grab_focus()
        
        pos = int(event.x / CURSOR_WIDTH)
        diff = pos % self.note_size
        pos = pos - diff
        self.mouse_pos = pos

        note = 128 -  int(event.y / CURSOR_HEIGHT)
        self.mouse_note = note
        synth_conn = self.conn.get_port(self.track.get_synth())

        state = event.state

        if state == EVENT_MODIFIER_NONE:
            self.move_cursor(pos)
            self.sel_pos_start = pos
            self.sel_note_start = note
            self.update_selection(pos, note, pos + self.note_size, note)
        elif state == EVENT_MODIFIER_SHIFT:
            #Add it to track
            if self.recording:
                self.mouse_painting = 1
                self.paint_note(note, pos, self.note_size)
                if synth_conn != None: 
                    synth_conn.note_on(note, self.track.get_port(), self.volume)
                    time.sleep(0.05)
                    synth_conn.note_off(note, self.track.get_port())
        
    def notes_area_button_release(self, widget, event):
        state = event.state

        if self.mouse_painting:
            self.add_note(self.mouse_note, self.mouse_pos, self.note_size, self.volume)
            
        self.mouse_painting = 0
        
    def notes_area_motion_notify(self, widget, event):
        synth_conn = self.conn.get_port(self.track.get_synth())
        
        micropos = int(event.x / CURSOR_WIDTH)
        diff = micropos % self.note_size
        pos = micropos - diff

        note = 128 -  int(event.y / CURSOR_HEIGHT)
        
        state = event.state
        
        if self.mouse_painting:

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
        elif state == EVENT_MOUSE_CTRL_SHIFT:
            pos_diff =  pos - self.mouse_pos
            note_diff =  note - self.mouse_note            
            if pos_diff or note_diff:
                self.move_selection(self.sel_pos_from + pos_diff, self.sel_note_from + note_diff)
        elif state == EVENT_MOUSE_CTRL:
            if micropos - self.mouse_micropos:
                self.resize_selection(micropos - self.mouse_micropos)
        elif state == EVENT_MOUSE:
            if pos >= self.sel_pos_start:
                selpos = pos + self.note_size
            else:
                selpos = pos
            self.sel_pos_end = selpos
            self.sel_note_end = note
            self.update_selection(self.sel_pos_start, self.sel_note_start, 
                selpos, note)
                    

        self.keyboard_paint_note(self.mouse_note, self.colors['background'])
        
        self.mouse_micropos = micropos
        self.mouse_pos = pos
        self.mouse_note = note

        self.keyboard_paint_note(self.mouse_note, self.colors['cursor'])


    def handle_midi_timer(self, timeout):
        
        if self.midi_keyboard_timeout == timeout:
            return
        
        if self.midi_keyboard_listen:
            gobject.source_remove(self.midi_keyboard_listen)

        self.cursor_timeout = timeout
        self.midi_keyboard_listen = gobject.timeout_add(timeout, self.handle_midi_input)
    
    #This is the MIDI Input handler, runs on the scheduled timer self.midi_keyboard_listen
    def handle_midi_input(self):
        
        #Sync player cursor with screen cursor if playing
        if self.player.playing():
            pos = self.player.get_pos()
            self.move_cursor(pos)
            self.handle_midi_timer(10)
        else:
            self.handle_midi_timer(50)
        
        synth_conn = self.conn.get_port(self.track.get_synth())

        #MIDI Input
        while self.conn.midi_input_event_pending():
            event = self.conn.get_midi_input_event()
            self.handle_midi_event(event)
            

        return True

    def handle_midi_event(self, event):
        """
        Process the midi event
        """
        synth_conn = self.conn.get_port(self.track.get_synth())

        #Normalize events
        if (event['type'] == alsaseq.EVENT_NOTE_ON and 
            not event['data']['note']['velocity']):
            event['type'] == alsaseq.EVENT_NOTE_OFF

        if event['type'] == alsaseq.EVENT_NOTE_ON:
            note = event['data']['note']['note']
            velocity = event['data']['note']['velocity']

            #Check if we are using a scale filter for notes
            if self.scale:
                if self.scale_var:
                    scale = [(x+(self.scale-1))%12 for x in SCALE_MIN]
                else:
                    scale = [(x+(self.scale-1))%12 for x in SCALE_MAJ]

                if not (note % 12) in scale:
                    return

            #How many keys pressed? Used for step editing chords
            self.midi_keyboard_count += 1
            
            #Are we making changes?
            if self.recording:
                #In case we are playing we qantize the note
                pos = self.cursor_pos - (self.cursor_pos % self.note_size)

                pat_len = self.pat.get_len()*TICKS_PER_BEAT
                
                if self.track_widget.cbo_vol.get_active() <= 7:
                    velocity = self.volume

                if self.player.playing():
                    # Keep track of the start
                    self.notes_insert_position_velocity[note] = (pos, velocity)
                    self.paint_note(note, pos % pat_len , self.note_size)
                else:
                    #If not playing, we add the note right now
                    self.add_note(note, pos, self.note_size, velocity)

            if synth_conn != None: synth_conn.note_on(note, self.track.get_port(), velocity)
                    
        elif event['type'] == alsaseq.EVENT_NOTE_OFF:
            note = event['data']['note']['note']
            self.midi_keyboard_count -= 1
            
            if self.recording:
                if self.player.playing():
                    (pos, velocity) = self.notes_insert_position_velocity[note]
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
                    self.move_cursor(self.cursor_pos + self.note_size)

            if synth_conn != None: synth_conn.note_off(note, self.track.get_port())
        elif event['type'] == alsaseq.EVENT_CONTROLLER:
            self.controller_editor_widget.handle_midi_input(self.cursor_pos, event['data']['control']['param'], event['data']['control']['value'])
        elif event['type'] == alsaseq.EVENT_PITCH:
            self.pitchbend_editor_widget.handle_midi_input(self.cursor_pos, event['data']['control']['value'])

    def notes_area_horizontal_value_changed(self, adj):
        value = adj.get_value()
        self.container.controller_editor_widget.set_scroll_pos(value)
        self.container.pitchbend_editor_widget.set_scroll_pos(value)

    def notes_area_vertical_value_changed(self, adj):
        value = adj.get_value()
        self.keyboard_vadj.set_value(value)
        self.notes_vadj.set_value(value)
        
    """
    ********************************************************
    EDITING LOGIC SECTION OF THE CLASS.
    ********************************************************
    """
                
    def move_cursor(self, pos):
        """
        Move insert/play cursor to an arbitrary position
        """

        #We calculate the screensize for beat ticks, based on a 1/8 max subdiv
        cursor_pos_x = pos_to_x(self.cursor_pos)

        #Warp around (both directions)
        pos = pos % (self.pat.get_len()*TICKS_PER_BEAT)
        pos_x = pos_to_x(pos)

        scroll_size, page_size, pages = self.get_notes_area_dimensions() 
        #Adjust scrollbar to see the notes playing
        if (cursor_pos_x/page_size) != (pos_x/page_size):
            mypage = (pos_x/page_size)
            if mypage == 0:
                self.hadj.set_value(0) 
            elif mypage >= (pages-1):
                self.hadj.set_value(scroll_size-page_size-BEAT_WIDTH*4)
            else:
                self.hadj.set_value(page_size*(mypage-1)) 

        self.notes_area_clear_cursor(self.cursor_pos)

        self.notes_area_paint_notes(128, 0, self.cursor_pos, self.cursor_pos+1)

        self.cursor_pos = pos
        self.notes_area_paint_cursor(self.cursor_pos)

    def clear_selection(self):
        """
        Repaint selection area and draw cursor and notes as needed
        """

        self.notes_area_paint_grid(self.sel_note_from, self.sel_note_to,  self.sel_pos_from, self.sel_pos_to)

        if self.sel_pos_from <= self.cursor_pos <= self.sel_pos_to * self.note_size:
            self.notes_area_paint_cursor(self.cursor_pos, self.sel_note_from, self.sel_note_to)

        self.notes_area_paint_notes(self.sel_note_from, self.sel_note_to,  self.sel_pos_from, self.sel_pos_to)

    #Update selected notes
    def update_selection(self, pos_from, note_from, pos_to, note_to):
        #Clear selection box
        self.clear_selection()

        #Update Selection Coords
        self.sel_pos_from = max(0, min(pos_from, pos_to))
        self.sel_note_from = max(note_from, note_to)
        self.sel_pos_to = min(self.pat.get_len()*TICKS_PER_BEAT ,max(pos_from, pos_to))
        self.sel_note_to = min(note_from, note_to)

        #Paint Selection
        self.notes_area_paint_selection()

        #Update selected notes
        self.selection = []
        #Delete old notes
        for (note, pos, duration, volume) in self.track.get_notes():
            if (self.sel_note_from >= note >= self.sel_note_to and 
                    self.sel_pos_from <= pos < self.sel_pos_to): 

                self.selection.append( (note, pos, duration, volume) )
    
    def move_selection(self, x, y):
        diff_pos = x - self.sel_pos_from
        diff_note = y - self.sel_note_from 

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
        
        self.sel_pos_from = x
        self.sel_note_from = y
        self.sel_pos_to = self.sel_pos_to + diff_pos
        self.sel_note_to = self.sel_note_to + diff_note

        self.notes_area_paint_selection()

    
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
            text += "%i, %i, %i, %i\n" % (note-self.sel_note_from, pos-self.sel_pos_from, duration, volume)
            
            if (note, pos, duration, volume) in self.track.get_notes():
                self.paint_note(note, pos, duration)

        text += "EndNotes\n"
        
        clipboard = gtk.clipboard_get(gtk.gdk.SELECTION_CLIPBOARD)
        clipboard.set_text(text)        

    def copy_selection(self):
        text = "Notes\n"
        
        for (note, pos, duration, volume) in self.selection:
            text += "%i, %i, %i, %i\n" % (note-self.sel_note_from, pos-self.sel_pos_from, duration, volume)

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
                    self.add_note( int(note)+self.sel_note_from, int(pos)+self.sel_pos_from, int(duration), int(volume) )

    def add_note(self, note, pos, duration=1, volume=127, overlap=False, mono=None):
        len = self.pat.get_len()*TICKS_PER_BEAT
       
        n_start = pos % len 
        n_end = n_start + duration

        #Paint it
        self.paint_note(note, n_start, duration)
        if mono is None:
            mono = self.rec_mono

        if mono:
            # Remove other notes
            for (snote, stime, sduration, svolume) in list(self.track.get_notes()):
                o_start = stime
                o_end = stime + sduration
                
                if o_end <= n_start or o_start >= n_end:
                    continue

                self.del_note(snote, stime, sduration)

                if o_start < n_start:
                    self.add_note(snote, o_start, n_start - o_start, svolume, mono=False)

                if o_end > n_end:
                    self.add_note(snote, n_end, o_end - n_end, svolume, mono=False)


        #Add it to track
        self.track.add_note(note, n_start, duration, volume, overlap)

    #Deletes a note from the grid, the track and the sequence, and stops it's sound
    def del_note(self, note, pos, duration=1):
        len = self.pat.get_len()*TICKS_PER_BEAT

        self.track.del_note(pos % len, note, duration)

        self.clear_note(note, pos % len, duration)
        
        synth_conn = self.conn.get_port(self.track.get_synth())
        if synth_conn != None: 
            port = self.track.get_port()
            synth_conn.note_off(note, port)

    """
    ********************************************************
    GRAPHICS DRAWING SECTION OF THE CLASS.
    ********************************************************
    """

    #Paints a single note in the piano keyboard
    def keyboard_paint_note(self, note, color):

        i = 128 - note 
        # Paint background of the note in chosen color
        self.keyboard_area.window.draw_rectangle(color, True, 
                    1, i * CURSOR_HEIGHT + 1, 
                    KEY_WIDTH + KEY_SPACE -1, CURSOR_HEIGHT - 2)
        
        # If note is an alteration paint it gray inside
        if i % 12 in [0, 2, 5, 7, 10]:
            self.keyboard_area.window.draw_rectangle(self.colors['keyboard'], True, 
                        0, i * CURSOR_HEIGHT + 2, 
                        KEY_WIDTH + KEY_SPACE - 1, KEY_HEIGHT - KEY_SPACE - 1)

    #Paints the piano roll (Where the notes are)
    def paint_roll(self):
        # Sometimes GTK is not ready... I don't know anything more about that.
        if self.notes_area.window == None:
            return

        self.set_colors()
       
        pat_len = self.pat.get_len()

        self.notes_area_paint_grid(128, 0,  0, pat_len*TICKS_PER_BEAT)
        self.notes_area_paint_notes(128, 0,  0, pat_len*TICKS_PER_BEAT)
       
        self.move_cursor(self.cursor_pos)
        
        # Do one time initialization
        if self.notes_area_first_draw:
            self.notes_vadj.set_value(32*(KEY_HEIGHT+KEY_SPACE))
            if self.midi_keyboard_listen:
                gobject.source_remove(self.midi_keyboard_listen)
            self.midi_keyboard_listen = gobject.timeout_add(50, self.handle_midi_input)
            self.notes_area_first_draw = False

        return True

    def paint_note(self, note, pos, duration=1):
        """
        Paint an individual note in the piano roll
        """
        pat_len = self.pat.get_len()*TICKS_PER_BEAT
        
        note = 128 - note
        self.notes_area.window.draw_rectangle(
                self.colors['note'], True, 
                (pos % pat_len) * CURSOR_WIDTH + 2, 
                note * CURSOR_HEIGHT + 2,
                duration * CURSOR_WIDTH -2,
                KEY_HEIGHT-2)
        
    def clear_note(self, note, pos, duration=1):
        """
        Repaint empty grid in the place of a note
        """
        self.notes_area_paint_grid(note, note, pos, pos+duration)        

    def notes_area_paint_notes(self, note_from, note_to, pos_from, pos_to):
        """
        Paint notes in a defined range
        """
        for (note, pos, duration, volume) in self.track.get_notes():
            if self.debug:
                print note, pos, pos+duration, note_from, note_to,pos_from, pos_to
            if (note_from >= note >= note_to and 
                pos_to >= pos and 
                pos_from <= pos+duration):
                self.paint_note(note, pos, duration)

    def notes_area_paint_selection(self):
        """
        Paint the selection frame
        """

        x_from = pos_to_x(self.sel_pos_from)
        x_to = pos_to_x(self.sel_pos_to)
        y_from = note_to_y(self.sel_note_from)
        y_to = note_to_y(self.sel_note_to-1)

        self.notes_area.window.draw_rectangle(self.colors['cursor'], False, 
                x_from, y_from, x_to-x_from, y_to-y_from)

    def notes_area_paint_cursor(self, pos, note_from=128, note_to=0, color='cursor'):
        """
        Paint insert/play cursor at pos. Default to full paint of cursor.
        """
        y_from =(128-note_from) * CURSOR_HEIGHT
        y_to =(128-note_to+1) * CURSOR_HEIGHT
        x = pos * CURSOR_WIDTH 
        self.notes_area.window.draw_line(self.colors[color], x, y_from, x, y_to)

    def notes_area_clear_cursor(self, pos):
        """
        Paint the grid at position pos
        """
        if pos % self.note_size == 0:
            color = 'foreground' if pos % TICKS_PER_BEAT == 0 else 'grid'
            self.notes_area_paint_cursor(pos, color=color)
        else:
            self.notes_area_paint_cursor(pos, color='background')
            self.notes_area_paint_horizontal_grid_lines(128, 0, pos, pos)

    def notes_area_paint_horizontal_grid_lines(self, note_from, note_to, pos_from, pos_to):
        """
        Paint horizontal lines.
        """
        x_from= pos_from * CURSOR_WIDTH
        x_to = pos_to * CURSOR_WIDTH

        # From bottom of the last note to top of the first one.
        for i in range (note_to - 1, note_from+1):
            y = (128 - i) * CURSOR_HEIGHT

            if self.debug:
                self.notes_area.window.draw_line(self.colors['debug2'], x_from, y, x_to, y)
            else: 
                self.notes_area.window.draw_line(self.colors['grid'], x_from, y, x_to, y)


    def notes_area_paint_vertical_grid_lines(self, note_from, note_to, pos_from, pos_to):
        """
        Paint vertical bars to mark beat and chosen grid size.
        """
        y_from =(128-note_from) * CURSOR_HEIGHT
        y_to =(128-note_to+1) * CURSOR_HEIGHT
        if self.debug:
            print pos_from, pos_to+1
        for tmp_pos in xrange(pos_from, pos_to+self.note_size, self.note_size):
            x = tmp_pos * CURSOR_WIDTH

            #Draw hard beat on black
            color = 'grid' if x % (BEAT_WIDTH * CURSOR_WIDTH) else 'foreground'
            if self.debug:
                color = 'debug2'

                print x, y_from, y_to

            self.notes_area.window.draw_line(self.colors[color], x, y_from, x, y_to)
                
    def notes_area_paint_grid(self, note_from, note_to, pos_from, pos_to):
        """
        Paint an empty grid between two notes and two pattern positions.
        Will draw vertical bars to mark beat and chosen grid size and horizontal
        lines to separate notes.
        """

        x_from= pos_from * CURSOR_WIDTH
        x_to = pos_to * CURSOR_WIDTH
        x_width = x_to-x_from
        y_from =(128-note_from) * CURSOR_HEIGHT
        y_to =(128-note_to+1) * CURSOR_HEIGHT
        y_height = y_to-y_from
        if self.debug:
            print note_from, y_from, note_to, y_to


        color = self.colors['background']
        if self.debug:
            color = self.colors['debug1']

        self.notes_area.window.draw_rectangle(color, True, x_from, y_from, x_width, y_height)

        self.notes_area_paint_horizontal_grid_lines(note_from, note_to, pos_from, pos_to)
        self.notes_area_paint_vertical_grid_lines(note_from, note_to, pos_from, pos_to)

    def set_colors(self):
        """
        Set the palette of colors.
        """

        def set_color(color_name, color_hex_code):
            """
            Allocate a color and return it
            """
            if color_name not in self.colors:
                color = colormap.alloc_color(color_hex_code, True, True)
                gc = self.notes_area.window.new_gc()
                gc.set_foreground(color)
                self.colors[color_name] = gc

        colormap = self.notes_area.get_colormap()
        #style = notes_area.get_style()
        #self.gc = style.fg_gc[gtk.STATE_NORMAL]

        set_color('keyboard', '#000000')
        set_color('foreground', '#C0C0C0')
        set_color('background', '#FFFFFF')
        set_color('grid', '#E0E0FF')
        set_color('note', '#ffa235')
        set_color('cursor', '#0000FF')
        set_color('debug1', '#FF00FF')
        set_color('debug2', '#00FFFF')

    def get_notes_area_dimensions(self):
        """
        Return the dimmensions of the notes area. Used to paint
        selections and expose events
        """
        alloc = self.notes_area.get_allocation()
        notes_area_width = alloc.width-alloc.x
        scroll_size = notes_area_width-32
        page_size = notes_area_width-(BEAT_WIDTH*4)
        pages = scroll_size / page_size

        if scroll_size % page_size:
            pages = pages + 1

        return scroll_size, page_size, pages

def note_to_y(note):
    return (128 - note) * CURSOR_HEIGHT

def pos_to_x(pos):
    return pos * CURSOR_WIDTH
