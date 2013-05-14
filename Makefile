LIBDIR = $(DESTDIR)/usr/share/pyshared/
BINDIR = $(DESTDIR)/usr/bin/
clean:
	rm -f *.py[co] */*.py[co]
install:
	mkdir -p $(BINDIR)
	mkdir -p $(LIBDIR)
	cp fntcd $(BINDIR)
	cp -r fntc $(LIBDIR)
	cp fntc/fntc.conf $(DESTDIR)/etc/fntc.conf
uninstall:
	rm -f $(BINDIR)/fntcd
	rm -rf $(LIBDIR)/fntc
