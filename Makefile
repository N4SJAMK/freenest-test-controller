LIBDIR = $(DESTDIR)/usr/share/pyshared/
BINDIR = $(DESTDIR)/usr/bin/
clean:
	rm -f *.py[co] */*.py[co]
install:
	mkdir -p $(BINDIR)
	mkdir -p $(LIBDIR)
	cp fntcd.py $(BINDIR)
	cp -r fntc $(LIBDIR)
uninstall:
	rm -f $(BINDIR)/fntcd.py
	rm -rf $(LIBDIR)/fntc
