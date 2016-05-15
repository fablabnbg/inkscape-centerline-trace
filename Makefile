# a simple makefile to release packages

DEST=/usr/share/inkscape/extensions
DISTNAME=inkscape-centerline-trace

dist:
	cd distribute; sh ./distribute.sh

#install is used by dist.
install:
	mkdir -p $(DEST)
	install -m 755 -t $(DEST) *.py
	install -m 644 -t $(DEST) *.inx

clean:
	rm -f *.orig */*.orig
	rm -rf distribute/$(DISTNAME)
	rm -rf distribute/deb/files
