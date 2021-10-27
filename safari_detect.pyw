#!/usr/bin/env python3

import tkinter as tk

import platform     # Linux vs Windows check

# We use this for parsing numbers in input fields
import data_files.safari_input as safari_input

import detect_module

if platform.system() == 'Windows':
    font_12 = ('Times New Roman', 12)
    font_14 = ('Times New Roman', 14)
    font_16 = ('Times New Roman', 16)
    font_18 = ('Times New Roman', 18)
    font_20 = ('Times New Roman', 20)
else:
    font_12 = ('DejaVu Sans', 12)
    font_14 = ('DejaVu Sans', 14)
    font_16 = ('DejaVu Sans', 16)
    font_18 = ('DejaVu Sans', 18)
    font_20 = ('DejaVu Sans', 20)

instances = []

# Constructs and starts an instance of the gui
def spawn_gui_proc():
    gui = DetectGui()
    root = None
    if len(instances) != 0:
        root = tk.Toplevel(instances[0].root)
    instances.append(gui)
    gui.start(root=root)

# Starts an instance of the gui as a new process
def spawn_gui():
    spawn_gui_proc()

class Menu:
    def __init__(self):
        self._opts_order = []
        self._help_order = self._opts_order
        self._options = {}
        self._labels = {}
        self._helps = {}
        self._label = ''

    def is_same(self, other):
        return other._label == self._label
    

    def merge_in(self, other):
        if not self.is_same(other):
            return other

        self._opts_order.append('sep')
        self._opts_order.extend(other._opts_order)

        for key, val in other._options.items():
            self._options[key] = val
        for key, val in other._labels.items():
            self._labels[key] = val
        for key, val in other._helps.items():
            self._helps[key] = val

        return self

class DetectGui:

    def __init__(self):
        self._modules = [detect_module.Module(self)]
        self.base_name = "SAFARI Detect"

        # Three initial menus
        _file_menu = Menu()
        self.settings_menu = Menu()
        self.help_menu = Menu()

        _file_menu._label = "File"
        self.settings_menu._label = "Settings"
        self.help_menu._label = "Help"

        _file_menu._options["new_instance"] = lambda: spawn_gui()
        _file_menu._labels["new_instance"] = "New Instance"
        _file_menu._helps["new_instance"] = 'Opens another copy of this window'

        _file_menu._opts_order.append("new_instance")

        all_menus = []
        
        self._settings = []
        
        for mod in self._modules:
            all_menus.extend(mod.get_menus())
            self._settings.extend(mod.get_settings())

        self._menus = []

        self._menus.append(_file_menu)
        self._menus.append(self.settings_menu)

        # Initialise settings menus here
        self.build_settings()

        for menu in all_menus:
            shouldAdd = not self.help_menu.is_same(menu)
            
            if not shouldAdd:
                self.help_menu.merge_in(menu)
                continue

            for old in self._menus:
                same = old.is_same(menu)
                if same:
                    shouldAdd = False
                    old.merge_in(menu)
                    break

            if not shouldAdd:
                continue
            self._menus.append(menu)

        self._menus.append(self.help_menu)

        self.aboutMessage = 'Analysis code for SAFARI data files\nimport a data file using the File menu.'
        self.copyrightMessage = 'Copyright © 2021 Patrick Johnson All Rights Reserved.'

        _file_menu._options["exit"] = lambda: self.exit_detect()

        _file_menu._opts_order.append("sep")
        _file_menu._opts_order.append("exit")

        _file_menu._labels["exit"] = "Exit"
        _file_menu._helps["exit"] = 'Exits this window (exits all if this was first window opened)'

    def build_settings(self):
        for setting in self._settings:
            key = setting._label
            help_msg = setting.help_text
            callback = setting._callback
            self.build_setting(key, help_msg, callback, setting)

    def build_setting(self, key, help_msg, callback, setting):
        self.settings_menu._options[key] = lambda: self.edit_options(setting, key, callback)
        self.settings_menu._opts_order.append(key)
        self.settings_menu._labels[key] = key
        self.settings_menu._helps[key] = help_msg

    # Starts the tk application, adds the file menus, etc
    def start(self, root=None):
        if root == None:
            self.root = tk.Tk()
            self.first = True
        else:
            self.root = root
            self.base_name = "SAFARI Detect {}".format(len(instances))
            self.first = False

        main_menu = tk.Menu(self.root)
        self.root.config(menu=main_menu)

        self.root.title(self.base_name)
        self.root.geometry("1280x768")
        self.root.protocol("WM_DELETE_WINDOW", self.exit_detect)
        if platform.system() == 'Windows':
            self.root.iconbitmap("sins-lab.ico")

        # Here we actually make/add the menus
        for menu in self._menus:
            # Help menu is handled differently.
            if menu == self.help_menu:
                continue
            _new_menu = tk.Menu(main_menu, tearoff=0)
            main_menu.add_cascade(label=menu._label, menu=_new_menu)
            # Add options in specified order
            for opt in menu._opts_order:
                if opt == 'sp' or opt == 'sep':
                    _new_menu.add_separator()
                    continue
                label = menu._labels[opt]
                cmd = menu._options[opt]
                _new_menu.add_command(label=label, command=cmd)

        # Now add the help menus
        _new_menu = tk.Menu(main_menu, tearoff=0)
        main_menu.add_cascade(label=self.help_menu._label, menu=_new_menu)
        for menu in self._menus:
            if menu == self.help_menu:
                continue
            name = menu._label
            # Here we just add the callback to bring up the help submenus
            _new_menu.add_cascade(label=name, menu=self.make_help_submenu(menu._opts_order, menu, _new_menu))
        _new_menu.add_command(label='About', command= lambda: self.about())

        for mod in self._modules:
            mod.on_start()

        if root == None:
            self.root.mainloop()

    #Opens About Window with description of software
    def about(self):
        t = tk.Toplevel(self.root)
        t.wm_title("About")
        l = tk.Label(t, text = self.aboutMessage, font = font_14)
        l.pack(side="top", fill="both", expand=True, padx=100, pady=100)
        messageVar = tk.Message(t, text = self.copyrightMessage, fg='black', font = font_14, width = 600)
        messageVar.place(relx = 0.5, rely = 1, anchor = tk.S)

    # Wrapper for making a submenu, so that the keys and the submenu are in new scope.
    def make_help_submenu(self, keys, menu, helpmenu):
        submenu = tk.Menu(helpmenu, tearoff=0)
        for key in keys:
            if not key in menu._helps:
                continue
            if key == 'sp' or key == 'sep':
                submenu.add_separator()
                continue
            label = menu._labels[key]
            msg = menu._helps[key]
            submenu.add_command(label=label, command=self.make_help_settings(label, msg))
        return submenu

    # Wrapper for the help_settings so that label and msg are in new scope.
    def make_help_settings(self, label, msg):
        return lambda: self.help_settings(label, msg)

    # Actually makes the setting option
    def help_settings(self, title, msg):
        t = tk.Toplevel(self.root)
        t.wm_title(title)
        l = tk.Text(t, font = font_14)
        l.insert('end',msg)
        l.config(state='disabled')
        l.pack(side="top", fill="both", expand=True, padx=100, pady=100)

    # Exits the application
    def exit_detect(self):
        
        for mod in self._modules:
            mod.on_stop()
        if(self.first):
            self.root.quit()
        self.root.destroy()

    # Generates a window with options for editing floating point fields for thing
    # thing must have a _names_ attribute which is a map of <attr> to <name>, where
    # <name> is what the box will be labelled. These values should all be floats!
    def edit_options(self, thing, name, callback):
        window = tk.Toplevel(self.root)
        window.wm_title(name)
        dh = 22
        h = int(len(thing._names_)*dh + 150)
        window.geometry('400x{}'.format(h))

        x_orig = 160

        fields = {}
        bools = {}
        i = 0
        for key,value in thing._names_.items():
            label = tk.Label(window, text = value, font = font_12)
            label.place(x=x_orig, y=50 + i * dh, anchor = tk.E)

            attr = getattr(thing,key)
            if isinstance(attr, bool):
                # Make an IntVar to store button check state
                var = tk.IntVar()
                var.set(1 if attr else 0)
                entry = tk.Checkbutton(window, variable=var)
                entry.place(x=x_orig, y=50 + i * dh, anchor = tk.W)
                fields[key] = entry
                bools[key] = var
            else:
                entry = tk.Entry(window, font = font_12, width = 10)
                entry.insert(0, attr)
                entry.place(x=x_orig, y=50 + i * dh, anchor = tk.W)

                fields[key] = entry

            label = tk.Label(window, text = thing._units_[key], font = font_12)
            label.place(x=x_orig + 100, y=50 + i * dh, anchor = tk.W)

            i = i + 1

        def update():
            for key,value in fields.items():
                if key in bools:
                    var = bools[key]
                    setattr(thing, key, True if var.get() else False)
                else:
                    setattr(thing, key, safari_input.parseVar(value.get()))
            if callback is not None:
                callback(window)
            elif window is not None:
                window.destroy()
        
        do_update = update
        def return_pressed(*args):
            do_update()
        window.bind('<Return>', return_pressed)
        
        update_button = tk.Button(window, text = 'Update', relief = 'raised', activebackground='green', font = font_16, width = 15, height = 1,\
                    command = update)
        update_button.place(relx=0.5, y=h-60, anchor = tk.CENTER)
        cancel_button = tk.Button(window, text = 'Cancel', relief = 'raised', activebackground='red', font = font_16, width = 15, height = 1,\
                    command = lambda: [window.destroy()])
        cancel_button.place(relx=0.5, y=h-20, anchor = tk.CENTER)

def start():
    if len(instances) == 0:
        spawn_gui_proc()

if __name__ == '__main__':
    start()