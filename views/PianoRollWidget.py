import gtk
from gtk import keysyms as key
import gobject

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
            widget.move_cursor(
                widget.cursor_pos +
                (widget.cursor_pos % widget.note_size or widget.note_size) *
                (1 if keycode == key.Right else -1)
            )
            selection_y = widget.selection_y
        else:
            selection_y = widget.selection_y + (1 if keycode == key.Up else -1)

        widget.update_selection(widget.cursor_pos, selection_y, 1, 1)

class KeyDeletePiano(KeyEventHook):
    keys = [key.Delete]

    def activate(self, widget, keycode):
        if not widget.deleting:
            widget.deleting = 1

    def deactivate(self, widget, keycode):
        #Delete only if recording and don't delete here if playing
        if not widget.player.playing() and widget.recording:
            #Full delete?
            if widget.deleting == 1:
                del_notes = []
                for item in widget.track.get_notes(): del_notes.append(item)
                for (dnote, dpos, dduration, dvolume) in del_notes:
                    if dpos == widget.cursor_pos:
                        widget.del_note(dnote, dpos, dduration)

            #Move cursor manually 
            if (widget.cursor_pos % widget.note_size):
                widget.move_cursor(widget.cursor_pos + widget.note_size - (widget.cursor_pos % widget.note_size))
            else:
                widget.move_cursor(widget.cursor_pos + widget.note_size)

            widget.update_selection(widget.cursor_pos, widget.selection_y, 1, 1)
        
        #Always clear delete note
        widget.deleting = 0
            
class KeyBackspacePiano(KeyEventHook):
    keys = [key.BackSpace]

    def activate(self, widget, keycode):
        #Delete only if recording and don't delete here if playing
        if not widget.player.playing() and widget.recording:

            #Move cursor manually 
            if (widget.cursor_pos % widget.note_size):
                widget.move_cursor(widget.cursor_pos - (widget.cursor_pos % widget.note_size))
            else:
                widget.move_cursor(widget.cursor_pos - widget.note_size * widget.step_size)

            #Delete
            del_notes = []
            for item in widget.track.get_notes(): del_notes.append(item)
            for (dnote, dpos, dduration, dvolume) in del_notes:
                if dpos == widget.cursor_pos:
                    widget.del_note(dnote, dpos, dduration)

            #I have drink a lot of wine now... so i'm in lazy mode. repainting cursor the bad way
            widget.move_cursor(widget.cursor_pos)

            widget.update_selection(widget.cursor_pos, widget.selection_y, 1, 1)
                    

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
    keys = [key.m, key.s, key.r, key.p]

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
            if widget.recording:
                widget.track_widget.chk_recording.set_active(0)
                widget.recording = 0
            else:
                widget.track_widget.chk_recording.set_active(1)
                widget.recording = 1
        #Mute trakcs
        elif keycode == key.m:
            #Muted track is NOT enabled... 
            widget.track_widget.chk_mute_track.set_active(widget.track.enabled)

class KeySelection(KeyEventHook):
    """
    Select notes on the piano roll with the keyboard
    """

    modifiers = EVENT_MODIFIER_SHIFT
    keys = [key.Left, key.Right, key.Up, key.Down]

    def activate(self, widget, keycode):
        diff_width = 0
        diff_height = 0

        #Change selection size
        if keycode == key.Up and widget.selection_height > 1:
            diff_height = -1
        elif keycode == key.Down:
            diff_height = 1
        elif keycode == key.Left and widget.selection_width > 1:
            diff_width = -1
        #horrible formula to avoid going too far... must think about this and make it clear
        elif keycode == key.Right and widget.selection_x + widget.selection_width * widget.note_size < widget.pat.get_len()*TICKS_PER_BEAT:
            diff_width = 1
                    
        #Update Selection
        widget.update_selection(
            widget.selection_x,
            widget.selection_y, 
            widget.selection_width + diff_width,
            widget.selection_height + diff_height
        )

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
            widget.selection_x + pos_shift.get(keycode, 0), 
            widget.selection_y + note_shift.get(keycode, 0)
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
                widget.add_note(widget.selection_y, pos, widget.note_size, widget.volume)
            
            synth_conn = widget.conn.get_port(widget.track.get_synth())
            if synth_conn != None: synth_conn.note_on(widget.selection_y, widget.track.get_port(), widget.volume)
            widget.vk_space = 1

    def deactivate(self, widget, keycode):
        synth_conn = widget.conn.get_port(widget.track.get_synth())
        if synth_conn != None: synth_conn.note_off(widget.selection_y, widget.track.get_port())
        widget.vk_space = 0
                
class KeyVirtualPiano(KeyEventHook):
    """
    Handle virtual keyboard emulation so people without a midi controller
    can have fun too.
    """

    keys = VIRTUAL_KEYBOARD

    def activate(self, widget, keycode):
        key_index = VIRTUAL_KEYBOARD.index(keycode)
        if widget.scale:
            if widget.scale_var:
                scale = [(x+(widget.scale-1))%12 for x in SCALE_MIN]
            else:
                scale = [(x+(widget.scale-1))%12 for x in SCALE_MAJ]

            if not (key_index % 12) in scale:
                return True
                
        #If not key already pressed
        if widget.vk_status[key_index] == 0:
            note = (widget.octave+60) + key_index
            
            #Are we making changes?
            if widget.recording:
            
                #In case Del is pressed
                if widget.deleting:
                    #Remember that we are "selected" deleting
                    widget.deleting = 2
                    
                    #If not in playing mode Delete note now, else we wait the cursor to do the work
                    if not widget.player.playing():
                        for (dnote, dpos, dduration, dvolume) in widget.track.get_notes():
                            if dpos == widget.cursor_pos and dnote == note:
                                widget.del_note(dnote, dpos, dduration)
                else:
                    if widget.player.playing():
                        #if we are playing, we must qantize
                        beat_size = widget.note_size
                        diff = widget.cursor_pos % beat_size
                        pos = widget.cursor_pos - diff
                        pat_len = widget.pat.get_len()*TICKS_PER_BEAT
                        #Live recording. Save position, velocity and paint the start
                        widget.notes_start_position_velocity[note] = (pos, widget.volume)
                        widget.paint_note(note, pos % pat_len , widget.note_size)
                            
                    else:
                        pos = widget.cursor_pos
                        #Add it to track
                        widget.add_note(note, pos, widget.note_size, widget.volume)
                                                
                    #Update Selection
                    widget.update_selection(pos, note, widget.selection_width, widget.selection_height)
                    
            #If not Deleting let's make noise
            if not widget.deleting:
                synth_conn = widget.conn.get_port(widget.track.get_synth())
                if synth_conn != None: synth_conn.note_on(note, widget.track.get_port(), widget.volume)
            
            #Keyboard status, to avoid repetition.
            widget.vk_status[key_index] = 1
            widget.vk_count = widget.vk_count + 1

    def deactivate(self, widget, keycode):
        key_index = VIRTUAL_KEYBOARD.index(keycode)

        if widget.scale:
            if widget.scale_var:
                scale = [(x+(widget.scale-1))%12 for x in SCALE_MIN]
            else:
                scale = [(x+(widget.scale-1))%12 for x in SCALE_MAJ]

            if not (key_index % 12) in scale:
                return True

        note = (widget.octave+60) + key_index
        
        #Update Keyboard Status
        widget.vk_status[key_index] = 0
        
        if widget.vk_count > 0:
            widget.vk_count = widget.vk_count - 1

        if not widget.deleting:

            #Stop the noise
            synth_conn = widget.conn.get_port(widget.track.get_synth())
            if synth_conn != None: synth_conn.note_off(note, widget.track.get_port())
        
            if widget.recording:
                if widget.player.playing():
                    (pos, velocity) = widget.notes_start_position_velocity[note]
                    duration = widget.cursor_pos - (widget.cursor_pos % widget.note_size) - pos
                    #Cut note duration at end of pattern
                    if duration < 0:
                        duration = widget.pat.get_len()*TICKS_PER_BEAT - pos
                    #Minimal size is note size (grid size)
                    if duration < widget.note_size: 
                        duration = widget.note_size
                    
                    #Delete original temorary note    
                    widget.del_note(note,pos)
                    #Add new real note
                    widget.add_note(note, pos, duration, velocity)
                else:
                    #If not playing move cursor manually and recording
                    if widget.vk_count == 0:
                        if (widget.cursor_pos % widget.note_size):
                            widget.move_cursor(widget.cursor_pos + widget.note_size - (widget.cursor_pos % widget.note_size))
                        else:
                            widget.move_cursor(widget.cursor_pos + widget.note_size * widget.step_size)
                            
                        widget.update_selection(widget.cursor_pos, widget.selection_y, 1, 1)

class PianoRollWidget(gtk.HBox):

    # Which events are handled by hooks for the piano roll area
    piano_roll_key_event_hooks = [
        KeyMoveCursor(),
        KeyDeletePiano(),
        KeyBackspacePiano(),
        KeyGridSize(),
        KeyOctaveShift(),
        KeyResizeSelection(),
        KeyCutCopyPaste(),
        KeyPlayControls(),
        KeySelection(),
        KeySelectionMove(),
        KeyInputVolume(),
        KeyInsertNote(),
        KeyVirtualPiano(),
    ]

    def __init__(self, track_widget):
        super(PianoRollWidget, self).__init__()

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

        # Piano roll colors
        self.gc_foreground = None
        self.gc_background = None

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

        # Selective deletion flag while playing (a feature borrowed from Alesis SR16)
        self.deleting = 0
        
        # Input volume
        self.volume = 127
        
        # Scale helpers variables (Help prevent inserting notes out of scale)
        self.scale = 0
        self.scale_var = 0
        

        # Reading MIDI Keyboard variables
        self.midi_keyboard_listen = 0
        self.midi_keyboard_count = 0
        
        # This handles when a note was pressed (in virt keyb or midi keyb) for
        # note insert in live recording by keeping track of the initial place
        # where the note was inserted.
        self.notes_insert_position_velocity = [(-1,0)]*127

        #Cursor position
        self.cursor_pos = 0
        
        # Selection is the tool to move, copy, paste and delete notes
        self.selection_x = 0
        self.selection_y = 60
        self.selection_width = 1
        self.selection_height = 1
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
        self.adjust = 1

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



    def notes_area_key_press(self, widget, event):
        #local alias, to make things more readable (and writeable)

        if self.player.playing():
            self.move_cursor(self.player.get_pos())
            
        val = event.keyval
        state = event.state

        # Check for hooks on this key/modifier combination
        for hook in self.piano_roll_key_event_hooks:
            if state == hook.modifiers and val in hook.keys:
                # If found, run hook and exit returning True
                hook.activate(self, val)
                return True
        
    def notes_area_key_release(self, widget, event):
        #local alias, to make things more readable (and writeable)

        if self.player.playing():
            self.move_cursor(self.player.get_pos())

        val = event.keyval
        state = event.state
        
        # Check for hooks on this key/modifier combination
        for hook in self.piano_roll_key_event_hooks:
            if state == hook.modifiers and val in hook.keys:
                # If found, run hook and exit returning True
                hook.deactivate(self, val)
                return True

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

    #Handles Expose event on piano roll (where the notes are)
    def notes_area_expose(self, notes_area, event):
        style = notes_area.get_style()
        self.gc = style.fg_gc[gtk.STATE_NORMAL]

        #Set variables needed for paging
        scroll_size, page_size, pages = self.get_notes_area_dimensions()

        self.paint_roll()
        self.notes_area_paint_selection()
        

    def notes_area_paint_selection(self):
        note_start = 128 - self.selection_y
        note_end = 128 - (self.selection_y + self.selection_height)

        self.notes_area.window.draw_rectangle(self.gc_cursor, False, 
                self.selection_x * CURSOR_WIDTH, 
                note_start * CURSOR_HEIGHT,
                (self.selection_width) * CURSOR_WIDTH * self.note_size,
                self.selection_height * CURSOR_HEIGHT)

    #Paint Piano Keys on expose event
    def keyboard_area_expose(self, area, event):
        style = area.get_style()
        self.gc = self.style.fg_gc[gtk.STATE_NORMAL]

        colormap = area.get_colormap()

        color_foreground = colormap.alloc_color('#C0C0C0', True, True)
        gc_foreground = area.window.new_gc()
        gc_foreground.set_foreground(color_foreground)

        color_background = colormap.alloc_color('#FFFFFF', True, True)
        self.gc_background = area.window.new_gc()
        self.gc_background.set_foreground(color_background)

        area.window.draw_rectangle(self.gc_background, True, 0, 0, KEY_WIDTH + KEY_SPACE + KEY_SPACE, 128 * CURSOR_HEIGHT)

        for i in range(128):
            area.window.draw_rectangle(self.gc, False, 
                        0, i * CURSOR_HEIGHT, 
                        KEY_WIDTH + KEY_SPACE, CURSOR_HEIGHT)
            if i % 12 in [5, 7, 10, 0 , 2]:
                area.window.draw_rectangle(self.gc, True, 
                            0, i * CURSOR_HEIGHT + 2, 
                            KEY_WIDTH + KEY_SPACE - 1, KEY_HEIGHT - KEY_SPACE - 1)
        return True

    #Handles mouse movement for the Piano Keys
    def keyboard_area_motion_notify(self, widget, event):
        note = 128 -  int(event.y / CURSOR_HEIGHT)

        self.paint_piano_note(self.mouse_note, self.gc_background)

        if event.state & gtk.gdk.BUTTON1_MASK:

            if self.mouse_note != note:
                synth_conn = self.track.conn.get_port(self.track.track.get_synth())

                if synth_conn != None: 
                    synth_conn.note_on(note, self.track.track.get_port(), self.track.volume)
                    time.sleep(0.025)
                    synth_conn.note_off(note, self.track.track.get_port())

        self.mouse_note = note
        self.paint_piano_note(self.mouse_note, self.gc_cursor)

    #Handles mouse buttons for Piano Keys
    def keyboard_area_button_press(self, widget, event):
        self.notes_area.grab_focus()

        note = 128 -  int(event.y / CURSOR_HEIGHT)
        synth_conn = self.conn.get_port(self.track.get_synth())

        if synth_conn != None: 
            synth_conn.note_on(note, self.track.get_port(), self.volume)
            time.sleep(0.025)
            synth_conn.note_off(note, self.track.get_port())

    #Paints a single note in the piano keyboard
    def paint_piano_note(self, note, color):

        i = 128 - note 
        self.keyboard_area.window.draw_rectangle(color, True, 
                    0, i * CURSOR_HEIGHT, 
                    KEY_WIDTH + KEY_SPACE, CURSOR_HEIGHT)
        self.keyboard_area.window.draw_rectangle(self.gc, False, 
                    0, i * CURSOR_HEIGHT, 
                    KEY_WIDTH + KEY_SPACE, CURSOR_HEIGHT)
        if i % 12 in [5, 7, 10, 0 , 2]:
            self.keyboard_area.window.draw_rectangle(self.gc, True, 
                        0, i * CURSOR_HEIGHT + 2, 
                        KEY_WIDTH + KEY_SPACE - 1, KEY_HEIGHT - KEY_SPACE - 1)

    #Paints the piano roll (Where the notes are)
    def paint_roll(self):
        if self.notes_area.window == None:
            return
        
        colormap = self.notes_area.get_colormap()

        if self.gc_background == None:
            color_background = colormap.alloc_color('#FFFFFF', True, True)
            self.gc_background = self.notes_area.window.new_gc()
            self.gc_background.set_foreground(color_background)

        if self.gc_foreground == None:
            color_foreground = colormap.alloc_color('#C0C0C0', True, True)
            self.gc_foreground = self.notes_area.window.new_gc()
            self.gc_foreground.set_foreground(color_foreground)

        color_grid = colormap.alloc_color('#E0E0FF', True, True)
        self.gc_grid = self.notes_area.window.new_gc()
        self.gc_grid.set_foreground(color_grid)

        color_note = colormap.alloc_color('#ffa235', True, True)
        self.gc_note = self.notes_area.window.new_gc()
        self.gc_note.set_foreground(color_note)

        color_cursor = colormap.alloc_color('#0000FF', True, True)
        self.gc_cursor = self.notes_area.window.new_gc()
        self.gc_cursor.set_foreground(color_cursor)

        alloc = self.notes_area.get_allocation()
        
        len = self.pat.get_len() * self.grid_tick

        #We calculate the screensize for beat ticks, based on a 1/8 max subdiv
        beat_size = ((BEAT_WIDTH + KEY_SPACE * TICKS_PER_BEAT) - KEY_SPACE * self.grid_tick) / self.grid_tick + KEY_SPACE
        self.notes_area.window.draw_rectangle(self.gc_foreground, True, len * beat_size, 0, alloc.width-alloc.x, alloc.height-alloc.y)

        self.notes_area.window.draw_rectangle(self.gc_background, True, 0, 0, len * beat_size, 128 * CURSOR_HEIGHT)
        
        for i in range(128):
            self.notes_area.window.draw_line(self.gc_grid, 0, i * CURSOR_HEIGHT, len * beat_size, i * CURSOR_HEIGHT)

        for i in range(len):
            if i % self.grid_tick:
                self.notes_area.window.draw_line(self.gc_grid, i * beat_size, 0, i * beat_size ,128 * CURSOR_HEIGHT)
            else:
                self.notes_area.window.draw_line(self.gc_foreground, i * beat_size, 0, i * beat_size,128 * CURSOR_HEIGHT)

        self.notes_area.window.draw_line(self.gc_grid, len * beat_size, 0, len * beat_size,128 * CURSOR_HEIGHT)

        for (note, time, duration, volume) in self.track.get_notes():
            self.paint_note(note, time, duration)
            
        if self.adjust:
            self.notes_vadj.set_value(32*(KEY_HEIGHT+KEY_SPACE))
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
        cursor_pos_x = self.cursor_pos * CURSOR_WIDTH
        piano_height = 128 * CURSOR_HEIGHT

        #Warp around (both directions)
        pos = pos % (self.pat.get_len()*TICKS_PER_BEAT)
        pos_x = pos * CURSOR_WIDTH

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

        #Draw hard beat on black
        if (self.cursor_pos % TICKS_PER_BEAT) == 0:
            self.notes_area.window.draw_line(self.gc_foreground, cursor_pos_x, 0, cursor_pos_x, piano_height)
        elif (self.cursor_pos % self.note_size) == 0:
            self.notes_area.window.draw_line(self.gc_grid, cursor_pos_x, 0, cursor_pos_x, piano_height)
        else:
            #Clear old cursor pos and draw grid points cleaned
            self.notes_area.window.draw_line(self.gc_background, cursor_pos_x, 0, cursor_pos_x, piano_height)
            for i in range(128):
                self.notes_area.window.draw_point(self.gc_grid, cursor_pos_x, i * CURSOR_HEIGHT)

        #If notes on cursor pos, redraw them
        for (note, npos, duration, volume) in self.track.get_notes():
            if self.cursor_pos > npos and self.cursor_pos < npos+duration:
                self.paint_note(note, npos, duration)
                
        #Cursor line in cursor color
        self.notes_area.window.draw_line(self.gc_cursor, pos_x, 0, pos_x, piano_height)
        
        self.cursor_pos = pos

        
    def clear_selection(self):
        note_start = 128 - self.selection_y
        note_end = 128 - (self.selection_y + self.selection_height)

        self.notes_area.window.draw_rectangle(self.gc_grid, False, 
                self.selection_x * CURSOR_WIDTH, 
                note_start * CURSOR_HEIGHT,
                (self.selection_width * self.note_size) * CURSOR_WIDTH,
                self.selection_height * CURSOR_HEIGHT)

        for pos in [self.selection_x, self.selection_x + (self.selection_width * self.note_size)]:

            #Draw hard beat on black
            if (pos % TICKS_PER_BEAT) == 0:
                self.notes_area.window.draw_line(self.gc_foreground, 
                        pos * CURSOR_WIDTH, 
                        note_start * CURSOR_HEIGHT, 
                        pos * CURSOR_WIDTH,
                        (note_start + self.selection_height) * CURSOR_HEIGHT)

            #Cursor
            if self.cursor_pos == pos:
                self.notes_area.window.draw_line(self.gc_cursor, 
                        pos * CURSOR_WIDTH, 
                        note_start * CURSOR_HEIGHT, 
                        pos * CURSOR_WIDTH,
                        (note_start + self.selection_height) * CURSOR_HEIGHT)
        
    #On mouse button click
    def notes_area_button_press(self, widget, event):
        self.notes_area.grab_focus()
        
        pos = int(event.x / CURSOR_WIDTH)
        diff = pos % self.note_size
        pos = pos - diff

        note = 128 -  int(event.y / CURSOR_HEIGHT)
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

    
    #This is the MIDI Input handler, runs on the scheduled timer self.midi_keyboard_listen
    def handle_midi_input(self):
        
        #Sync player cursor with screen cursor if playing
        if self.player.playing():
            self.move_cursor(self.player.get_pos())
        
        synth_conn = self.conn.get_port(self.track.get_synth())

        #MIDI Input
        while self.conn.midi_input_event_pending():
            event = self.conn.get_midi_input_event()
            
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
                            if self.track_widget.cbo_vol.get_active() > 7:
                                self.notes_insert_position_velocity[note] = (pos, event['data']['note']['velocity'])
                            else:
                                self.notes_insert_position_velocity[note] = (pos, self.volume)

                            #Paint it
                            self.paint_note(note, pos % pat_len , self.note_size)
                        else:
                            #If not playing, we add the note right now
                            if self.track_widget.cbo_vol.get_active() > 7:
                                self.add_note(note, pos, self.note_size, event['data']['note']['velocity'])
                            else:
                                self.add_note(note, pos, self.note_size, self.volume)

                    if self.track_widget.cbo_vol.get_active() > 7:
                        if synth_conn != None: synth_conn.note_on(note, self.track.get_port(), event['data']['note']['velocity'])
                    else:
                        if synth_conn != None: synth_conn.note_on(note, self.track.get_port(), self.volume)
                        
                #Note off event
                elif do_note and event['data']['note']['note']:
                    self.midi_keyboard_count -= 1
                    
                    if self.recording:
                        if self.player.playing():
                            note = event['data']['note']['note']
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
            self.notes_area_paint_selection()
        return True

    def notes_area_horizontal_value_changed(self, adj):
        value = adj.get_value()
        self.container.controller_editor_widget.set_scroll_pos(value)
        self.container.pitchbend_editor_widget.set_scroll_pos(value)

    def notes_area_vertical_value_changed(self, adj):
        value = adj.get_value()
        self.keyboard_vadj.set_value(value)
        self.notes_vadj.set_value(value)

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
        self.notes_area_paint_selection()

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
        self.notes_area.window.draw_rectangle(color, True, 
                (time % len) * CURSOR_WIDTH + 1, 
                note * CURSOR_HEIGHT + 1,
                duration * CURSOR_WIDTH,
                KEY_HEIGHT)
                
    #Paint the space of a note with a color
    def paint_note_sound(self, color, note, time, duration=1):
        pat_len = self.pat.get_len()*TICKS_PER_BEAT
        
        note = 128 - note
        self.notes_area.window.draw_rectangle(color, True, 
                (time % pat_len) * CURSOR_WIDTH + 2, 
                note * CURSOR_HEIGHT + 2,
                duration * CURSOR_WIDTH -2,
                KEY_HEIGHT-2)
                
    #Paint the grid on a range
    def paint_grid(self, note_from, note_to, pos, duration=1):
        note_from = 128 - note_from
        note_to = 128 - note_to + 1 #1 plus, to fill the end of the note
        
        note_width = CURSOR_WIDTH        
        note_height = CURSOR_HEIGHT
        
        #Horizontal lines
        for i in range (note_from, note_to):
            self.notes_area.window.draw_line(self.gc_grid, 
                    pos * note_width, i * note_height, 
                    pos + duration * note_width, i * note_height)

        #Vertical lines
        for tmp_pos in range(pos, pos+duration+1):

            #Draw hard beat on black
            if tmp_pos % TICKS_PER_BEAT == 0:
                self.notes_area.window.draw_line(self.gc_foreground, 
                        tmp_pos * note_width, note_from * note_height, 
                        tmp_pos * note_width, note_to * note_height)
            elif tmp_pos % self.note_size == 0:
                self.notes_area.window.draw_line(self.gc_grid, 
                        tmp_pos * note_width, note_from * note_height, 
                        tmp_pos * note_width, note_to * note_height)
