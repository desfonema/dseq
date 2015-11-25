import threading
import time
import Queue

from util import nanosleep
from  models import Sequence

time.sleep = nanosleep.nanosleep
TICKS_PER_BEAT = 24

class PlayerThread(threading.Thread):
    def __init__(self, conn):  
        threading.Thread.__init__(self)
        #Position means pattern if playing a channel, or cursor pos if playing pattern 
        self.__pos = 0
        self.__conn = conn
        self.__play_queue = Queue.Queue()
        self.__playing = False
        self.__repeat = False
        
    def play(self, data, bpm, repeat = False):
        if self.playing():
            self.stop()
            
        self.__conn.refresh_connections()
        self.__playing = True
        self.__data = data
        self.time_tick = (1./TICKS_PER_BEAT)/(bpm/60.0)
        self.__repeat = repeat
        self.__play_queue.put('play')

    def playing(self):
        return self.__playing
        
    def stop(self):
        self.__playing = False

    def quit(self):
        self.stop()
        self.__play_queue.put('quit')
        
    def get_pos(self):
        return self.__pos

    def set_pos(self, pos):
        self.__pos = pos

    def run(self):
        data = self.__play_queue.get()
        while data != 'quit':
            #Are we playing a channel or a single module?
            playing_channel = (self.__data.__module__ == 'Channel')
            
            if playing_channel:
                patterns = self.__data.get_patterns()
                
                pos_max = len(patterns)
                if self.__pos >= pos_max:
                    self.__pos = 0
                    
                if pos_max:
                    pat = patterns[self.__pos]
                    pos = 0
            else:
                patterns = [self.__data]
                pos_max = self.__data.get_len()*TICKS_PER_BEAT
                pat = self.__data
                pos = self.__pos
                
            if self.__pos >= pos_max:
                self.__pos = 0

            time_tick = self.time_tick
            while self.__playing and (self.__pos < pos_max):
                for track in pat.get_tracks():
                    #If playing channel we don't honor track mute. 
                    if playing_channel or track.enabled:
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
                time.sleep(time_tick)
                pos = pos + 1
                if playing_channel:
                    if pos == pat.get_len()*TICKS_PER_BEAT:
                        pos = 0
                        self.__pos = self.__pos + 1
                        pos_max = len(patterns)
                        if self.__pos < pos_max:
                            pat = patterns[self.__pos]
                else:
                    pos_max = pat.get_len()*TICKS_PER_BEAT
                    if (pos == pos_max) and self.__repeat:
                        pos = 0
                    self.__pos = pos
            #Stop all sound
            for pat in patterns:
                for track in pat.get_tracks():
                    synth_conn = self.__conn.get_port(track.get_synth())
                    port = track.get_port()
                    for seq_pos in track.get_sequence():
                        for (event, note, volume) in seq_pos:
                            if synth_conn != None: synth_conn.note_off(note, port)

            if self.__pos >= pos_max:
                self.__pos = 0

            self.__playing = False
                
            data = self.__play_queue.get()

    
    def stop_sounds(self):
        pass
