class queue:
    def __init__(self, file_array, loop_when_done_playing):
        self.full_file_array = file_array
        self.file_array = self.full_file_array
        self.loop_when_done_playing = loop_when_done_playing
    
    def add_to_queue(self, filenname):
        self.file_array.push(filenname)
    
    def get_current_song(self):
        return self.file_array[0]
    
    def loop(self):
        self.file_array = self.full_file_array
    
    def clear(self):
        self.file_array = []
        self.full_file_array = []

    def goto_next_song(self):
        del self.file_array[0]

        if len(self.file_array) <= 0 and self.loop_when_done_playing:
            self.loop()