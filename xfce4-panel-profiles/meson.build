info_py_in = configure_file(
  input: 'info.py.in.in',
  output: 'info.py.in',
  configuration: {
    'appname': meson.project_name(),
    'version': meson.project_version(),
    'copyright_year': copyright_year,
    'revision': '@REVISION@',
  },
  install: false,
)

# {'install arg in vcs_tag', 'install_dir arg in vcs_tag'} is only supported in 1.7.0+.
if meson.version().version_compare('>= 1.7.0')
  vcs_tag(
    command: ['git', 'rev-parse', '--short', 'HEAD'],
    fallback: 'UNKNOWN',
    input: info_py_in,
    output: 'info.py',
    replace_string: '@REVISION@',
    install: true,
    install_dir: pkgdatadir / 'xfce4-panel-profiles',
  )
else
  configure_file(
    input: info_py_in,
    output: 'info.py',
    configuration: {'REVISION': 'UNKNOWN'},
    install: true,
    install_dir: pkgdatadir / 'xfce4-panel-profiles',
  )
endif

xfce4_panel_profiles_sources = [
  'panelconfig.py',
  'xfce4-panel-profiles.glade',
  'xfce4-panel-profiles.py',
]

install_data(
  xfce4_panel_profiles_sources,
  install_dir: pkgdatadir / 'xfce4-panel-profiles',
)
