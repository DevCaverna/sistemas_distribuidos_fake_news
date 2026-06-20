import sys


class RedirectorConsole:
    def __init__(self, textbox, app):
        self.textbox = textbox
        self.app = app
        self.original_stdout = sys.stdout

    def write(self, texto):
        self.original_stdout.write(texto)
        self.app.after(0, self._escrever_na_gui, texto)

    def _escrever_na_gui(self, texto):
        self.textbox.configure(state="normal")
        self.textbox.insert("end", texto)
        self.textbox.see("end")
        self.textbox.configure(state="disabled")

    def flush(self):
        self.original_stdout.flush()
