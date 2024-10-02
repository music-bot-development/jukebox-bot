import os

class queue:
    def __init__(self, url_array, loop_when_done_playing):
        self.full_url_array = url_array
        self.url_array = self.full_url_array
        self.loop_when_done_playing = loop_when_done_playing
    
    def get_current_song(self) -> str:
        """Returns the current song in the queue."""
        return self.url_array[0]
    
    def loop(self) -> None:
        """Resets the queue."""
        self.url_array = self.full_url_array
    
    def clear(self) -> None:
        """Clears the queue and the queue base."""
        self.url_array = []
        self.full_url_array = []

    def goto_next_song(self) -> None:
        """Skips the current song and goes to the next song or
        loops the queue if looping is enabled."""
        del self.url_array[0]

        if len(self.url_array) <= 0 and self.loop_when_done_playing:
            self.loop()
    
    def add_to_queue(self, url) -> str:
        """Adds a url to the queue and returns a simple log message"""

        self.url_array.insert(len(self.url_array), url)

        return f"Successfully added {url} to the queue."

    def list_queue(self) -> str:
        """Returns a list of items in the queue."""
        liststr = "Queue:\n"
        for index, item in enumerate(self.url_array):
            liststr = liststr + f"{str(index)}. {item},\n"
        return liststr