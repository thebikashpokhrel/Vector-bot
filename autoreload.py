import time
import subprocess
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler


class ReloadHandler(FileSystemEventHandler):
    def __init__(self, script_path):
        self.script_path = script_path
        self.process = self.start_process()

    def start_process(self):
        """Start the bot process."""
        return subprocess.Popen(
            ["D:/vector-bot/botenv/Scripts/python.exe", self.script_path]
        )

    def on_modified(self, event):
        """Handle file modification events."""
        if event.is_directory:  # Ignore directory changes
            return

        # Check if the modified file is a Python file
        if event.src_path.endswith(".py"):
            print(f"File changed: {event.src_path}. Reloading...")
            self.process.terminate()  # Stop the current process
            self.process = self.start_process()  # Restart the process


if __name__ == "__main__":
    script_to_watch = "main.py"
    event_handler = ReloadHandler(script_to_watch)
    observer = Observer()

    # Watch the current directory and all subdirectories
    observer.schedule(event_handler, path=".", recursive=True)
    observer.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()
