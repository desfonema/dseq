#This is the Controller Editor Widget

import pygtk
import gtk

KEY_SPACE = 1
BEAT_WIDTH = 24
TICKS_PER_BEAT = 24
PITCHBEND_RESOLUTION = 24

class PitchbendEditorWidget(gtk.Expander):
    def __init__(self, container, label="Pitchbend Editor"):

        gtk.Expander.__init__(self, label)
    
        #container object
        self.container = container
        
        #Make sure we got the right track
        self.track = container.tw.track

        #Space from left
        alloc = self.container.tw.area_piano_sw.get_allocation()
        self.space = alloc.width

        #Main Vertical Box where we put our controls
        vbox = gtk.VBox(False,0)

        #Scroll widget to contain painting area
        self.sw = gtk.ScrolledWindow()
        self.sw.set_policy(gtk.POLICY_ALWAYS, gtk.POLICY_NEVER)
        
        #Note zone
        self.area = gtk.DrawingArea()
        
        self.area.set_events(
            gtk.gdk.BUTTON_PRESS_MASK | 
            gtk.gdk.BUTTON_RELEASE_MASK |
            gtk.gdk.POINTER_MOTION_MASK )
        
        self.area.connect("expose-event", self.area_expose)
        self.area.connect("motion_notify_event", self.area_motion_notify)
        self.area.connect("button_press_event", self.area_button_press)

        self.area_resize()
        self.area.show()
        self.pangolayout = self.area.create_pango_layout("")

        self.sw.add_with_viewport(self.area)
        self.sw_hadj = self.sw.get_hadjustment()        
        self.sw_hadj.connect('value_changed', self.sw_hadj_value_changed)
        self.sw.show()
        
        vbox.pack_start(self.sw, True, True, 0)        
        vbox.show()
        self.add(vbox)

    #Set graphic area size to the pattern notes
    def area_resize(self):
        self.area.set_size_request(self.container.pat.get_len() * (BEAT_WIDTH + KEY_SPACE * TICKS_PER_BEAT) + 32 + self.space, 128)
        
    #Handles Expose event on controller roll
    def area_expose(self, area, event):
        self.redraw()
        
    def redraw(self):
        #Make sure we got the right track
        self.track = self.container.tw.track

        #Space from left
        alloc = self.container.tw.area_piano_sw.get_allocation()
        self.space = alloc.width

        self.gc = self.style.fg_gc[gtk.STATE_NORMAL]
        try:
            colormap = self.area.get_colormap()
        except:
            return
            
        color_background = colormap.alloc_color('#FFFFFF', True, True)
        gc_background = self.area.window.new_gc()
        gc_background.set_foreground(color_background)

        color_foreground = colormap.alloc_color('#C0C0C0', True, True)
        gc_foreground = self.area.window.new_gc()
        gc_foreground.set_foreground(color_foreground)

        pat_len = self.container.pat.get_len()
        beat_size = (BEAT_WIDTH + KEY_SPACE * TICKS_PER_BEAT)
        
        self.area.window.draw_rectangle(gc_background, True, self.space , 0, pat_len * beat_size + 32 + self.space, 128)
        
        for i in range(pat_len):
            self.area.window.draw_line(gc_foreground, (i+1) * beat_size + self.space, 0, (i+1) * beat_size + self.space, 128)
        
        for (pos, value) in self.track.get_pitchbends():
            self.paint_pitchbend_value(pos * PITCHBEND_RESOLUTION / TICKS_PER_BEAT, value)
        
    #Handles mouse movement
    def area_motion_notify(self, widget, event):

        if event.state & gtk.gdk.BUTTON1_MASK:
            tick = (BEAT_WIDTH + KEY_SPACE * TICKS_PER_BEAT) / PITCHBEND_RESOLUTION
            
            value = 8191-int(event.y)*128
            if value < -8192: value = -8192 
            if value > 8191: value = 8191 
            pos = (int(event.x) - self.space) / tick

            if (pos >= 0) and (pos < self.track.get_len()*PITCHBEND_RESOLUTION): 
                self.track.set_pitchbend(pos * TICKS_PER_BEAT / PITCHBEND_RESOLUTION, value)
                self.paint_pitchbend_value(pos, value)

        elif event.state & gtk.gdk.BUTTON2_MASK:
            tick = (BEAT_WIDTH + KEY_SPACE * TICKS_PER_BEAT) / PITCHBEND_RESOLUTION
            
            pos = (int(event.x) - self.space) / tick

            if (pos >= 0) and (pos < self.track.get_len()*PITCHBEND_RESOLUTION): 
                delete = []
                for (opos, ovalue) in self.track.get_pitchbends():
                    if opos == pos * TICKS_PER_BEAT / PITCHBEND_RESOLUTION:
                        delete.append((opos, ovalue))
                for (opos,  ovalue) in delete:
                    self.track.del_pitchbend(opos, ovalue)
                self.paint_pitchbend_value(pos, -8192)

        elif event.state & gtk.gdk.BUTTON3_MASK:
            tick = (BEAT_WIDTH + KEY_SPACE * TICKS_PER_BEAT) / PITCHBEND_RESOLUTION
            
            pos = (int(event.x) - self.space) / tick

            if (pos >= 0) and (pos < self.track.get_len()*PITCHBEND_RESOLUTION): 
                delete = []
                for (opos, ovalue) in self.track.get_pitchbends():
                    if opos == pos * TICKS_PER_BEAT / PITCHBEND_RESOLUTION:
                        delete.append((opos, ovalue))
                for (opos,  ovalue) in delete:
                    self.track.del_pitchbend(opos, ovalue)

                self.track.set_pitchbend(pos * TICKS_PER_BEAT / PITCHBEND_RESOLUTION, 0)
                self.paint_pitchbend_value(pos, 0)
            
    #Handles mouse buttons
    def area_button_press(self, widget, event):
        if event.state & gtk.gdk.BUTTON1_MASK:
            tick = (BEAT_WIDTH + KEY_SPACE * TICKS_PER_BEAT) / PITCHBEND_RESOLUTION
            
            value = 8191-int(event.y)*128
            if value < -8192: value = -8192 
            if value > 8191: value = 8191 
            pos = (int(event.x) - self.space) / tick

            if (pos >= 0) and (pos < self.track.get_len()*PITCHBEND_RESOLUTION): 
                self.track.set_pitchbend(pos * TICKS_PER_BEAT / PITCHBEND_RESOLUTION, value)
                self.paint_pitchbend_value(pos, value)

        elif event.state & gtk.gdk.BUTTON2_MASK:
            tick = (BEAT_WIDTH + KEY_SPACE * TICKS_PER_BEAT) / PITCHBEND_RESOLUTION
            
            pos = (int(event.x) - self.space) / tick

            if (pos >= 0) and (pos < self.track.get_len()*PITCHBEND_RESOLUTION): 
                delete = []
                for (opos, ovalue) in self.track.get_pitchbends():
                    if opos == pos * TICKS_PER_BEAT / PITCHBEND_RESOLUTION:
                        delete.append((opos, ovalue))
                for (opos,  ovalue) in delete:
                    self.track.del_pitchbend(opos, ovalue)
                self.paint_pitchbend_value(pos, -8192)

        elif event.state & gtk.gdk.BUTTON3_MASK:
            tick = (BEAT_WIDTH + KEY_SPACE * TICKS_PER_BEAT) / PITCHBEND_RESOLUTION
            
            pos = (int(event.x) - self.space) / tick

            if (pos >= 0) and (pos < self.track.get_len()*PITCHBEND_RESOLUTION): 
                delete = []
                for (opos, ovalue) in self.track.get_pitchbends():
                    if opos == pos * TICKS_PER_BEAT / PITCHBEND_RESOLUTION:
                        delete.append((opos, ovalue))
                for (opos,  ovalue) in delete:
                    self.track.del_pitchbend(opos, ovalue)

                self.track.set_pitchbend(pos * TICKS_PER_BEAT / PITCHBEND_RESOLUTION, 0)
                self.paint_pitchbend_value(pos, 0)
            
    def paint_pitchbend_value(self, pos, value):
        colormap = self.area.get_colormap()
        
        color_background = colormap.alloc_color('#FFFFFF', True, True)
        try:
            gc_background = self.area.window.new_gc()
        except:
            return
            
        gc_background.set_foreground(color_background)

        color_foreground = colormap.alloc_color('#C0C0C0', True, True)
        gc_foreground = self.area.window.new_gc()
        gc_foreground.set_foreground(color_foreground)
        
        beat_size = (BEAT_WIDTH + KEY_SPACE * TICKS_PER_BEAT)
        tick = beat_size / PITCHBEND_RESOLUTION
        value = 64 -(value / 128)
        self.area.window.draw_rectangle(gc_background, True, self.space + pos*tick , 0, tick, value)
        self.area.window.draw_rectangle(gc_foreground, True, self.space + pos*tick , value, tick, 128)
        if pos % PITCHBEND_RESOLUTION == 0:
            self.area.window.draw_line(gc_foreground, pos * tick + self.space, 0, pos * tick + self.space, 128)

    def set_scroll_pos(self, pos):
        self.sw_hadj.set_value(pos)

    def sw_hadj_value_changed(self, adj):
        pass

    def handle_midi_input(self, pos, value):
        pos = pos * PITCHBEND_RESOLUTION / TICKS_PER_BEAT
        if (pos >= 0) and (pos < self.track.get_len()*PITCHBEND_RESOLUTION):
            self.track.set_pitchbend(pos * TICKS_PER_BEAT / PITCHBEND_RESOLUTION, value)
            self.paint_pitchbend_value(pos, value)
        synth_conn = self.container.container.conn.get_port(self.track.get_synth())
        if synth_conn != None: synth_conn.set_pitchbend(value, self.track.get_port())

        
