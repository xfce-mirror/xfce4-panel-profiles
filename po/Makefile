include Makevars

xfce4-panel-profiles.pot:
	xgettext $(XGETTEXT_OPTIONS) --directory=$(top_builddir) \
		--files-from=./POTFILES.in \
		--copyright-holder='$(COPYRIGHT_HOLDER)' \
		--msgid-bugs-address="$(MSGID_BUGS_ADDRESS)" \
		-o $@
