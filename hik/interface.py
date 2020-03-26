from pathlib import Path

import gi

from view import View

gi.require_version('Gtk', '3.0')
from gi.repository import Gtk

builder = Gtk.Builder()
builder.add_from_file("HImaKura.glade")
main_window = builder.get_object("MainWindow")
dir_selector = builder.get_object("DirectoryOpener")

selected_dir = None
view = None


def change_selected_dir(button):
    global selected_dir

    selected_dir = dir_selector.get_filename()
    button.set_sensitive(True)


def setup_view(*args):
    global view

    dir_selector.hide()
    view = View(Path(selected_dir))
    builder.get_object("NextButton").set_sensitive(True)
    builder.get_object("AuthorField").set_sensitive(True)
    builder.get_object("UniverseField").set_sensitive(True)
    builder.get_object("CharactersField").set_sensitive(True)
    builder.get_object("TagsField").set_sensitive(True)
    view.next()

    refresh_image()


def refresh_image():
    global builder
    global view

    builder.get_object("ImagePanel").set_from_pixbuf(view.get_image())


def show_previous_image(*args):
    global view

    try:
        view.prev()
        builder.get_object("NextButton").set_sensitive(True)
    except StopIteration:
        builder.get_object("PrevButton").set_sensitive(False)
    refresh_image()


def show_next_image(*args):
    global view

    try:
        view.next()
        builder.get_object("PrevButton").set_sensitive(True)
    except StopIteration:
        builder.get_object("NextButton").set_sensitive(False)
    refresh_image()


signal_mapping = {'show_dir_selector': lambda *args: dir_selector.show_all(),
                  'hide_dir_selector': lambda *args: dir_selector.hide(),
                  'change_dir': change_selected_dir,
                  'set_as_dir': setup_view,
                  'show_previous_image': show_previous_image,
                  'show_next_image': show_next_image,
                  'hide_on_delete': lambda *args: args[0].hide_on_delete(),
                  'quit_program': lambda *args: Gtk.main_quit()}

builder.connect_signals(signal_mapping)

main_window.show_all()

Gtk.main()
