import gi

gi.require_version('Gtk', '3.0')
from gi.repository import Gtk


def quit_program(*args):
    Gtk.main_quit()


builder = Gtk.Builder()
builder.add_from_file("HImaKura.glade")
main_window = builder.get_object("MainWindow")
dir_selector = builder.get_object("DirectoryOpener")

signal_mapping = {'show_dir_selector': lambda *args: dir_selector.show_all(),
                  'hide_dir_selector': lambda *args: dir_selector.hide(),
                  'hide_on_delete': lambda *args: args[0].hide_on_delete(),
                  'quit_program': lambda *args: Gtk.main_quit()}

builder.connect_signals(signal_mapping)

main_window.show_all()

Gtk.main()
