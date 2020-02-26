import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk


class Handlers:
    def quit_program(self):
        Gtk.main_quit()


builder = Gtk.Builder()
builder.add_from_file("HImaKura.glade")
builder.connect_signals(Handlers)

main_window = builder.get_object("MainWindow")
main_window.show_all()

Gtk.main()
