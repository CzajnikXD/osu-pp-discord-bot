import os
import json

# The BeatmapManager class is responsible for managing beatmap files within a specified directory.
# It provides methods to add, use, and delete beatmap files, as well as to save and load the manager's state.
class BeatmapManager:
    def __init__(self, base_directory: str, max_directory_size: int = None):
        self.base_directory = base_directory
        self.beatmap_ids = []
        self.max_directory_size = max_directory_size

    def get_file_path(self, beatmapset_id: int) -> str:
        """
        Returns the file path for a given beatmapset ID.
        """
        return os.path.join(self.base_directory, f'{beatmapset_id}.zip')

    def add_beatmap(self, beatmapset_id: int):
        """
        Adds a beatmapset ID to the manager and checks if the directory size exceeds the maximum limit.
        """
        if beatmapset_id not in self.beatmap_ids:
            self.beatmap_ids.append(beatmapset_id)

        if self.max_directory_size and self.get_directory_size() > self.max_directory_size:
            self.delete_least_used_file()

    def use_beatmap(self, beatmapset_id: int):
        """
        Moves the specified beatmapset ID to the first position in the list.
        """
        if beatmapset_id not in self.beatmap_ids:
            print(f"Beatmapset {beatmapset_id} not found!")
            return

        self.beatmap_ids.remove(beatmapset_id)
        self.beatmap_ids.insert(0, beatmapset_id)

    def get_sorted_paths(self):
        """
        Returns a list of file paths for the beatmapset IDs, sorted by usage.
        """
        return [self.get_file_path(beatmapset_id) for beatmapset_id in self.beatmap_ids]

    def delete_least_used_file(self):
        """
        Deletes the least used beatmap file from the directory.
        """
        if not self.beatmap_ids:
            print("No beatmap files to delete.")
            return

        least_used_id = self.beatmap_ids.pop()
        file_path = self.get_file_path(least_used_id)

        print(f"Deleting least used beatmap file: {file_path}")

        if os.path.exists(file_path):
            os.remove(file_path)
            print(f"File {file_path} successfully deleted.")
        else:
            print(f"File {file_path} not found.")

    def get_directory_size(self) -> int:
        """
        Returns the total size of the base directory in bytes.
        """
        total_size = 0
        for dirpath, dirnames, filenames in os.walk(self.base_directory):
            for filename in filenames:
                file_path = os.path.join(dirpath, filename)
                total_size += os.path.getsize(file_path)
        return total_size

    def save_state(self, file_path="beatmap_data.json"):
        """
        Saves the current state of the beatmap manager to a JSON file.
        """
        data = {"beatmap_ids": self.beatmap_ids, "base_directory": self.base_directory}
        with open(file_path, "w") as file:
            json.dump(data, file)

    @staticmethod
    def load_state(file_path="beatmap_data.json"):
        """
        Loads the beatmap manager state from a JSON file.
        """
        if not os.path.exists(file_path):
            print("No saved state, starting fresh.")
            return BeatmapManager("mapfolder")
        with open(file_path, "r") as f:
            data = json.load(f)
        manager = BeatmapManager(data["base_directory"])
        manager.beatmap_ids = data["beatmap_ids"]
        return manager
