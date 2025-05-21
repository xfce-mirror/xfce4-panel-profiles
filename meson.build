project('xfce4-panel-profiles', version : '1.1.0', license : 'GPL-3.0-or-later', meson_version : '>= 0.56.0')

pkgdatadir = get_option('prefix') / get_option('datadir') / meson.project_name()
copyright_year = '2025'

pkgconfig = import('pkgconfig')
python = import('python')
i18n = import('i18n')

python3_required_modules = ['gi', 'psutil']

python3 = python.find_installation(
  'python3',
  modules: python3_required_modules,
)

dependency_versions = {
  'glib': '>= 2.50.0',
  'gtk': '>= 3.22.0',
  'xfce4': '>= 4.16.0',
}

# Declare runtime dependency versions here to make packaging more obvious
dependency('glib-2.0', version: dependency_versions['glib'])
dependency('gtk+-3.0', version: dependency_versions['gtk'])
dependency('libxfce4ui-2', version: dependency_versions['xfce4'])
dependency('libxfce4util-1.0', version: dependency_versions['xfce4'])

ls = find_program('ls')
tar = find_program('tar')
have_tar_sort = run_command(tar, '--help', check: false).stdout().contains('sort=')

i18n.merge_file(
  input: 'org.xfce.PanelProfiles.desktop.in',
  output: 'org.xfce.PanelProfiles.desktop',
  po_dir: 'po',
  type: 'desktop',
  install: true,
  install_dir: get_option('prefix') / get_option('datadir') / 'applications',
)

doc_files = [
  'AUTHORS',
  'COPYING',
  'INSTALL',
  'NEWS',
  'README.md',
]

install_data(
  doc_files,
  install_dir: get_option('prefix') / get_option('datadir') / 'doc' / meson.project_name(),
)

install_man('xfce4-panel-profiles.1')

subdir('bin')
subdir('data')
subdir('xfce4-panel-profiles')
subdir('po')
