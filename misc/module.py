
class Settings:
    def __init__(self):
        # Names of the values, for showing in the options box
        self._names_ = {
            'value':'Value: ',
        }
        # Units to go with the value, use `` if no units
        self._units_ = {
            'value':'U'
        }
        self.value = 10

        # A help string to show in the help menu
        self.help_text = '   Some generic help text\n\n'+\
                         '   This can be multi-line, etc.'

        # This is the label to click to ge the above help text,
        # this is also used for the label in the settings dropdown
        self._label = 'Generic Setting'

        # If this is set to a function, it will be called whenever
        # the settings have been changed via a gui interaction
        self._callback = None

class Menu:
    def __init__(self):
        self._opts_order = []
        self._help_order = self._opts_order
        self._options = {}
        self._labels = {}
        self._helps= {}
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

class Module:

    def __init__(self, root):

        # This is the gui instance that owns this module.
        self._root = root

        # We need to have a settings object.
        self.settings = Settings()
    
    def get_tk(self):
        # This returns the TK root object.
        return self._root.root

    def on_start(self):
        # This is called when the module is first added, after making the settings,
        # menus, etc.
        print("Done setup")

    def on_stop(self):
        # This is called when the program is exited
        print("Closing")

    def get_settings(self):
        # Return an array or collection of settings here
        # Module can have more than 1 set of settings.
        return [self.settings]

    def get_menus(self):

        # This returns what menus (except for settings) should be made for this
        # module. This example adds a "Misc" dropdown, with 3 values, and 1 separator

        def run_misc():
            # Dummy function for the menu example
            print("misc run")
        
        _misc_menu = Menu()

        # Add some options, the value is the function to run on click
        _misc_menu._options["misc_1"] = lambda: run_misc()
        _misc_menu._options["misc_2"] = lambda: run_misc()
        _misc_menu._options["misc_3"] = lambda: run_misc()

        _misc_menu._opts_order.append("misc_1")
        _misc_menu._opts_order.append("misc_2")
        _misc_menu._opts_order.append("sep") # "sep" is reserved to place a separator in the dropdown
        _misc_menu._opts_order.append("misc_3")

        # Adds some help menu text for these as well
        _misc_menu._helps["misc_1"] = 'Help info for misc_1, can be multiline if needed'
        _misc_menu._helps["misc_2"] = 'Help info for misc_2, can be multiline if needed'
        _misc_menu._helps["misc_3"] = 'Help info for misc_3, can be multiline if needed'

        # Adds labels for the non-separator values
        _misc_menu._labels["misc_1"] = "Misc_1"
        _misc_menu._labels["misc_2"] = "Misc_2"
        _misc_menu._labels["misc_3"] = "Misc_3"

        # Specify a label for the menu
        _misc_menu._label = "Misc Menu"

        # Returns an array of menus (only 1 in this case)
        return [_misc_menu]
