from functools import update_wrapper
from importlib import resources
from inspect import getmembers
from pathlib import Path
from typing import Callable, Optional

from gi.repository import Gtk
from gi.repository.GdkPixbuf import InterpType

from interface.view import View


class GtkInterface:
    instance = None
    interface_markup = resources.read_text('interface', 'HImaKura.glade')

    class Handler:
        def __init__(self, h: Callable):
            update_wrapper(self, h)
            self.local_handler = h

        def __call__(self, *args, **kwargs):
            return self.local_handler(*args, **kwargs)

    _builder: Gtk.Builder
    selected_dir: Optional[str]
    view: Optional[View]

    @Handler
    def show_dir_selector(self):
        self["DirectoryOpener"].show_all()

    @Handler
    def hide_dir_selector(self):
        self["DirectoryOpener"].hide()

    @Handler
    def change_selected_dir(self):
        self.selected_dir = self["DirectoryOpener"].get_filename()
        self["ChooserButton"].set_sensitive(True)

    @Handler
    def setup_view(self):
        self["DirectoryOpener"].hide()
        self.view = View(Path(self.selected_dir))
        self["NextButton"].set_sensitive(True)
        self["AuthorField"].set_sensitive(True)
        self["UniverseField"].set_sensitive(True)
        self["CharactersField"].set_sensitive(True)
        self["TagsField"].set_sensitive(True)
        self["SaveButton"].set_sensitive(True)
        self["ClearButton"].set_sensitive(True)

        self.show_next_image(self)

    @Handler
    def refresh_image(self):
        if self.view is not None:
            panel = self["ImageSurface"]
            img_pix = self.view.get_image()
            img_width, img_height = img_pix.get_width(), img_pix.get_height()
            ratio = img_width / img_height
            view_alloc = self["ImagePort"].get_allocation()
            view_width, view_height = view_alloc.width, view_alloc.height

            if img_width > view_width:
                img_width = view_width
                img_height = (1 / ratio) * view_width
            if img_height > view_height:
                img_height = view_height
                img_width = ratio * view_height

            panel.set_from_pixbuf(img_pix.scale_simple(img_width, img_height, InterpType.BILINEAR))

    @Handler
    def show_previous_image(self):
        try:
            self.view.prev()
            self["NextButton"].set_sensitive(True)
        except StopIteration:
            self["PrevButton"].set_sensitive(False)

        self.refresh_image(self)
        self.load_meta()

    @Handler
    def show_next_image(self):
        try:
            self.view.next()
            self["PrevButton"].set_sensitive(True)
        except StopIteration:
            self["NextButton"].set_sensitive(False)

        self.refresh_image(self)
        self.load_meta()

    @Handler
    def clear_fields(self):
        self["AuthorField"].set_text('')
        self["UniverseField"].set_text('')
        self["CharactersField"].set_text('')
        self["TagsField"].get_buffer().set_text('')

    def load_meta(self):
        author = self.view.get_author()
        self["AuthorField"].set_text(author if author is not None else '')
        universe = self.view.get_universe()
        self["UniverseField"].set_text(universe if universe is not None else '')
        characters = self.view.get_characters()
        self["CharactersField"].set_text(characters if characters is not None else '')
        tags = self.view.get_tags()
        self["TagsField"].get_buffer().set_text(tags if tags is not None else '')

    @Handler
    def save_meta(self):
        self.view.set_author(self["AuthorField"].get_text())
        self.view.set_universe(self["UniverseField"].get_text())
        self.view.set_characters(self["CharactersField"].get_text())

        tags_buffer = self["TagsField"].get_buffer()
        self.view.set_tags(tags_buffer.get_text(tags_buffer.get_start_iter(), tags_buffer.get_end_iter(), False))

        self.view.write()

    def _wrap_handler(self, c: Callable):
        return lambda *args: c(self)

    def launch(self):
        self["MainWindow"].show_all()
        Gtk.main()

    def __new__(cls):
        if cls.instance is None:
            new_instance = object.__new__(cls)
            signal_mapping = dict()
            for name, func in getmembers(new_instance, lambda m: isinstance(m, cls.Handler)):
                signal_mapping[name] = new_instance._wrap_handler(func)

            signal_mapping["hide_on_delete"] = lambda *args: args[0].hide_on_delete()
            signal_mapping["quit_program"] = Gtk.main_quit

            builder = Gtk.Builder.new_from_string(cls.interface_markup, -1)
            builder.connect_signals(signal_mapping)

            new_instance._builder = builder
            new_instance.selected_dir = None
            new_instance.view = None

            cls.instance = new_instance

        return cls.instance

    def __getitem__(self, item: str):
        if not isinstance(item, str):
            raise TypeError("Expected a string, given a: " + str(type(item)))

        return self._builder.get_object(item)
