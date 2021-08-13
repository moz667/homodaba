build_addon_zip() {
	ADDON_NAME=$1
	KODI_VERSION=$2
	OUTPUT_ZIP_FILE="$ADDON_NAME-$KODI_VERSION.zip"

	echo " * Construyendo $ADDON_NAME ($KODI_VERSION) en $OUTPUT_ZIP_FILE"

	if [ -f $OUTPUT_ZIP_FILE ]; then
		rm $OUTPUT_ZIP_FILE
	fi

	zip -qr $OUTPUT_ZIP_FILE $ADDON_NAME/
}

mkdir -p build

rsync -qa --del plugin.homodaba.movies/ build/plugin.homodaba.movies/

ADDON_DESC_FILE=plugin.homodaba.movies/addon.xml

cd build

if [ -e settings.xml ]; then
	cp settings.xml plugin.homodaba.movies/resources/
fi

build_addon_zip plugin.homodaba.movies matrix


ADDON_DESC_FILE=plugin.homodaba.movies/addon.xml
sed -i 's/addon="xbmc.python" version="3.0.0"/addon="xbmc.python" version="2.25.0"/g' $ADDON_DESC_FILE

build_addon_zip plugin.homodaba.movies leia
