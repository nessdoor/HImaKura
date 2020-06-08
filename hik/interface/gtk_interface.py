from importlib import resources
from inspect import getmembers
from pathlib import Path
from typing import Callable, Optional

from gi.repository import Gtk, GLib
from gi.repository.GdkPixbuf import InterpType

from data.filtering import FilterBuilder
from interface.view import View


def signal_handler(h: Callable):
    """Mark function as a signal handler."""

    h._signal_handler = True
    return h


# TODO This class has become gargantuan and ugly. Refactor asap
class GtkInterface:
    """
    Singleton representing the application's GTK interface.

    The sole instance is created on demand and is initialized with the UI's XML description, contained in
    `HImaKura.glade`.
    Some of its methods are marked as handlers and invoked by the GTK loop.
    """

    instance = None
    interface_markup = resources.read_text('interface', 'HImaKura.glade')

    _builder: Gtk.Builder
    selected_dir: Optional[str]
    view: Optional[View]
    filter_builder: Optional[FilterBuilder]

    @signal_handler
    def show_dir_selector(self, *args):
        window = self["DirectoryOpener"]
        window.show_all()

    @signal_handler
    def hide_dir_selector(self, *args):
        self["DirectoryOpener"].hide()

    @signal_handler
    def change_selected_dir(self, *args):
        """Alter the currently selected directory."""

        self.selected_dir = self["DirectoryOpener"].get_filename()
        self["ChooserButton"].set_sensitive(True)

    @signal_handler
    def show_filter_editor(self, *args):
        self["FilterEditor"].show_all()

    @signal_handler
    def set_filters(self, *args):
        """Configure a filter builder and setup a filtered view."""

        self["FilterEditor"].hide()
        self.metadata_box_sensitiveness(False)

        # Configure all filters in one, ugly pass
        self.filter_builder = FilterBuilder()
        for spec in self["IdFilters"]:
            self.filter_builder.id_constraint(spec[0], spec[1])
        for spec in self["FilenameFilters"]:
            self.filter_builder.filename_constraint(spec[0], spec[1])
        for spec in self["AuthorFilters"]:
            self.filter_builder.author_constraint(spec[0], spec[1])
        for spec in self["UniverseFilters"]:
            self.filter_builder.universe_constraint(spec[0], spec[1])
        for spec in self["CharacterFilters"]:
            self.filter_builder.character_constraint(spec[0], spec[1])
        for spec in self["TagFilters"]:
            self.filter_builder.tag_constraint(spec[0], spec[1])

        self.filter_builder.characters_as_disjunctive(self["CharactersDisjunctiveSwitch"].get_active())
        self.filter_builder.tags_as_disjunctive(self["TagsDisjunctiveSwitch"].get_active())

        self.setup_view()

    @signal_handler
    def clear_filters(self, *args):
        """Scrap the filter builder and re-setup view."""

        self["FilterEditor"].hide()
        self.metadata_box_sensitiveness(False)
        self.filter_builder = None
        self.setup_view()

    @signal_handler
    def add_filter(self, *args):
        """Append an empty filter rule to the focused table."""

        args[0].append()

    @signal_handler
    def del_filter(self, *args):
        """Delete the selected filter rule from the focused table."""

        selected = self[args[0].get_name() + "Selection"].get_selected()[1]
        if selected is not None:
            args[0].remove(selected)

    @signal_handler
    def filter_edited(self, *args):
        """Set the new filter matcher on the edited filter rule."""

        store = args[0]
        store.set_value(store.get_iter(args[1]), 0, args[2])

    @signal_handler
    def filter_neg_toggle(self, *args):
        """Toggle the excluded flag on the edited filter rule."""

        store = args[0]
        siter = store.get_iter(args[1])
        store.set_value(siter, 1, not store.get_value(siter, 1))

    @signal_handler
    def setup_view(self, *args):
        """Setup the View object and activate buttons and fields."""

        def _prev_callback(view: View):
            self.refresh_image()
            self.load_meta()

            self["PrevButton"].set_sensitive(view.has_prev())
            self["NextButton"].set_sensitive(view.has_next())

        def _next_callback(view: View):
            self.refresh_image()
            self.load_meta()

            self["PrevButton"].set_sensitive(view.has_prev())
            self["NextButton"].set_sensitive(view.has_next())

        self["DirectoryOpener"].hide()
        try:
            self.view = View(Path(self.selected_dir), self.filter_builder)
            self.view.set_prev_callback(_prev_callback)
            self.view.set_next_callback(_next_callback)

            # Initialize the UI only if the selected directory has images inside
            if self.view.has_next():
                self.view.load_next()
                self.metadata_box_sensitiveness(True)
                self["FilterEditorButton"].set_sensitive(True)
            else:
                self["ImageSurface"].clear()
        except OSError as ose:
            # Show error popup
            error_dialog = self["ErrorDialog"]
            error_dialog.set_markup("<b>Error opening " + self.selected_dir + "</b>")
            error_dialog.format_secondary_text(str(ose))
            error_dialog.show_all()
        except GLib.Error as ge:
            # Invalid data on first image
            error_dialog = self["ErrorDialog"]
            error_dialog.set_markup("<b>Error while loading first image</b>")
            error_dialog.format_secondary_text(ge.message)
            error_dialog.show_all()
            # Optimistically enable forward-iteration
            self["NextButton"].set_sensitive(True)

    def metadata_box_sensitiveness(self, sensitive: bool):
        self["AuthorField"].set_sensitive(sensitive)
        self["UniverseField"].set_sensitive(sensitive)
        self["CharactersField"].set_sensitive(sensitive)
        self["TagsField"].set_sensitive(sensitive)
        self["SaveButton"].set_sensitive(sensitive)
        self["ClearButton"].set_sensitive(sensitive)

    @signal_handler
    def refresh_image(self, *args):
        """Reload, resize and refresh the displayed image, taking it from the backing View object."""

        if self.view is not None and self.view.has_image_data():
            panel = self["ImageSurface"]
            img_pix = self.view.get_image_contents()
            img_width, img_height = img_pix.get_width(), img_pix.get_height()
            # Get the visible area's size
            view_alloc = self["ImagePort"].get_allocation()
            view_width, view_height = view_alloc.width, view_alloc.height

            # If the visible area is smaller than the image, calculate the scaling factor and set the new image sizes
            # (Thanks to https://stackoverflow.com/a/1106367/13140497 for leading me down the right path)
            if img_width > view_width or img_height > view_height:
                s_fact = min(view_width / img_width, view_height / img_height)
                img_width, img_height = img_width * s_fact, img_height * s_fact

            # Load and resize the image
            panel.set_from_pixbuf(img_pix.scale_simple(img_width, img_height, InterpType.BILINEAR))

    @signal_handler
    def show_previous_image(self, *args):
        try:
            self.view.load_prev()
        except StopIteration:
            # In case something goes wrong with the iteration, disable further movement in this direction
            self["PrevButton"].set_sensitive(False)
        except GLib.Error as ge:
            # Invalid image data
            error_dialog = self["ErrorDialog"]
            error_dialog.set_markup("<b>Error while loading previous image</b>")
            error_dialog.format_secondary_text(ge.message)
            error_dialog.show_all()

    @signal_handler
    def show_next_image(self, *args):
        try:
            self.view.load_next()
        except StopIteration:
            # In case something goes wrong with the iteration, disable further movement in this direction
            self["NextButton"].set_sensitive(False)
        except GLib.Error as ge:
            # Invalid image data
            error_dialog = self["ErrorDialog"]
            error_dialog.set_markup("<b>Error while loading next image</b>")
            error_dialog.format_secondary_text(ge.message)
            error_dialog.show_all()

    @signal_handler
    def clear_fields(self, *args):
        self["AuthorField"].set_text('')
        self["UniverseField"].set_text('')
        self["CharactersField"].set_text('')
        self["TagsField"].get_buffer().set_text('')

    def load_meta(self):
        """Display metadata, pre-filling the fields."""

        self["IDLabel"].set_label(str(self.view.image_id))
        self["FileNameLabel"].set_label(self.view.filename)
        author = self.view.get_author()
        self["AuthorField"].set_text(author if author is not None else '')
        universe = self.view.get_universe()
        self["UniverseField"].set_text(universe if universe is not None else '')
        characters = self.view.get_characters()
        self["CharactersField"].set_text(characters if characters is not None else '')
        tags = self.view.get_tags()
        self["TagsField"].get_buffer().set_text(tags if tags is not None else '')

    @signal_handler
    def save_meta(self, *args):
        """Overwrite the image's metadata with the field's contents."""

        self.view.set_author(self["AuthorField"].get_text())
        self.view.set_universe(self["UniverseField"].get_text())
        self.view.set_characters(self["CharactersField"].get_text())

        tags_buffer = self["TagsField"].get_buffer()
        self.view.set_tags(tags_buffer.get_text(tags_buffer.get_start_iter(), tags_buffer.get_end_iter(), False))

        try:
            self.view.write()
        except OSError as ose:
            error_dialog = self["ErrorDialog"]
            error_dialog.set_markup("<b>Error while saving metadata</b>")
            error_dialog.format_secondary_text(str(ose))
            error_dialog.show_all()

    def launch(self):
        """Show the main window and start the GTK thread."""

        self["MainWindow"].show_all()
        Gtk.main()

    def __new__(cls):
        """Create the new singleton, if not already existing, and return it. Otherwise, return the existing one."""

        if cls.instance is None:
            new_instance = object.__new__(cls)
            signal_mapping = dict()
            # Register the signal handlers
            for name, meth in getmembers(new_instance, lambda m: hasattr(m, '_signal_handler') and m._signal_handler):
                signal_mapping[name] = meth

            # Special handler for GTK's hide-on-delete
            signal_mapping["hide_on_delete"] = lambda *args: args[0].hide_on_delete()
            # Handler for quitting. There was no point in keeping this as a static method (maybe).
            signal_mapping["quit_program"] = Gtk.main_quit

            builder = Gtk.Builder.new_from_string(cls.interface_markup, -1)
            builder.connect_signals(signal_mapping)

            new_instance._builder = builder
            new_instance.selected_dir = None
            new_instance.view = None
            new_instance.filter_builder = None

            cls.instance = new_instance

        return cls.instance

    def __getitem__(self, item: str):
        """Retrieve the corresponding GTK widget."""

        if not isinstance(item, str):
            raise TypeError("Expected a string, given a: " + str(type(item)))

        return self._builder.get_object(item)
