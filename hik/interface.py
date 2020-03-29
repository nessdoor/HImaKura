from pathlib import Path

import gi
gi.require_version('GdkPixbuf', '2.0')
from gi.repository.GdkPixbuf import InterpType

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

    show_next_image()


def refresh_image(*args):
    global builder
    global view

    if view is not None:
        panel = builder.get_object("ImageSurface")
        img_pix = view.get_image()
        img_width , img_height = img_pix.get_width(), img_pix.get_height()
        ratio = img_width / img_height
        view_alloc = builder.get_object("ImagePort").get_allocation()
        view_width, view_height = view_alloc.width, view_alloc.height

        if img_width > view_width:
            img_width = view_width
            img_height = (1 / ratio) * view_width
        if img_height > view_height:
            img_height = view_height
            img_width = ratio * view_height

        panel.set_from_pixbuf(img_pix.scale_simple(img_width, img_height, InterpType.BILINEAR))


def load_meta():
    author = view.get_author()
    builder.get_object("AuthorField").set_text(author if author is not None else '')
    universe = view.get_universe()
    builder.get_object("UniverseField").set_text(universe if universe is not None else '')
    characters = view.get_characters()
    builder.get_object("CharactersField").set_text(characters if characters is not None else '')
    tags = view.get_tags()
    builder.get_object("TagsField").get_buffer().set_text(tags if tags is not None else '')


def show_previous_image(*args):
    global view

    try:
        view.prev()
        builder.get_object("NextButton").set_sensitive(True)
    except StopIteration:
        builder.get_object("PrevButton").set_sensitive(False)
    refresh_image()
    load_meta()


def show_next_image(*args):
    global view

    try:
        view.next()
        builder.get_object("PrevButton").set_sensitive(True)
    except StopIteration:
        builder.get_object("NextButton").set_sensitive(False)
    refresh_image()
    load_meta()


signal_mapping = {'show_dir_selector': lambda *args: dir_selector.show_all(),
                  'hide_dir_selector': lambda *args: dir_selector.hide(),
                  'change_dir': change_selected_dir,
                  'set_as_dir': setup_view,
                  'show_previous_image': show_previous_image,
                  'show_next_image': show_next_image,
                  'refresh_image': refresh_image,
                  'hide_on_delete': lambda *args: args[0].hide_on_delete(),
                  'quit_program': lambda *args: Gtk.main_quit()}

builder.connect_signals(signal_mapping)

main_window.show_all()

Gtk.main()
