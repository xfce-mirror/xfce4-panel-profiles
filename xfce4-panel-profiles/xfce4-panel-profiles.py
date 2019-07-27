#!/usr/bin/env python3
# -*- Mode: Python; coding: utf-8; indent-tabs-mode: nil; tab-width: 4 -*-
#   Panel Profiles
#   Copyright (C) 2013 Alistair Buxton <a.j.buxton@gmail.com>
#   Copyright (C) 2015 Sean Davis <smd.seandavis@gmail.com>
#
#   This program is free software: you can redistribute it and/or modify it
#   under the terms of the GNU General Public License version 3 or newer,
#   as published by the Free Software Foundation.
#
#   This program is distributed in the hope that it will be useful, but
#   WITHOUT ANY WARRANTY; without even the implied warranties of
#   MERCHANTABILITY, SATISFACTORY QUALITY, or FITNESS FOR A PARTICULAR
#   PURPOSE.  See the GNU General Public License for more details.
#
#   You should have received a copy of the GNU General Public License along
#   with this program.  If not, see <http://www.gnu.org/licenses/>.

import gettext
gettext.textdomain('xfce4-panel-profiles')

from gettext import gettext as _
from gettext import ngettext

import shlex
import os
import datetime

import gi
gi.require_version('Gtk', '3.0')

from gi.repository import Gtk, GLib, Gio

from panelconfig import PanelConfig

homedir = GLib.get_home_dir()
cachedir = GLib.get_user_cache_dir()
cachefile = os.path.join(cachedir, "xfce4-panel-profiles.tar.gz")

try:
    if not os.path.exists(cachedir):
        os.makedirs(cachedir)
except:
    pass

class XfcePanelProfiles:

    '''XfcePanelProfiles application class.'''

    data_dir = "xfce4-panel-profiles"
    save_location = os.path.join(GLib.get_user_data_dir(), data_dir)

    def __init__(self):
        '''Initialize the Panel Profiles application.'''
        self.builder = Gtk.Builder()
        self.builder.set_translation_domain('xfce4-panel-profiles')

        script_dir = os.path.dirname(os.path.abspath(__file__))
        glade_file = os.path.join(script_dir, "xfce4-panel-profiles.glade")
        self.builder.add_from_file(glade_file)
        self.builder.connect_signals(self)

        self.window = self.builder.get_object("xfpanel_switch_window")
        self.window.set_title(_("Panel Profiles"))
        self.fix_xfce_header()

        self.load_xfconf()

        modified_col = self.builder.get_object('modified_column')
        cell = Gtk.CellRendererText()
        modified_col.pack_start(cell, False)
        modified_col.set_cell_data_func(cell, self.cell_data_func_modified, 2)

        self.treeview = self.builder.get_object('saved_configurations')
        self.tree_model = self.treeview.get_model()
        for config in self.get_saved_configurations():
            self.tree_model.append(config)

        # Sort by name, then sort by date so timestamp sort is alphabetical
        self.tree_model.set_sort_column_id(1, Gtk.SortType.ASCENDING)
        self.tree_model.set_sort_column_id(2, Gtk.SortType.DESCENDING)

        if not os.path.exists(self.save_location):
            os.makedirs(self.save_location)

        self.window.show()

    def _copy(self, src, dst):
        PanelConfig.from_file(src).to_file(dst)

    def _filedlg(self, title, action, default=None):
        if action == Gtk.FileChooserAction.SAVE:
            button = _("Save")
        else:
            button = _("Open")
        dialog = Gtk.FileChooserDialog(title=title,
                                       transient_for=self.window,
                                       action=action)
        dialog.add_buttons(
            _("Cancel"), Gtk.ResponseType.CANCEL,
            button, Gtk.ResponseType.ACCEPT
        )
        dialog.set_default_response(Gtk.ResponseType.ACCEPT)
        if default:
            dialog.set_current_name(default)
        return dialog

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
                path = os.path.join(path, "layouts")
                if os.path.isdir(path):
                    dirs.append(path)
        path = os.path.join(GLib.get_user_data_dir(), self.data_dir)
        if os.path.isdir(path):
            dirs.append(path)
        return list(set(dirs))

    def get_saved_configurations(self):
        results = []
        now = int(datetime.datetime.now().strftime('%s'))
        if (os.path.isfile(cachefile)):
            results.append((cachefile, _("Current Configuration"), now))
        else:
            results.append(("", _("Current Configuration"), now))

        for directory in self.get_data_dirs():
            for filename in os.listdir(directory):
                name, ext = os.path.splitext(filename)
                name = os.path.splitext(name)[0]
                if ext in [".gz", ".bz2"]:
                    path = os.path.join(directory, filename)
                    t = int(os.path.getmtime(path))
                    results.append((path, name, int(t)))

        return results

    def cell_data_func_modified(self, column, cell_renderer,
                                tree_model, tree_iter, id):
        today_delta = datetime.datetime.today() - datetime.timedelta(days=1)
        t = tree_model.get_value(tree_iter, id)
        datetime_o = datetime.datetime.fromtimestamp(t)
        if datetime_o > today_delta:
            modified = _("Today")
        elif datetime_o == today_delta:
            modified = _("Yesterday")
        else:
            modified = datetime_o.strftime("%x")
        cell_renderer.set_property('text', modified)
        return

    def get_selected(self):
        model, treeiter = self.treeview.get_selection().get_selected()
        values = model[treeiter][:]
        return (model, treeiter, values)

    def get_selected_filename(self):
        values = self.get_selected()[2]
        filename = values[0]
        return filename

    def copy_configuration(self, row, new_name, append=True):
        values = row[2]
        filename = values[0]
        old_name = values[1]
        created = values[2]
        new_filename = new_name + ".tar.bz2"
        new_filename = os.path.join(self.save_location, new_filename)
        self._copy(filename, new_filename)
        if append:
            name = _("%s (Copy of %s)") % (new_name, old_name)
            self.tree_model.append([new_filename, name, created])

    def save_configuration(self, name, append=True):
        filename = name + ".tar.bz2"
        filename = os.path.join(self.save_location, filename)
        PanelConfig.from_xfconf(self.xfconf).to_file(filename)
        created = int(datetime.datetime.now().strftime('%s'))
        if append:
            self.tree_model.append([filename, name, created])

    def on_save_clicked(self, widget):
        filename = self.get_selected_filename()
        dialog = PanelSaveDialog(self.window)
        if dialog.run() == Gtk.ResponseType.ACCEPT:
            name = dialog.get_save_name()
            if len(name) > 0:
                if filename == "":
                    self.save_configuration(name)
                else:
                    self.copy_configuration(self.get_selected(), name)
        dialog.destroy()

    def on_export_clicked(self, widget):
        dialog = self._filedlg(_("Export configuration as..."),
                               Gtk.FileChooserAction.SAVE, _("Untitled"))
        response = dialog.run()
        if response == Gtk.ResponseType.ACCEPT:
            selected = self.get_selected_filename()
            filename = dialog.get_filename()
            if selected == "":
                self.save_configuration(filename, False)
            else:
                self.copy_configuration(self.get_selected(), filename, False)
        dialog.destroy()

    def on_import_clicked(self, widget):
        dialog = self._filedlg(_("Import configuration file..."),
                               Gtk.FileChooserAction.OPEN)
        response = dialog.run()
        if response == Gtk.ResponseType.ACCEPT:
            filename = dialog.get_filename()
            savedlg = PanelSaveDialog(self.window)
            if savedlg.run() == Gtk.ResponseType.ACCEPT:
                name = savedlg.get_save_name()
                dst = os.path.join(self.save_location, name + ".tar.bz2")
                self._copy(filename, dst)
                self.tree_model.append(
                    [dst, name, int(datetime.datetime.now().strftime('%s'))])
            savedlg.destroy()
        dialog.destroy()

    def load_configuration(self, filename):
        if os.path.isfile(filename):
            PanelConfig.from_file(filename).to_xfconf(self.xfconf)

    def on_apply_clicked(self, widget):
        filename = self.get_selected_filename()
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

    def on_saved_configurations_cursor_changed(self, widget):
        filename = self.get_selected_filename()
        delete = self.builder.get_object("toolbar_delete")
        if os.access(filename, os.W_OK):
            delete.set_sensitive(True)
        else:
            delete.set_sensitive(False)

    def on_window_destroy(self, *args):
        '''Exit the application when the window is closed.'''
        Gtk.main_quit()

    def on_close_clicked(self, *args):
        '''Exit the application when the window is closed.'''
        Gtk.main_quit()

    def on_help_clicked(self, *args):
        '''Navigate to the application documentation on Help click.'''
        screen = self.window.get_screen()
        link = "https://docs.xfce.org/apps/xfce4-panel-profiles/start"
        Gtk.show_uri(screen, link, Gtk.get_current_event_time())


class PanelSaveDialog(Gtk.MessageDialog):

    def __init__(self, parent=None, default=None):
        primary = _("Name the new panel configuration")
        Gtk.MessageDialog.__init__(
            self, transient_for=parent, modal=True,
            message_type=Gtk.MessageType.QUESTION,
            text=primary)
        self.add_buttons(
            _("Cancel"), Gtk.ResponseType.CANCEL,
            _("Save Configuration"), Gtk.ResponseType.ACCEPT
        )
        self.set_default_icon_name("document-save-as")
        self.set_default_response(Gtk.ResponseType.ACCEPT)
        box = self.get_message_area()
        self.entry = Gtk.Entry.new()
        self.entry.set_activates_default(True)
        if default:
            self.entry.set_text(default)
        else:
            self.default()
        box.pack_start(self.entry, True, True, 0)
        box.show_all()

    def default(self):
        date = datetime.datetime.now().strftime("%x %X")
        date = date.replace(":", "-").replace("/", "-").replace(" ", "_")
        name = _("Backup_%s") % date
        self.set_save_name(name)

    def get_save_name(self):
        return self.entry.get_text().strip()

    def set_save_name(self, name):
        self.entry.set_text(name.strip())

if __name__ == "__main__":
    import sys

    session_bus = Gio.BusType.SESSION
    cancellable = None
    connection = Gio.bus_get_sync(session_bus, cancellable)

    proxy_property = 0
    interface_properties_array = None
    destination = 'org.xfce.Xfconf'
    path = '/org/xfce/Xfconf'
    interface = destination

    xfconf = Gio.DBusProxy.new_sync(
        connection,
        proxy_property,
        interface_properties_array,
        destination,
        path,
        interface,
        cancellable)

    if len(sys.argv) > 1:
        if sys.argv[1] in ['save', 'load']:
            try:
                if sys.argv[1] == 'save':
                    PanelConfig.from_xfconf(xfconf).to_file(sys.argv[2])
                elif sys.argv[1] == 'load':
                    PanelConfig.from_file(sys.argv[2]).to_xfconf(xfconf)
            except Exception as e:
                print(repr(e))
                exit(1)
            exit(0)
        else:
            print('Xfce Panel Profiles - Usage:')
            print(sys.argv[0] + ' : load graphical user interface.')
            print(sys.argv[0] + ' save <filename> : save current configuration.')
            print(sys.argv[0] + ' load <filename> : load configuration from file.')
            print('')
            exit(-1)

    try:
        PanelConfig.from_xfconf(xfconf).to_file(cachefile)
    except:
        pass

    main = XfcePanelProfiles()
    Gtk.main()
