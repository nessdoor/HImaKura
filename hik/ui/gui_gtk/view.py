from typing import Optional

from gi.repository.GdkPixbuf import Pixbuf

from ui.view import View


class GtkView(View):
    """Specialization of the View class that provides image data as Pixbuf objects."""

    _current_image: Pixbuf

    def load_prev(self) -> None:
        super().load_prev()
        self._current_image = Pixbuf.new_from_file(str(self._image_path))

    def load_next(self) -> None:
        super().load_next()
        self._current_image = Pixbuf.new_from_file(str(self._image_path))

    def has_image_data(self) -> bool:
        return hasattr(self, '_current_image')

    def get_image_data(self) -> Optional[Pixbuf]:
        """
        Return the current image as a pixbuf copy.

        :return: a pixbuf containing the image, or None if no image has been loaded
        """

        if self.has_image_data():
            return self._current_image.copy()
        else:
            return None