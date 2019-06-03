VERSION = 2.3

release:
	mkdir ./droidlysis-$(VERSION)
	cp *.py README.md ./droidlysis-$(VERSION)
	tar cvfz droidlysis-$(VERSION).tar.gz ./droidlysis-$(VERSION)

clean:
	rm -rf ./droidlysis-?.*
	rm -f *~ properties *.csv *.pyc

