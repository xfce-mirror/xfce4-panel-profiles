#!/usr/bin/env python3
# * Configuration switcher for xfce4-panel
# *
# * Copyright 2013 Alistair Buxton <a.j.buxton@gmail.com>
# *
# * License: This program is free software; you can redistribute it and/or
# * modify it under the terms of the GNU General Public License as published
# * by the Free Software Foundation; either version 3 of the License, or (at
# * your option) any later version. This program is distributed in the hope
# * that it will be useful, but WITHOUT ANY WARRANTY; without even the implied
# * warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# * GNU General Public License for more details.

from gi.repository import Gio, GLib
import tarfile
import io
import time
import os
import psutil

# yes, python 3.2 has exist_ok, but it will still fail if the mode is different

config_dir = os.path.join(GLib.get_user_config_dir(), 'xfce4/panel/')

def mkdir_p(path):
    try:
        os.makedirs(path, exist_ok=True)
    except FileExistsError:
        pass


def add_to_tar(t, bytes, arcname):
    ti = tarfile.TarInfo(name=arcname)
    ti.size = len(bytes)
    ti.mtime = time.time()
    f = io.BytesIO(bytes)
    t.addfile(ti, fileobj=f)


class PanelConfig(object):

    def __init__(self):
        self.desktops = []
        self.properties = {}
        self.rc_files = []
        self.source = None
        self.errors = []

    @classmethod
    def from_xfconf(cls, xfconf):
        pc = PanelConfig()

        result = xfconf.call_sync(
            'GetAllProperties',
            GLib.Variant('(ss)', ('xfce4-panel', '')), 0, -1, None)

        props = result.get_child_value(0)

        for n in range(props.n_children()):
            p = props.get_child_value(n)
            pp = p.get_child_value(0).get_string()
            pv = p.get_child_value(1).get_variant()

            pn = GLib.Variant.parse(None, str(pv), None, None)
            assert(pv == pn)

            pc.properties[pp] = pv

        pc.remove_orphans()
        pc.find_desktops()
        pc.find_rc_files()

        return pc

    @classmethod
    def from_file(cls, filename):
        pc = PanelConfig()

        pc.source = tarfile.open(filename, mode='r')
        config = pc.source.extractfile('config.txt')

        for line in config:
            try:
                x = line.decode('utf-8').strip().split(' ', 1)
                pc.properties[x[0]] = GLib.Variant.parse(None, x[1], None, None)
            except:
                pass

        pc.remove_orphans()
        pc.find_desktops()
        pc.find_rc_files()

        return pc

    def source_not_file(self):
        return getattr(self, 'source', None) is None

    def remove_orphans(self):
        plugin_ids = set()
        rem_keys = []

        for pp, pv in self.properties.items():
            path = pp.split('/')
            if len(path) == 4 and path[0] == '' and path[1] == 'panels' and \
                    path[2].startswith('panel-') and path[3] == 'plugin-ids':
                plugin_ids.update(pv)

        for pp, pv in self.properties.items():
            path = pp.split('/')
            if len(path) == 3 and path[0] == '' and path[1] == 'plugins' and \
                    path[2].startswith('plugin-'):
                number = path[2].split('-')[1]
                try:
                    if int(number) not in plugin_ids:
                        rem_keys.append('/plugins/plugin-' + number)
                except ValueError:
                    pass

        self.remove_keys(rem_keys)

    def check_desktop(self, path):
        try:
            f = self.get_desktop_source_file(path)
            bytes = f.read()
            f.close()
        except (KeyError, FileNotFoundError):
            return False

        # Check if binary exists
        keyfile = GLib.KeyFile.new()
        try:
            if keyfile.load_from_data(bytes.decode(), len(bytes), GLib.KeyFileFlags.NONE):
                exec_str = keyfile.get_string("Desktop Entry", "Exec")
                if self.check_exec(exec_str):
                    return True
        except GLib.Error:  # pylint: disable=E0712
            self.errors.append('Error parsing desktop file ' + path)
            pass #  https://bugzilla.xfce.org/show_bug.cgi?id=14597

        return False

    def find_desktops(self):
        rem_keys = []

        for pp, pv in self.properties.items():
            path = pp.split('/')
            if len(path) == 3 and path[0] == '' and path[1] == 'plugins' and \
                    path[2].startswith('plugin-'):
                number = path[2].split('-')[1]
                if pv.get_type_string() == 's' and \
                        pv.get_string() == 'launcher':
                    prop_path = '/plugins/plugin-' + number + '/items'
                    if prop_path not in self.properties:
                        rem_keys.append('/plugins/plugin-' + number)
                        continue
                    for d in self.properties[prop_path].unpack():
                        desktop_path = 'launcher-' + number + '/' + d
                        if self.check_desktop(desktop_path):
                            self.desktops.append(desktop_path)
                        else:
                            rem_keys.append('/plugins/plugin-' + number)

        self.remove_keys(rem_keys)

    def find_rc_files(self):
        if self.source_not_file():
            plugin_ids = []
            filenames = []

            for pp in self.properties:
                path = pp.split('/')
                if len(path) == 4 and path[0] == '' and path[1] == 'panels' and path[3] == 'plugin-ids':
                    plugin_ids.extend(self.properties[pp])

            if len(plugin_ids) == 0:
                return

            for plugin_id in plugin_ids:
                plugin_id = str(plugin_id)
                prop_path = '/plugins/plugin-' + plugin_id
                try:
                    prop = self.properties[prop_path].get_string()
                except:
                    continue

                if prop == 'launcher':
                    continue

                filename = prop + '-' + plugin_id + '.rc'
                path = os.path.join(config_dir, filename)
                if os.path.exists(path):
                    filenames.append(filename)
            self.rc_files = filenames
        else:
            filenames = self.source.getnames()
            for filename in filenames:
                if filename.find('.rc') > -1:
                    self.rc_files.append(filename)

    def remove_keys(self, rem_keys):
        keys = list(self.properties.keys())
        for param in keys:
            for bad_plugin in rem_keys:
                if param == bad_plugin or param.startswith(bad_plugin+'/'):
                    try:
                        del self.properties[param]
                    except KeyError:
                        pass #  https://bugzilla.xfce.org/show_bug.cgi?id=14934

    def get_desktop_source_file(self, desktop):
        if self.source_not_file():
            path = os.path.join(config_dir, desktop)
            return open(path, 'rb')
        else:
            return self.source.extractfile(desktop)

    def get_rc_source_file(self, rc):
        if self.source_not_file():
            path = os.path.join(config_dir, rc)
            return open(path, 'rb')
        else:
            return self.source.extractfile(rc)

    def to_file(self, filename):
        if filename.endswith('.gz'):
            mode = 'w:gz'
        elif filename.endswith('.bz2'):
            mode = 'w:bz2'
        else:
            mode = 'w'
        t = tarfile.open(name=filename, mode=mode)
        props_tmp = []
        for (pp, pv) in sorted(self.properties.items()):
            props_tmp.append(str(pp) + ' ' + str(pv))
        add_to_tar(t, '\n'.join(props_tmp).encode('utf8'), 'config.txt')

        for d in self.desktops:
            bytes = self.get_desktop_source_file(d).read()
            add_to_tar(t, bytes, d)

        for rc in self.rc_files:
            bytes = self.get_rc_source_file(rc).read()
            add_to_tar(t, bytes, rc)

        t.close()

    def check_exec(self, program):
        program = program.strip()
        if len(program) == 0:
            return False

        params = list(GLib.shell_parse_argv(program)[1])
        executable = params[0]

        if os.path.exists(executable):
            return True

        path = GLib.find_program_in_path(executable)
        if path is not None:
            return True

        return False

    def to_xfconf(self, xfconf):
        session_bus = Gio.BusType.SESSION
        conn = Gio.bus_get_sync(session_bus, None)

        destination = 'org.xfce.Panel'
        path = '/org/xfce/Panel'
        interface = destination

        dbus_proxy = Gio.DBusProxy.new_sync(conn, 0, None, destination, path, interface, None)

        if dbus_proxy is not None:
            # Reset all properties to make sure old settings are invalidated
            try:
                xfconf.call_sync('ResetProperty', GLib.Variant(
                    '(ssb)', ('xfce4-panel', '/', True)), 0, -1, None)
            except GLib.Error:  # pylint: disable=E0712
                pass

            for (pp, pv) in sorted(self.properties.items()):
                xfconf.call_sync('SetProperty', GLib.Variant(
                    '(ssv)', ('xfce4-panel', pp, pv)), 0, -1, None)

            for d in self.desktops:
                bytes = self.get_desktop_source_file(d).read()
                mkdir_p(config_dir + os.path.dirname(d))
                f = open(config_dir + d, 'wb')
                f.write(bytes)
                f.close()

            for rc in self.rc_files:
                bytes = self.get_rc_source_file(rc).read()
                f = open(os.path.join(config_dir, rc), 'wb')
                f.write(bytes)
                f.close()

                # Kill the plugin so that it reloads the config we just wrote and does
                # not overwrite it with its current cache when the panel restarts below.
                # Some plugins don't save their config when restarting the panel
                # (e.g. whiskermenu) but others do (e.g. netload)
                plugin_id = rc.replace('.', '-').split('-')[1]
                proc_name_prefix = 'panel-' + plugin_id + '-'
                for proc in psutil.process_iter():
                    if proc.name().startswith(proc_name_prefix):
                        proc.kill()

            try:
                dbus_proxy.call_sync('Terminate', GLib.Variant('(b)', ('xfce4-panel',)), 0, -1, None)
            except GLib.GError:  # pylint: disable=E0712
                pass

    def has_errors(self):
        return len(self.errors) > 0
