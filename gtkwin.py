#!/usr/bin/env python
# -*- coding: utf-8 -*-

import warnings
warnings.filterwarnings('error', module='gtk')
try:
    import pygtk
    pygtk.require('2.0')
    import gtk
except:
    raise Warning
warnings.resetwarnings()

import gobject
gobject.threads_init()

class InputW(gtk.Window): #{{{
    def __init__(self, console):
        try:
            gtk.Window.__init__(self)
        except gtk.GtkWarning:
            raise Warning
        self.set_title("Botounet")
        #self.set_modal(True)
        #self.resize(800, 55)
        self.set_size_request(800, 45)
        icon_file = 'tongue.png'
        self.set_icon_from_file(icon_file)
        self.set_resizable(False)
        self.connect("destroy", lambda *w: gtk.main_quit())

        hbox = gtk.HBox()
        hbox.set_border_width(8)
        self.add(hbox)
        hbox.show()

        entry = gtk.Entry()
        entry.connect('activate', self.enter_callback, entry)
        entry.connect('key-press-event', self.key_press_event_callback, entry)
        hbox.pack_start(entry, True, True)
        entry.show()

        button = gtk.Button('Send')
        button.connect('clicked', self.enter_callback, entry)
        hbox.pack_start(button, False, True)
        button.show()

        mini = gtk.Button('Iconify')
        mini.connect('clicked', self.toggle)
        hbox.pack_start(mini, False, True)
        mini.show()

        quit_item = gtk.MenuItem("Quitter")
        quit_item.connect("activate", self.quit)
        quit_item.show()
        sample_item = gtk.MenuItem("Sample 1")
        sample_item.show()
        sample_item_2 = gtk.MenuItem("Sample 2")
        sample_item_2.show()
        tray_popup = gtk.Menu()
        tray_popup.attach(quit_item, 0, 1, 0, 1)
        tray_popup.attach(sample_item, 0, 1, 1, 2)
        tray_popup.attach(sample_item_2, 0, 1, 2, 3)

        self.trayicon = gtk.status_icon_new_from_file(icon_file)
        self.trayicon.connect("activate", self.toggle)
        self.trayicon.set_tooltip('Botounet')
        self.trayicon.connect("popup-menu", self.trayicon_popup_callback,
                tray_popup)

        self.hidden = True

        self.history = [""]
        self.n_history = 0
        self.console = console

    def enter_callback(self, widget, entry):
        """ When enter is pressed """
        text = entry.get_text()
        if not self.console:
            print text
            return
        self.n_history = 0
        self.history[0] = text
        self.history.insert(0, "")
        entry.set_text("")
        result = self.console.onecmd(self.console.precmd(text))
        if result == -1:
            gtk.main_quit()

    def key_press_event_callback(self, widget, event, entry):
        """ When a key is pressed"""
        if not self.console: return
        key = gtk.gdk.keyval_name(event.keyval)
        # L'index 0 de l'historique correspond au texte en cours.
        self.history[self.n_history] = entry.get_text()
        move = False
        if key == "Up":
            if self.n_history < len(self.history)-1:
                self.n_history += 1
                move = True
        elif key == "Down":
            if self.n_history > 0:
                self.n_history -= 1
                move = True
        try:
            entry.set_text(self.history[self.n_history])
        except:
            # Si on appuie sur 'Ctrl' par exemple, ça foire.
            # Wtf gtk ?
            pass
        if move:
            entry.set_position(len(entry.get_text()))

    def mainloop(self):
        try:
            gtk.main()
        except KeyboardInterrupt:
            pass

    def toggle(self, widget):
        if self.hidden:
            self.show_all()
            self.hidden = False
        else:
            self.hidden = True
            self.hide_all()

    def trayicon_popup_callback(self, widget, button, act_time, menu):
        menu.popup(None, None, None, button, act_time)

    def quit(self, widget=None):
        if self.console:
            self.console.do_exit(None)
        gtk.main_quit()
#}}}

def main():
    w = InputW(None)
    w.mainloop()

if __name__ == "__main__": main()
