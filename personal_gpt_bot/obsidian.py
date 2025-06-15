import os


class Obsidian:

    def __init__(self, vault_path):
        self.vault_path = vault_path

    def get_note_content(self, name):
        if not self.vault_path:
            return ""
        if not os.path.exists(self.vault_path):
            return ""
        if not os.path.isdir(self.vault_path):
            return ""

        name = name + ".md"
        for file in os.listdir(self.vault_path):
            if file == name:
                filefull = os.path.join(self.vault_path, file)
                with open(filefull, "r") as f:
                    data = f.read()
                    return data

        return ""
