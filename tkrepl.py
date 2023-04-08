# importing modules
import tkinter as tk
import sys
import io

class REPL(tk.Frame):
    def __init__(self, master=None):
        # setting up widgets and needed variables
        super().__init__(master)
        self.master = master
        self.master.title("REPL")
        self.pack(fill=tk.BOTH, expand=True)
        self.create_widgets()
        self.history = []
        self.history_index = 0
        # useful for testing things, can be removed
        self.master.wm_attributes("-topmost", True)

    def create_widgets(self):
        # set up the first text widget that will act as a "prompt", similar to python interpreter
        # for both the first and second text widget, we hide the separation between them, mostly for aesthetic
        self.prompt_widget = tk.Text(self, height=20, width=4, borderwidth=0, highlightthickness=0)
        self.prompt_widget.pack(side=tk.LEFT, fill=tk.Y)
        self.prompt_widget.insert(tk.END, ">>> ")

        # set up the second text widget that will act as the input/output for our repl
        self.text_widget = tk.Text(self, height=20, width=76, borderwidth=0, highlightthickness=0)
        self.text_widget.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.text_widget.focus()

        # set up a basic colorscheme, I preferred this one because of eyesight
        self.prompt_widget.configure(bg='black', fg='white')
        self.text_widget.configure(bg='black', fg='white')
        # invert color of blinking cursor to match the background and foreground
        self.text_widget.config(insertbackground="white")

        # adding mousewheel support, so we can scroll on both text widget at the same time, in a synchronous way
        # to match the prompt related to the start of each input in the second widget
        self.text_widget.bind("<MouseWheel>", self.sync_scrolls)
        self.prompt_widget.bind("<MouseWheel>", self.sync_scrolls)

        # Here is the main way to either type a newline, or execute our input
        # Using Shift+Return to execute commands, and Return to just type a normal newline
        self.text_widget.bind("<Shift-Return>", self.execute_command)
        self.text_widget.bind("<Return>", self.newline)

        # goes up and down in history
        self.text_widget.bind('<Up>', self.history_show)
        self.text_widget.bind('<Down>', self.history_show)

        # useful for preventing any "input" if the blinking cursor happen to be on any other places than the latest prompt
        self.text_widget.bind('<Key>', self.is_last_line)

        # prevent clicking on the prompt widget
        self.prompt_widget.bind("<Button-1>", self.do_nothing)

        # copy,paste,cut using Ctrl+c,Ctrl+v,Ctrl+x respectively
        self.text_widget.bind("<Control-c>", self.copy)
        self.text_widget.bind("<Control-v>", self.paste)
        self.text_widget.bind("<Control-x>", self.cut)

    def copy(self, event):
        # copy, which isn't supported by default in this case
        self.text_widget.event_generate("<<Copy>>")
        return "break"

    def paste(self, event):
        # supported by default for some reason, but still set it up anyway
        self.text_widget.event_generate("<<Paste>>")
        return "break"

    def cut(self, event):
        # cut, also already supported by default on Windows 10, but you never know...
        self.text_widget.event_generate("<<Cut>>")
        return "break"

    def sync_scrolls(self, event):
        # sync the two text widget scrolling, doesn't seem to always work
        if event.delta == -120:
            self.prompt_widget.yview_scroll(1, "units")
            self.text_widget.yview_scroll(1, "units")
        elif event.delta == 120:
            self.prompt_widget.yview_scroll(-1, "units")
            self.text_widget.yview_scroll(-1, "units")
        return "break"

    def newline(self, event):
        # make a newline for Return
        self.text_widget.insert(tk.END, "\n")
        return "break"

    def do_nothing(self, event):
        # just useful to make a tkinter component do nothing. Might not always work (eg: for tag related method/function, etc)
        return "break"

    def execute_command(self, event):
        # set up variable for the last line of the prompt widget, last line text/secondary widget, and command
        prompt_last_line = int(self.prompt_widget.index(tk.END).split(".")[0]) - 1
        text_last_line = int(self.text_widget.index(tk.END).split(".")[0]) - 1
        command = self.text_widget.get(f"{prompt_last_line}.0", f"{text_last_line}.end").strip()

        # check if the command variable is empty, which happens if only the Return key or any key mapped to the newline method is used
        if not command:
            self.prompt_widget.insert(tk.END, "\n>>> ")
            self.text_widget.insert(tk.END, "\n")
            return "break"

        # append to history
        self.history.append(command)
        self.history_index = len(self.history)

        # here we execute and show result if there is any
        code = command
        self.text_widget.see(tk.END)
        try:
            # so here we both cache the result of any print() used, and reuse the global namespace and local namespace,
            # so we can execute command "non-continuously", like modern REPL, eg: ipython
            stdout = sys.stdout
            sys.stdout = io.StringIO()
            global_ns = sys.modules['__main__'].__dict__
            local_ns = {}
            exec(code, global_ns, local_ns)
            result = sys.stdout.getvalue()
            sys.stdout = stdout
            global_ns.update(local_ns)
        except Exception as e:
            result = str(e)

        # we insert the result
        self.text_widget.insert(tk.END, f"\n{result}")

        # this part is to "fill" the prompt widget, so we can delimit the starting and end of an input/output on the second widget
        current_line = int(self.text_widget.index(tk.INSERT).split(".")[0])
        prompt_line_index = f"{current_line}.0"
        if current_line > prompt_last_line:
            for i in range(prompt_last_line + 1, current_line + 1):
                self.prompt_widget.insert(f"{i}.0", "\n")
            self.prompt_widget.insert(prompt_line_index, "\n>>> ")

    def is_last_line(self, event):
        # useful method to know if our blinking cursor is currently on current valid latest prompt, which is equal to the latest "\n>>> " in the first widget, and current line in the second widget
        current_line = int(self.text_widget.index(tk.INSERT).split(".")[0])
        prompt_last_line = int(self.prompt_widget.index(tk.END).split(".")[0]) - 1

        # if the blinking cursor is before the latest prompt
        if current_line < prompt_last_line:
            return "break"
        # if blinking cursor is at first line of valid prompt of the second widget/last line of prompt widget, prevent backspace from occuring, since it can circuvent the binding to <Key>
        elif current_line == prompt_last_line and event.keysym == "BackSpace":
            cursor_index = self.text_widget.index(tk.INSERT)
            if cursor_index == f"{current_line}.0":
                return "break"
        # Same as for the backspace. technically this one isn't needed since we allow the cursor to move freely when clicking with the mouse, at least on the second widget
        elif current_line == prompt_last_line and event.keysym == "Left":
            cursor_index = self.text_widget.index(tk.INSERT)
            if cursor_index == f"{current_line}.0":
                return "break"
        else:
            pass

    def history_show(self, event):
        # show history in a very rudimentary way. no deduplication, history replacement on edit, etc.
        prompt_last_line = int(self.prompt_widget.index(tk.END).split(".")[0]) - 1
        current_line = int(self.text_widget.index(tk.INSERT).split(".")[0])
        text_last_line = int(self.text_widget.index(tk.END).split(".")[0]) - 1
        if event.keysym == "Up" and current_line == prompt_last_line:
            if self.history_index > 0:
                self.history_index -= 1
                self.text_widget.delete(f"{prompt_last_line}.0", f"{text_last_line}.end")
                self.text_widget.insert(f"{prompt_last_line}.0", self.history[self.history_index])
            return "break"
        elif event.keysym == "Down" and text_last_line == prompt_last_line:
            if self.history_index < len(self.history) - 1:
                self.history_index += 1
                self.text_widget.delete(f"{prompt_last_line}.0", f"{text_last_line}.end")
                self.text_widget.insert(f"{prompt_last_line}.0", self.history[self.history_index])
            return "break"

root = tk.Tk()
repl = REPL(master=root)
repl.mainloop()
