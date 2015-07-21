#!/usr/bin/python
# -*- Mode: Python; coding: utf-8; indent-tabs-mode: nil; tab-width: 4 -*-
#
#   This program is free software: you can redistribute it and/or modify it
#   under the terms of the GNU General Public License version 3, as published
#   by the Free Software Foundation.
#
#   This program is distributed in the hope that it will be useful, but
#   WITHOUT ANY WARRANTY; without even the implied warranties of
#   MERCHANTABILITY, SATISFACTORY QUALITY, or FITNESS FOR A PARTICULAR
#   PURPOSE.  See the GNU General Public License for more details.
#
#   You should have received a copy of the GNU General Public License along
#   with this program.  If not, see <http://www.gnu.org/licenses/>.

import gettext
gettext.textdomain('xfpanel-switch')

from gettext import gettext as _
from gettext import ngettext

import shlex
import shutil
import os
import datetime
from gi.repository import Gtk, GLib, Gio

from panelconfig import PanelConfig


class XfpanelSwitch:
    '''XfpanelSwitch application class.'''

    data_dir = "xfpanel-switch"
    save_location = os.path.join(GLib.get_user_data_dir(), data_dir)

    def __init__(self):
        '''Initialize the Xfce Panel Switch application.'''
        self.builder = Gtk.Builder()
        self.builder.set_translation_domain ('xfpanel-switch')

        script_dir = os.path.dirname(os.path.abspath(__file__))
        glade_file = os.path.join(script_dir, "xfpanel-switch.glade")
        self.builder.add_from_file(glade_file)
        self.builder.connect_signals(self)

        self.window = self.builder.get_object("xfpanel_switch_window")
        self.window.set_title(_("Xfce Panel Switch"))
        self.fix_xfce_header()

        self.load_xfconf()

        self.treeview = self.builder.get_object('saved_configurations')
        self.tree_model = self.treeview.get_model()
        for config in self.get_saved_configurations():
            self.tree_model.append(config)
        
        if not os.path.exists(self.save_location):
            os.makedirs(self.save_location)

        self.window.show()

    def load_xfconf(self):
        session_bus = Gio.BusType.SESSION
        cancellable = None
        connection = Gio.bus_get_sync(session_bus, cancellable)

        proxy_property = 0
        interface_properties_array = None
        destination = 'org.xfce.Xfconf'
        path = '/org/xfce/Xfconf'
        interface = destination

        self.xfconf = Gio.DBusProxy.new_sync(
             connection,
             proxy_property,
             interface_properties_array,
             destination,
             path,
             interface,
             cancellable)

    def fix_xfce_header(self):
        ''' Set background-color of frame to base-color to make it resemble the
        XfceHeading widget '''
        self.xfce_header = self.builder.get_object("xfce_header")
        entry = Gtk.Entry.new()
        style = entry.get_style_context()
        base_color = style.lookup_color("theme_base_color")
        self.xfce_header.override_background_color(0, base_color[1])
        fg_color = style.lookup_color("theme_fg_color")
        self.xfce_header.override_color(0, fg_color[1])

    def get_data_dirs(self):
        dirs = []
        for directory in GLib.get_system_data_dirs():
            path = os.path.join(directory, self.data_dir)
            if os.path.isdir(path):
                dirs.append(path)
        path = os.path.join(GLib.get_user_data_dir(), self.data_dir)
        if os.path.isdir(path):
            dirs.append(path)
        return dirs

    def get_saved_configurations(self):
        results = []
        results.append(("", "Current Configuration", ""))

        for directory in self.get_data_dirs():
            for filename in os.listdir(directory):
                name, ext = os.path.splitext(filename)
                name, tar = os.path.splitext(name)
                if ext in [".gz", ".bz2"]:
                    path = os.path.join(directory, filename)
                    t = os.path.getmtime(path)
                    datetime_o = datetime.datetime.fromtimestamp(t)
                    modified = datetime_o.strftime("%x")
                    results.append((path, name, modified))

        return results

    def get_selected(self):
        model, treeiter = self.treeview.get_selection().get_selected()
        values = model[treeiter][:]
        return (model, treeiter, values)

    def get_save_dialog(self, default_name=None):
        dialog = self.builder.get_object("save_dialog")
        self.name_entry = self.builder.get_object("name_entry")
        if default_name is None:
            date = datetime.datetime.now().strftime("%x %X")
            date = date.replace(":", "-").replace("/", "-").replace(" ", "_")
            default_name = _("Backup_%s") % date
        self.name_entry.set_text(default_name)

        return dialog

    def copy_configuration(self, row, new_name, append=True):
        model, treeiter, values = row
        filename = values[0]
        old_name = values[1]
        created = values[2]
        new_filename = new_name + ".tar.bz2"
        new_filename = os.path.join(self.save_location, new_filename)
        PanelConfig.from_file(filename).to_file(new_filename)
        if append:
            name = _("%s (Copy of %s)") % (new_name, old_name)
            self.tree_model.append([new_filename, name, created])

    def save_configuration(self, name, append=True):
        filename = name + ".tar.bz2"
        filename = os.path.join(self.save_location, filename)
        PanelConfig.from_xfconf(self.xfconf).to_file(filename)
        created = datetime.datetime.now().strftime("%X")
        if append:
            self.tree_model.append([filename, name, created])

    def on_save_clicked(self, widget):
        model, treeiter, values = self.get_selected()
        filename = values[0]
        dialog = self.get_save_dialog()
        if dialog.run() == Gtk.ResponseType.OK:
            name = self.name_entry.get_text().strip()
            if len(name) > 0:
                if filename == "":
                    self.save_configuration(name)
                else:
                    self.copy_configuration(self.get_selected(), name)
        dialog.hide()
        
    def on_export_clicked(self, widget):
        dialog = Gtk.FileChooserDialog(_("Export configuration as..."),
                                       self.window, Gtk.FileChooserAction.SAVE,
                                       (_("Cancel"), Gtk.ResponseType.CANCEL,
                                        _("Save"), Gtk.ResponseType.ACCEPT))
        dialog.set_current_name(_("Untitled"))
        response = dialog.run()
        if response == Gtk.ResponseType.ACCEPT:
            filename = dialog.get_filename()
            if filename == "":
                self.save_configuration(filename, False)
            else:
                self.copy_configuration(self.get_selected(), filename)
        dialog.hide()
        dialog.destroy()
        
    def on_import_clicked(self, widget):
        dialog = Gtk.FileChooserDialog(_("Import configuration file..."),
                                       self.window, Gtk.FileChooserAction.OPEN,
                                       (_("Cancel"), Gtk.ResponseType.CANCEL,
                                        _("Save"), Gtk.ResponseType.ACCEPT))
        response = dialog.run()
        if response == Gtk.ResponseType.ACCEPT:
            filename = dialog.get_filename()
            savedlg = self.get_save_dialog()
            if savedlg.run() == Gtk.ResponseType.OK:
                name = self.name_entry.get_text().strip()
                dst = os.path.join(self.save_location, name+".tar.bz2")
                shutil.copyfile(filename, dst)
                self.tree_model.append([dst, name, 
                                        datetime.datetime.now().strftime("%X")])
            savedlg.hide()
        dialog.hide()
        dialog.destroy()
        
    def get_selected_filename(self):
        model, treeiter, values = self.get_selected()
        filename = values[0]
        if filename == "":
            return
        return filename

    def load_configuration(self, filename):
        if os.path.isfile(filename):
            PanelConfig.from_file(filename).to_xfconf(self.xfconf)

    def on_apply_clicked(self, widget):
        model, treeiter, values = self.get_selected()
        filename = values[0]
        self.load_configuration(filename)

    def delete_configuration(self, filename):
        if os.path.isfile(filename):
            os.remove(filename)

    def on_delete_clicked(self, widget):
        model, treeiter, values = self.get_selected()
        filename = values[0]
        if filename == "":
            return
        self.delete_configuration(filename)
        model.remove(treeiter)

    def on_window_destroy(self, *args):
        '''Exit the application when the window is closed.'''
        Gtk.main_quit()

    def on_close_clicked(self, *args):
        '''Exit the application when the window is closed.'''
        Gtk.main_quit()

if __name__ == "__main__":
    main = XfpanelSwitch()
    Gtk.main()
