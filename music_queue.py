import os

class queue:
    def __init__(self, file_array, loop_when_done_playing):
        self.full_file_array = file_array
        self.file_array = self.full_file_array
        self.loop_when_done_playing = loop_when_done_playing
    
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

    def name_to_path(self, name):
        return rf"C:\Users\{os.getlogin()}\Music\Discord\{name}"
    
    def add_to_queue(self, filenname):
        
        if not os.path.exists(self.name_to_path(filenname)):
            return f"{filenname} doesn't exist."

        self.file_array.insert(len(self.file_array), filenname)

        return f"Successfully added {filenname} to the queue."

    def list_queue(self):
        liststr = "Queue:\n"
        for index, item in enumerate(self.file_array):
            liststr = liststr + f"{str(index)}. {item},\n"
        return liststr