# importing modules
import tkinter as tk
import sys
import io
import ast
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
        self.current_prompt = 1
        self.scrolling = False

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
        # self.text_widget.bind("<MouseWheel>", self.sync_scrolls)
        # self.prompt_widget.bind("<MouseWheel>", self.sync_scrolls)
        self.text_widget.config(yscrollcommand=self.sync_yview)
        self.prompt_widget.config(yscrollcommand=self.sync_yview)
        # either using self.sync_view or self.sync_scrolls show different way the syncing break.

        # Here is the main way to either type a newline, or execute our input
        # Using Shift+Return to execute commands, and Return to just type a normal newline

        self.text_widget.bind('<Return>', self.add_line2)
        self.text_widget.bind('<Shift-Return>', self.execute_command)

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
        

    def sync_yview(self, *args):
        if not self.scrolling:  # Check if no scroll operation is currently underway
            self.scrolling = True  # Indicate that a scroll operation is now underway
            first, last = args
            self.text_widget.yview_moveto(first)
            self.prompt_widget.yview_moveto(first)
            self.scrolling = False  # Indicate that the scroll operation is complete

        # Optionally, log information for debugging
        total_lines1 = int(self.prompt_widget.index('end').split('.')[0])
        total_lines2 = int(self.text_widget.index('end').split('.')[0])

        first_frac1, last_frac1 = self.prompt_widget.yview()
        first_line1 = int(first_frac1 * total_lines1) + 1
        last_line1 = int(last_frac1 * total_lines1)

        first_frac2, last_frac2 = self.text_widget.yview()
        first_line2 = int(first_frac2 * total_lines2) + 1
        last_line2 = int(last_frac2 * total_lines2)
        print(f"Synced Text Widgets - Lines: {total_lines1}, {total_lines2}", self.current_prompt, first_line1, first_line2, last_line1, last_line2)


    def add_line2(self, event=None):
        self.prompt_widget.insert('end', '\n')
        self.prompt_widget.see('end')

    def copy(self, event):
        # copy, which isn't supported by default in this case
        self.text_widget.event_generate("<<Copy>>")
        return "break"

    def paste(self, event):
        self.text_widget.event_generate("<<Paste>>")
        meow = int(self.prompt_widget.index(tk.END).split(".")[0])
        meow2 = int(self.text_widget.index(tk.END).split(".")[0])
        if meow2 > meow:
            for i in range(meow, meow2):
                self.prompt_widget.insert(f"{i}.0", "\n")
        elif meow2 < meow:
            for i in range(meow2, meow):
                self.prompt_widget.delete(f"{i}.0")
        prompt_frac1, prompt_frac2 = self.text_widget.yview()
        self.text_widget.yview_moveto(prompt_frac2) # tried to make this work, but to no avail
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

        prompt_frac1, prompt_frac2 = self.prompt_widget.yview()
        self.text_widget.yview_moveto(prompt_frac1)

        total_lines1 = int(self.prompt_widget.index('end').split('.')[0])
        total_lines2 = int(self.text_widget.index('end').split('.')[0])

        first_frac1, last_frac1 = self.prompt_widget.yview()
        first_line1 = int(first_frac1 * total_lines1) + 1
        last_line1 = int(last_frac1 * total_lines1)

        first_frac2, last_frac2 = self.text_widget.yview()
        first_line2 = int(first_frac2 * total_lines2) + 1
        last_line2 = int(last_frac2 * total_lines2)
        print(f"Split Text Widgets - Lines: {total_lines1}, {total_lines2}", self.current_prompt, first_line1, first_line2, last_line1, last_line2)
        return "break"

    def newline(self, event):
        # make a newline for Return
        self.text_widget.insert(tk.END, "\n")
        return "break"

    def do_nothing(self, event):
        # just useful to make a tkinter component do nothing. Might not always work (eg: for tag related method/function, etc)
        return "break"

    def execute_command(self, event):
        text_last_line = int(self.text_widget.index(tk.END).split(".")[0]) - 1
        print(self.current_prompt, text_last_line)
        command = self.text_widget.get(f"{self.current_prompt}.0", f"{text_last_line}.end").strip()
        print([command])
        if not command:
            self.prompt_widget.insert('end', '\n>>> ')
            self.prompt_widget.see('end')

            meow = int(self.text_widget.index(tk.END).split(".")[0])
            self.current_prompt = meow
            return

        self.history.append(command)
        self.history_index = len(self.history)
        # so here we both cache the result of any print() used, and reuse the global namespace and local namespace,
        # so we can execute command "non-continuously", like modern REPL, eg: ipython
        global_ns = sys.modules['__main__'].__dict__
        local_ns = {}
        stdout = sys.stdout
        sys.stdout = io.StringIO()

        try:
            # Parse the input command into an AST
            parsed_ast = ast.parse(command, filename='<input>', mode='exec')

            # Check if the parsed AST consists of a single expression
            is_single_expr = len(parsed_ast.body) == 1 and isinstance(parsed_ast.body[0], ast.Expr)

            if is_single_expr:
                # Evaluate the single expression and print the result
                expr = ast.Expression(parsed_ast.body[0].value)
                code = compile(expr, '<input>', 'eval')
                result = eval(code, global_ns, local_ns)
                print(result)
            else:
                # Execute multiple statements
                code = compile(parsed_ast, '<input>', 'exec')
                exec(code, global_ns, local_ns)

            result = sys.stdout.getvalue()
            global_ns.update(local_ns)
        except SystemExit:
            raise
        except Exception as e:
            result = str(e)

        sys.stdout = stdout

        # we insert the result
        self.text_widget.insert(tk.END, f"\n{result}")
        meow = int(self.prompt_widget.index(tk.END).split(".")[0])
        meow2 = int(self.text_widget.index(tk.END).split(".")[0])
        print(meow, meow2)
        if meow2 > meow:
            for i in range(meow, meow2):
                print(i)
                self.prompt_widget.insert(f"{i}.0", "\n")
        self.prompt_widget.insert('end', '\n>>> ')
        self.prompt_widget.yview_moveto(self.text_widget.yview()[1])
        self.prompt_widget.see('end')
        meow = int(self.text_widget.index(tk.END).split(".")[0])
        self.current_prompt = meow

    def is_last_line(self, event):
        # useful method to know if our blinking cursor is currently on current valid latest prompt, which is equal to the latest "\n>>> " in the first widget, and current line in the second widget
        current_line = int(self.text_widget.index(tk.INSERT).split(".")[0])
        prompt_last_line = self.current_prompt

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
        prompt_last_line = self.current_prompt
        current_line = int(self.text_widget.index(tk.INSERT).split(".")[0])
        text_last_line = int(self.text_widget.index(tk.END).split(".")[0]) - 1
        if event.keysym == "Up" and current_line == prompt_last_line:
            if self.history_index > 0:
                self.history_index -= 1
                self.text_widget.delete(f"{prompt_last_line}.0", f"{text_last_line}.end")
                self.text_widget.insert(f"{prompt_last_line}.0", self.history[self.history_index])
                meow = int(self.prompt_widget.index(tk.END).split(".")[0])
                meow2 = int(self.text_widget.index(tk.END).split(".")[0])
                print("meow:", meow, "meow2:", meow2)
                if meow2 > meow:
                    for i in range(meow, meow2):
                        self.prompt_widget.insert(f"{i}.0", "\n")
                elif meow2 < meow:
                    for i in range(meow2, meow):
                        self.prompt_widget.delete(f"{i}.0")
                self.text_widget.see("end")
                self.prompt_widget.see("end")
            return "break"
        elif event.keysym == "Down" and current_line == text_last_line:
            print("nope sadly")
            print(text_last_line, prompt_last_line)
            if self.history_index < len(self.history) - 1:
                self.history_index += 1
                lenght_history = self.history[self.history_index]
                self.text_widget.delete(f"{prompt_last_line}.0", f"{text_last_line}.end")
                self.text_widget.insert(f"{prompt_last_line}.0", self.history[self.history_index])
                meow = int(self.prompt_widget.index(tk.END).split(".")[0])
                meow2 = int(self.text_widget.index(tk.END).split(".")[0])
                print("meow:", meow, "meow2:", meow2)
                if meow2 > meow:
                    for i in range(meow, meow2):
                        self.prompt_widget.insert(f"{i}.0", "\n")
                elif meow2 < meow:
                    for i in range(meow2, meow):
                        self.prompt_widget.delete(f"{i}.0")
                self.text_widget.mark_set("insert", f"{prompt_last_line}.end")
                self.text_widget.see("end")
                self.prompt_widget.see("end")
            return "break"


root = tk.Tk()
repl = REPL(master=root)
repl.mainloop()
