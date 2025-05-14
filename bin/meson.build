configure_file(
  input: 'xfce4-panel-profiles.in',
  output: 'xfce4-panel-profiles',
  configuration: {
    'python': python3.full_path(),
    'pkgdatadir': pkgdatadir,
  },
  install: true,
  install_dir: get_option('prefix') / get_option('bindir'),
  install_mode: 'rwxr-xr-x',
)
