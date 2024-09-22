import os

class queue:
    # TODO: implement url_array instead of file_array
    def __init__(self, file_array, loop_when_done_playing):
        self.full_file_array = file_array
        self.file_array = self.full_file_array
        self.loop_when_done_playing = loop_when_done_playing
    
    def get_current_song(self) -> str:
        """Returns the current song in the queue."""
        return self.file_array[0]
    
    def loop(self) -> None:
        """Resets the queue."""
        self.file_array = self.full_file_array
    
    def clear(self) -> None:
        """Clears the queue and the queue base."""
        self.file_array = []
        self.full_file_array = []

    def goto_next_song(self) -> None:
        """Skips the current song and goes to the next song or
        loops the queue if looping is enabled."""
        del self.file_array[0]

        if len(self.file_array) <= 0 and self.loop_when_done_playing:
            self.loop()

    # legacy function TODO: remove or return correct path to the download dir.
    def name_to_path(self, name) -> str:
        return rf"C:\Users\{os.getlogin()}\Music\Discord\{name}"
    
    def add_to_queue(self, filenname) -> str:
        """Adds a url to the queue and returns a simple log message"""

        if not os.path.exists(self.name_to_path(filenname)):
            return f"{filenname} doesn't exist."

        self.file_array.insert(len(self.file_array), filenname)

        return f"Successfully added {filenname} to the queue."

    def list_queue(self) -> str:
        """Returns a list of items in the queue."""
        liststr = "Queue:\n"
        for index, item in enumerate(self.file_array):
            liststr = liststr + f"{str(index)}. {item},\n"
        return liststr