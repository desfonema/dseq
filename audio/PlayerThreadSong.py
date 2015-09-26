import threading
import time
import Queue
import jack
from util import nanosleep
import models.Sequence

jack.attach("dseq")

def get_time():
    return float(jack.get_current_transport_frame()) / jack.get_sample_rate()

#testing state set/get
def get_state():
    return jack.get_transport_state()

time.sleep = nanosleep.nanosleep
TICKS_PER_BEAT = 24

class PlayerThreadSong(threading.Thread):
    def __init__(self, conn):  
        threading.Thread.__init__(self)
        #Position means pattern if playing a channel, or cursor pos if playing pattern 
        self.__pos = 0
        self.__conn = conn
        self.__quit = True
        self.__playing = False
        self.__repeat = False
        
    def play(self, data, bpm, repeat = False):
            
        self.__conn.refresh_connections()

    def set_data(self, data):
        self.__data = data

    def set_bpm(self, bpm):
        self.time_tick = (1./TICKS_PER_BEAT)/(bpm/60.0)

    def set_repeat(self, repeat):
        self.__repeat = repeat
        
    def playing(self):
        return self.__playing
        
    def stop(self):
        self.__playing = False

    def quit(self):
        self.stop()
        self.__quit = True
        
    def get_pos(self):
        return self.__pos

    def set_pos(self, pos):
        self.__pos = pos

    def run(self):
        while True:
            self.__playing = False            
            while get_state() == 0:
                time.sleep(0.05)
                if self.__quit:
                    return

            patterns = self.__data.get_patterns()

            time_tick = self.time_tick
            
            self.__playing = True
            self.__pos = -1

            while get_state() == 1:
                #Check current position
                jack_pos = int(get_time()/time_tick)
                if self.__pos == jack_pos:
                    time.sleep(0.001)
                    continue
                
                self.__pos = jack_pos
                #Get current pattern and calculate maximum position
                pos = 0
                current_pattern = None
                for pat in patterns:
                    plen = pat.len * TICKS_PER_BEAT
                    if self.__pos >= pos and self.__pos < pos + plen:
                        current_pattern = pat
                        break
                    pos += plen

                pos = self.__pos - pos
                
                #Play current position of current pattern
                if current_pattern:
                    for track in current_pattern.get_tracks():
                        synth_conn = self.__conn.get_port(track.get_synth())
                        port = track.get_port()
                        for (event, note, volume) in track.get_sequence()[pos]:
                            if synth_conn != None: 
                                if event == Sequence.NOTE_ON:
                                    synth_conn.note_on(note, port, volume)
                                elif event == Sequence.NOTE_OFF:
                                    synth_conn.note_off(note, port)
                                elif event == Sequence.CONTROL:
                                    synth_conn.set_control(volume, note, port)
                                elif event == Sequence.PITCHBEND:
                                    synth_conn.set_pitchbend(note, port)
                
            #Stop all sound
            for pat in patterns:
                for track in pat.get_tracks():
                    synth_conn = self.__conn.get_port(track.get_synth())
                    port = track.get_port()
                    for seq_pos in track.get_sequence():
                        for (event, note, volume) in seq_pos:
                            if synth_conn != None: synth_conn.note_off(note, port)
    
    def stop_sounds(self):
        pass
