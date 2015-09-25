#This is the Controller Editor Widget

import pygtk
import gtk

KEY_SPACE = 1
BEAT_WIDTH = 24
TICKS_PER_BEAT = 24
CONTROLLER_RESOLUTION = 8

CONTROLLERS = [
    ('Volume', 7),
    ('Modulation', 1),
    ('Pan', 10),
    ('Expression', 11),
    ('Sustain', 64),
    ('Portamento', 65),
    ('Filter Q', 71),
    ('Filter cutoff', 74)
    ]

class ControllerEditorWidget(gtk.Expander):
    def __init__(self, container, label="Controller Editor"):

        gtk.Expander.__init__(self, label)
    
        #Selected Controler
        self.controller = CONTROLLERS[0][1]
        
        #Make sure we got the right track
        self.track = container.tw.track
        
        #Controller Mapping
        self.controllers_mapping = [(0,0),(0,0)]
        #container object
        self.container = container

        #Space from left
        alloc = self.container.tw.area_piano_sw.get_allocation()
        self.space = alloc.width

        #Main Vertical Box where we put our controls
        vbox = gtk.VBox(False,0)

        #Horizontal Box for Controller Selection 
        hbox = gtk.HBox(False,0)

        #Controller Selector
        lbl_controller = gtk.Label("Controller View:")
        lbl_controller.show()
        hbox.pack_start(lbl_controller, False, False, 0)
        self.cbo_controller = gtk.combo_box_new_text()
        for c in CONTROLLERS:
            self.cbo_controller.append_text(c[0])
        self.cbo_controller.connect('changed', self.cbo_controller_changed)
        self.cbo_controller.set_active(0)
        self.cbo_controller.show()
        hbox.pack_start(self.cbo_controller, False, False, 4)
        
        #Clear controller
        btn_clear = gtk.Button("Clear")
        btn_clear.connect("clicked", self.btn_clear_clicked, None)
        btn_clear.show()
        hbox.pack_start(btn_clear, True, True, 4)
        
        #Input Controller 1
        lbl_controller_input_1 = gtk.Label("Use Input")
        lbl_controller_input_1.show()
        hbox.pack_start(lbl_controller_input_1, False, False, 0)
        self.cbo_controller_input_1 = gtk.combo_box_new_text()
        for c in CONTROLLERS:
            self.cbo_controller_input_1.append_text(c[0])
        self.cbo_controller_input_1.connect('changed', self.cbo_controller_input_1_changed)
        self.cbo_controller_input_1.show()
        hbox.pack_start(self.cbo_controller_input_1, False, False, 4)

        #As...
        lbl_controller_output_1 = gtk.Label("as")
        lbl_controller_output_1.show()
        hbox.pack_start(lbl_controller_output_1, False, False, 0)
        self.cbo_controller_output_1 = gtk.combo_box_new_text()
        for c in CONTROLLERS:
            self.cbo_controller_output_1.append_text(c[0])
        self.cbo_controller_output_1.connect('changed', self.cbo_controller_input_1_changed)
        self.cbo_controller_output_1.show()
        hbox.pack_start(self.cbo_controller_output_1, False, False, 4)

        self.cbo_controller_input_1.set_active(0)
        self.cbo_controller_output_1.set_active(0)

        #Input Controller 2
        lbl_controller_input_2 = gtk.Label("and")
        lbl_controller_input_2.show()
        hbox.pack_start(lbl_controller_input_2, False, False, 0)
        self.cbo_controller_input_2 = gtk.combo_box_new_text()
        for c in CONTROLLERS:
            self.cbo_controller_input_2.append_text(c[0])
        self.cbo_controller_input_2.connect('changed', self.cbo_controller_input_2_changed)
        self.cbo_controller_input_2.show()
        hbox.pack_start(self.cbo_controller_input_2, False, False, 4)

        #As...
        lbl_controller_output_2 = gtk.Label("as")
        lbl_controller_output_2.show()
        hbox.pack_start(lbl_controller_output_2, False, False, 0)
        self.cbo_controller_output_2 = gtk.combo_box_new_text()
        for c in CONTROLLERS:
            self.cbo_controller_output_2.append_text(c[0])
        self.cbo_controller_output_2.connect('changed', self.cbo_controller_input_2_changed)
        self.cbo_controller_output_2.show()
        hbox.pack_start(self.cbo_controller_output_2, False, False, 4)
        
        self.cbo_controller_input_2.set_active(1)
        self.cbo_controller_output_2.set_active(1)

        hbox.show()
        vbox.pack_start(hbox, False, False, 0)
        
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
        
        for (pos, param, value) in self.track.get_controllers():
            if param == self.controller:
                self.paint_control_value(pos * CONTROLLER_RESOLUTION / TICKS_PER_BEAT, value)
        
    #Handles mouse movement
    def area_motion_notify(self, widget, event):

        if event.state & gtk.gdk.BUTTON1_MASK:
            tick = (BEAT_WIDTH + KEY_SPACE * TICKS_PER_BEAT) / CONTROLLER_RESOLUTION
            
            value = 127-int(event.y)
            if value < 0: value = 0 
            if value > 127: value = 127 
            pos = (int(event.x) - self.space) / tick

            if (pos >= 0) and (pos < self.track.get_len()*CONTROLLER_RESOLUTION): 
                self.track.set_control(pos * TICKS_PER_BEAT / CONTROLLER_RESOLUTION, self.controller, value)
                self.paint_control_value(pos, value)
        elif event.state & gtk.gdk.BUTTON3_MASK:
            tick = (BEAT_WIDTH + KEY_SPACE * TICKS_PER_BEAT) / CONTROLLER_RESOLUTION
            
            pos = (int(event.x) - self.space) / tick

            if (pos >= 0) and (pos < self.track.get_len()*CONTROLLER_RESOLUTION): 
                delete = []
                for (opos, oparam, ovalue) in self.track.get_controllers():
                    if oparam == self.controller and opos == pos * TICKS_PER_BEAT / CONTROLLER_RESOLUTION:
                        delete.append((opos, oparam, ovalue))
                for (opos, oparam, ovalue) in delete:
                    self.track.del_control(opos, oparam, ovalue)
                self.paint_control_value(pos, 0)
            
    #Handles mouse buttons
    def area_button_press(self, widget, event):
        if event.state & gtk.gdk.BUTTON1_MASK:
            tick = (BEAT_WIDTH + KEY_SPACE * TICKS_PER_BEAT) / CONTROLLER_RESOLUTION
            
            value = 127-int(event.y)
            if value < 0: value = 0 
            if value > 127: value = 127 
            pos = (int(event.x) - self.space) / tick

            if (pos >= 0) and (pos < self.track.get_len()*CONTROLLER_RESOLUTION): 
                self.track.set_control(pos * TICKS_PER_BEAT / CONTROLLER_RESOLUTION, self.controller, value)
                self.paint_control_value(pos, value)

        elif event.state & gtk.gdk.BUTTON3_MASK:
            tick = (BEAT_WIDTH + KEY_SPACE * TICKS_PER_BEAT) / CONTROLLER_RESOLUTION
            
            pos = (int(event.x) - self.space) / tick

            if (pos >= 0) and (pos < self.track.get_len()*CONTROLLER_RESOLUTION): 
                delete = []
                for (opos, oparam, ovalue) in self.track.get_controllers():
                    if oparam == self.controller and opos == pos * TICKS_PER_BEAT / CONTROLLER_RESOLUTION:
                        delete.append((opos, oparam, ovalue))
                for (opos, oparam, ovalue) in delete:
                    self.track.del_control(opos, oparam, ovalue)
                self.paint_control_value(pos, 0)
            
    def paint_control_value(self, pos, value):
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
        tick = beat_size / CONTROLLER_RESOLUTION
        
        self.area.window.draw_rectangle(gc_background, True, self.space + pos*tick , 0, tick, 127-value)
        self.area.window.draw_rectangle(gc_foreground, True, self.space + pos*tick , 127-value, tick, 127)
        if pos % CONTROLLER_RESOLUTION == 0:
            self.area.window.draw_line(gc_foreground, pos * tick + self.space, 0, pos * tick + self.space, 128)

    def cbo_controller_changed(self, widget, data= None):
        self.controller = CONTROLLERS[widget.get_active()][1]
        self.redraw()
                
    def cbo_controller_input_1_changed(self, widget, data= None):
        self.controllers_mapping[0] = (
            CONTROLLERS[self.cbo_controller_input_1.get_active()][1], 
            CONTROLLERS[self.cbo_controller_output_1.get_active()][1]
            )
                
    def cbo_controller_input_2_changed(self, widget, data= None):
        self.controllers_mapping[1] = (
            CONTROLLERS[self.cbo_controller_input_2.get_active()][1], 
            CONTROLLERS[self.cbo_controller_output_2.get_active()][1]
            )
                
    def set_scroll_pos(self, pos):
        self.sw_hadj.set_value(pos)

    def sw_hadj_value_changed(self, adj):
        pass

    def btn_clear_clicked(self, widget, data=None):
        delete = []
        for (pos, param, value) in self.track.get_controllers():
            if param == self.controller:
                delete.append((pos, param, value))
        for (pos, param, value) in delete:
            self.track.del_control(pos, param, value)
            
        self.redraw()

    def handle_midi_input(self, pos, param, value):
        translated_controller = param
        for mapped_controller in self.controllers_mapping:
            if mapped_controller[0] == param:
                translated_controller = mapped_controller[1]
                break
                
        pos = pos * CONTROLLER_RESOLUTION / TICKS_PER_BEAT
        if (pos >= 0) and (pos < self.track.get_len()*CONTROLLER_RESOLUTION):
            self.track.set_control(pos * TICKS_PER_BEAT / CONTROLLER_RESOLUTION, translated_controller, value)
            if translated_controller == self.controller:
                self.paint_control_value(pos, value)
                
        synth_conn = self.container.container.conn.get_port(self.track.get_synth())
        if synth_conn != None: synth_conn.set_control(value, translated_controller, self.track.get_port())

        
