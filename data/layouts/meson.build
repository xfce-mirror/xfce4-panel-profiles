layouts = {
  'cupertino': 'Cupertino.tar.bz2',
  'gnome2': 'GNOME 2.tar.bz2',
  'openSUSE-Leap-15.x': 'openSUSE Leap 15.x.tar.bz2',
  'redmond': 'Redmond.tar.bz2',
  'redmond7': 'Redmond 7.tar.bz2',
  'unity': 'Unity.tar.bz2',
  'xfce-4.12': 'Xfce 4.12.tar.bz2',
  'xfce-4.14': 'Xfce 4.14.tar.bz2',
  'xfce-4.16': 'Xfce 4.16.tar.bz2',
  'xubuntu-12.04': 'Xubuntu 12.04 (Precise).tar.bz2',
  'xubuntu-14.04': 'Xubuntu 14.04 (Trusty).tar.bz2',
  'xubuntu-18.04': 'Xubuntu 18.04 (Bionic).tar.bz2',
}

foreach layout, tarball : layouts
  layoutdir = meson.project_source_root() / 'data' / 'layouts' / layout

  command = [tar, '-cvjf', '@OUTPUT@', '-C', layoutdir]
  command += run_command(ls, '-1', layoutdir, check: true).stdout().strip().split('\n')

  if have_tar_sort
    command += [
      '--sort=name', '--format', 'ustar',
      '--owner=0', '--group=0', '--numeric-owner',
      '--mode=u=wrX,og=',
    ]
  endif

  custom_target(
    layout,
    output: tarball,
    command: command,
    install: true,
    install_dir: pkgdatadir / 'layouts',
  )
endforeach
