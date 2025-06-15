import os


class Obsidian:

    def __init__(self, vault_path):
        self.vault_path = vault_path
        self.vault_folder = "anotes"
        self.vault_folder_path = os.path.join(self.vault_path, self.vault_folder)

    def get_note_content(self, name):
        if not self.vault_path:
            return ""
        if not os.path.exists(self.vault_folder_path):
            return ""
        if not os.path.isdir(self.vault_folder_path):
            return ""

        name = name + ".md"
        for file in os.listdir(self.vault_folder_path):
            if file == name:
                filefull = os.path.join(self.vault_folder_path, file)
                with open(filefull, "r") as f:
                    data = f.read()
                    return data

        return ""
