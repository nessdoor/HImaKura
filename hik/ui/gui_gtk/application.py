from importlib import resources

from gi.repository import Gtk, Gio

from ui.gui_gtk.interface import Signals, State


class GtkInstance(Gtk.Application):
    """The GTK application instance for HImaKura."""

    appId = "network.entropic.himakura"
    interface_markup = resources.read_text('ui.gui_gtk', 'HImaKura.glade')

    def __init__(self):
        super().__init__(application_id=self.appId, flags=Gio.ApplicationFlags.FLAGS_NONE)

        # Connect signal handlers for this application
        self.connect("startup", self.startup)
        self.connect("activate", self.activate)
        self.connect("shutdown", self.shutdown)

    def startup(self, *args):
        """Load the interface description file and connect the signal handlers."""

        State.builder = Gtk.Builder.new_from_string(self.interface_markup, -1)
        State.builder.connect_signals(Signals.handlers)
        
        # Attach special change-detection handler to the buffer of the tags box, since it can't be done from Glade
        State.get_object("TagsField").get_buffer().connect("changed", Signals.handlers["set_changed_flag"])

    def activate(self, *args):
        """Register the application window with the instance and show the main interface."""

        main_window = State.get_object("MainWindow")
        self.add_window(main_window)
        main_window.present()

    def shutdown(self, *args):
        """Destroy the application window."""

        State.get_object("MainWindow").destroy()
