from pathlib import Path
from typing import Callable, Optional, MutableMapping

from gi.repository import Gtk, GLib
from gi.repository.GdkPixbuf import InterpType

from data.filtering import FilterBuilder
from ui.gui_gtk.view import GtkView


class Signals:
    """A registry class for keeping track of signal handlers."""

    handlers: MutableMapping[str, Callable] = dict()

    @classmethod
    def register(cls, h: Callable) -> Callable:
        """Register a new handler."""

        cls.handlers[h.__name__] = h
        return h


# TODO can this global state be turned into a more rational state representation?
class State:
    """Impure class containing the few stateful objects for the GTK interface."""

    builder: Gtk.Builder = None
    view: GtkView = None
    inhibit_changed: bool = False
    changed: bool = False
    interrupted_action: Optional[Callable] = None

    @classmethod
    def get_object(cls, obj_id: str):
        """Retrieve the GTK object identified by the specified ID."""

        return cls.builder.get_object(obj_id)


# Utilities #
def notify_error(primary: str, secondary: Optional[str] = None):
    """Show an error dialog with the specified primary and secondary text."""

    error_dialog = State.get_object("ErrorDialog")
    error_dialog.set_markup(primary)
    error_dialog.format_secondary_text(secondary)
    error_dialog.show_all()


def metadata_box_sensitiveness(sensitive: bool):
    """Set sensitivity for the whole metadata area."""

    State.get_object("AuthorField").set_sensitive(sensitive)
    State.get_object("UniverseField").set_sensitive(sensitive)
    State.get_object("CharactersField").set_sensitive(sensitive)
    State.get_object("TagsField").set_sensitive(sensitive)
    State.get_object("SaveButton").set_sensitive(sensitive)
    State.get_object("ClearButton").set_sensitive(sensitive)


def trigger_unsaved_warning(continuation: Callable):
    """Display the 'unsaved changes' warning and record the suspended action."""

    State.interrupted_action = continuation
    State.get_object("ChangedWarningDialog").show_all()


@Signals.register
def set_sensitive(obj):
    """Make an object sensitive."""

    obj.set_sensitive(True)


@Signals.register
def set_changed_flag(*args):
    """Set the global 'changed' flag."""

    if not State.inhibit_changed:
        State.changed = True


@Signals.register
def clear(obj):
    """
    Clear the contents of the provided object, if supported.

    For now, only Gtk.Entry and Gtk.TextView objects are cleared.
    """

    if isinstance(obj, Gtk.Entry):
        obj.set_text('')
    elif isinstance(obj, Gtk.TextView):
        obj.get_buffer.set_text('')


@Signals.register
def valid_path_check(chooser):
    """Check if the currently-pointed directory is valid."""

    if chooser.get_filename() is not None:
        set_sensitive(State.get_object("ChooserButton"))


@Signals.register
def debug(*args):
    """Print the arguments received from the GTk signaling system."""

    print(args)


# Generic window signal handlers #
@Signals.register
def destroy(obj):
    obj.destroy()


@Signals.register
def safe_destroy(obj):
    """Check for unsaved changes before destroying."""

    if State.changed:
        trigger_unsaved_warning(lambda: destroy(obj))
    else:
        destroy(obj)


@Signals.register
def hide_on_delete(obj):
    obj.hide_on_delete()


@Signals.register
def show(obj):
    obj.show_all()


@Signals.register
def hide(obj):
    obj.hide()


# Image and metadata handling and navigation #
@Signals.register
def setup_view(chooser, filtering_context: Optional[FilterBuilder] = None):
    """Setup the View object and activate buttons and fields."""

    metadata_box_sensitiveness(False)

    # Don't setup a new view until all modifications have been accounted for
    if State.changed:
        trigger_unsaved_warning(lambda: setup_view(chooser, filtering_context))
        metadata_box_sensitiveness(True)
        return

    try:
        State.view = GtkView(Path(chooser.get_filename()), filtering_context)

        # Initialize the UI only if the selected directory has images inside
        if State.view.has_next():
            State.view.load_next()
            refresh_image()
            load_meta()
            State.get_object("PrevButton").set_sensitive(State.view.has_prev())
            State.get_object("NextButton").set_sensitive(State.view.has_next())

            metadata_box_sensitiveness(True)
            State.get_object("FilterEditorButton").set_sensitive(True)
        else:
            State.get_object("ImageSurface").clear()
    except OSError as ose:
        # Show error popup
        notify_error("<b>Error opening " + chooser.get_filename() + "</b>", str(ose))
    except GLib.Error as ge:
        # Invalid data on first image
        notify_error("<b>Error while loading first image</b>", ge.message)
        # Optimistically enable forward-iteration
        State.get_object("NextButton").set_sensitive(True)


@Signals.register
def refresh_image(*args):
    """Reload, resize and refresh the displayed image, taking it from the backing View object."""

    if State.view is not None and State.view.has_image_data():
        panel = State.get_object("ImageSurface")
        img_pix = State.view.get_image_data()
        img_width, img_height = img_pix.get_width(), img_pix.get_height()
        # Get the visible area's size
        view_alloc = State.get_object("ImagePort").get_allocation()
        view_width, view_height = view_alloc.width, view_alloc.height

        # If the visible area is smaller than the image, calculate the scaling factor and set the new image sizes
        # (Thanks to https://stackoverflow.com/a/1106367/13140497 for leading me down the right path)
        if img_width > view_width or img_height > view_height:
            s_fact = min(view_width / img_width, view_height / img_height)
            img_width, img_height = img_width * s_fact, img_height * s_fact

        # Load and resize the image
        panel.set_from_pixbuf(img_pix.scale_simple(img_width, img_height, InterpType.BILINEAR))


@Signals.register
def show_previous_image(*args):
    try:
        if State.changed:
            # Halt in the presence of unsaved changes
            trigger_unsaved_warning(show_previous_image)
            return

        State.view.load_prev()
        refresh_image()
        load_meta()

        State.get_object("PrevButton").set_sensitive(State.view.has_prev())
        State.get_object("NextButton").set_sensitive(State.view.has_next())
    except StopIteration:
        # In case something goes wrong with the iteration, disable further movement in this direction
        State.get_object("PrevButton").set_sensitive(False)
    except GLib.Error as ge:
        # Invalid image data
        notify_error("<b>Error while loading previous image</b>", ge.message)


@Signals.register
def show_next_image(*args):
    try:
        if State.changed:
            # Halt in the presence of unsaved changes
            trigger_unsaved_warning(show_next_image)
            return

        State.view.load_next()
        refresh_image()
        load_meta()

        State.get_object("PrevButton").set_sensitive(State.view.has_prev())
        State.get_object("NextButton").set_sensitive(State.view.has_next())
    except StopIteration:
        # In case something goes wrong with the iteration, disable further movement in this direction
        State.get_object("NextButton").set_sensitive(False)
    except GLib.Error as ge:
        # Invalid image data
        notify_error("<b>Error while loading next image</b>", ge.message)


def load_meta():
    """Display metadata, pre-filling the fields."""

    # Stop entries from setting the 'changed' flag
    State.inhibit_changed = True

    State.get_object("IDLabel").set_label(str(State.view.image_id))
    State.get_object("FileNameLabel").set_label(State.view.filename)
    author = State.view.get_author()
    State.get_object("AuthorField").set_text(author if author is not None else '')
    universe = State.view.get_universe()
    State.get_object("UniverseField").set_text(universe if universe is not None else '')
    characters = State.view.get_characters()
    State.get_object("CharactersField").set_text(characters if characters is not None else '')
    tags = State.view.get_tags()
    State.get_object("TagsField").get_buffer().set_text(tags if tags is not None else '')

    # Re-enable the 'changed' flag
    State.inhibit_changed = False


@Signals.register
def save_meta(*args):
    """Overwrite the image's metadata with the contents of the field."""

    State.view.set_author(State.get_object("AuthorField").get_text())
    State.view.set_universe(State.get_object("UniverseField").get_text())
    State.view.set_characters(State.get_object("CharactersField").get_text())

    tags_buffer = State.get_object("TagsField").get_buffer()
    State.view.set_tags(tags_buffer.get_text(tags_buffer.get_start_iter(), tags_buffer.get_end_iter(), False))

    try:
        State.view.write()
    except OSError as ose:
        notify_error("<b>Error while saving metadata</b>", str(ose))


# Filtering #
@Signals.register
def add_filter(obj):
    """Append an empty filter rule to the focused table."""

    obj.append()


@Signals.register
def del_filter(*args):
    """Delete the selected filter rule from the focused table."""

    selected = State.get_object(args[0].get_name() + "Selection").get_selected()[1]
    if selected is not None:
        args[0].remove(selected)


@Signals.register
def set_filters(*args):
    """Configure a filter builder and setup a filtered view."""

    metadata_box_sensitiveness(False)

    # Configure all filters in one, ugly pass
    filter_builder = FilterBuilder()
    for spec in State.get_object("IdFilters"):
        filter_builder.id_constraint(spec[0], spec[1])
    for spec in State.get_object("FilenameFilters"):
        filter_builder.filename_constraint(spec[0], spec[1])
    for spec in State.get_object("AuthorFilters"):
        filter_builder.author_constraint(spec[0], spec[1])
    for spec in State.get_object("UniverseFilters"):
        filter_builder.universe_constraint(spec[0], spec[1])
    for spec in State.get_object("CharacterFilters"):
        filter_builder.character_constraint(spec[0], spec[1])
    for spec in State.get_object("TagFilters"):
        filter_builder.tag_constraint(spec[0], spec[1])

    filter_builder.characters_as_disjunctive(State.get_object("CharactersDisjunctiveSwitch").get_active())
    filter_builder.tags_as_disjunctive(State.get_object("TagsDisjunctiveSwitch").get_active())

    setup_view(State.get_object("DirectoryOpener"), filter_builder)


@Signals.register
def clear_filters(*args):
    State.get_object("IdFilters").clear()
    State.get_object("FilenameFilters").clear()
    State.get_object("AuthorFilters").clear()
    State.get_object("UniverseFilters").clear()
    State.get_object("CharacterFilters").clear()
    State.get_object("TagFilters").clear()

    State.get_object("CharactersDisjunctiveSwitch").set_active(False)
    State.get_object("TagsDisjunctiveSwitch").set_active(False)


@Signals.register
def filter_edited(*args):
    """Set the new filter matcher on the edited filter rule."""

    store = args[0]
    store.set_value(store.get_iter(args[1]), 0, args[2])


@Signals.register
def filter_neg_toggle(*args):
    """Toggle the excluded flag on the edited filter rule."""

    store = args[0]
    siter = store.get_iter(args[1])
    store.set_value(siter, 1, not store.get_value(siter, 1))


# Error dialog response
@Signals.register
def error_clear(*args):
    args[0].hide()


# "Unsaved changes" dialog response
@Signals.register
def save_changes(*args):
    State.changed = False
    save_meta()
    State.interrupted_action()


@Signals.register
def ignore_changes(*args):
    State.changed = False
    State.interrupted_action()
