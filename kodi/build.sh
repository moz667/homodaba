mkdir -p build

rsync -va plugin.homodaba.movies/ build/plugin.homodaba.movies/

cd build

if [ -f plugin.homodaba.movies.zip ]; then
	rm plugin.homodaba.movies.zip
fi

if [-e settings.xml]; then
	cp settings.xml plugin.homodaba.movies/resources/
fi

zip -r plugin.homodaba.movies.zip plugin.homodaba.movies/
