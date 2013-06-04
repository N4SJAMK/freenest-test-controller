LIBDIR = $(DESTDIR)/usr/share/pyshared/
BINDIR = $(DESTDIR)/usr/bin/
clean:
	rm -f *.py[co] */*.py[co]
install:
	mkdir -p $(BINDIR)
	mkdir -p $(LIBDIR)
	cp fntsd $(BINDIR)
	cp -r fnts $(LIBDIR)
	cp fnts/fnts.conf $(DESTDIR)/etc/fnts.conf
uninstall:
	rm -f $(BINDIR)/fntsd
	rm -rf $(LIBDIR)/fnts
