#!/bin/bash

build_addon_zip() {
	ADDON_NAME=$1
	KODI_VERSION=$2
	ADDON_VERSION=`grep "<addon" $ADDON_NAME/addon.xml|sed -e 's/.*version="//g' -e 's/".*//g'`
	OUTPUT_ZIP_FILE="$KODI_VERSION/$ADDON_NAME/$ADDON_NAME-$ADDON_VERSION.zip"

	mkdir -p $KODI_VERSION/$ADDON_NAME

	echo " * Construyendo $ADDON_NAME ($KODI_VERSION) en $OUTPUT_ZIP_FILE ..."

	if [ -f $OUTPUT_ZIP_FILE ]; then
		rm $OUTPUT_ZIP_FILE
	fi

	if [ -e "$ADDON_NAME/resources/icon.png" ]; then
		cp $ADDON_NAME/resources/icon.png $KODI_VERSION/$ADDON_NAME
	fi

	cp $ADDON_NAME/addon.xml $KODI_VERSION/$ADDON_NAME

	cat $ADDON_NAME/addon.xml|grep -v "<?xml" >> $KODI_VERSION/addons.xml

	zip -qr $OUTPUT_ZIP_FILE $ADDON_NAME/
}

convert_from_matrix_to_leia() {
	ADDON_NAME=$1

	echo " * Convirtiendo $ADDON_NAME de matrix a leia ..."
	sed -i 's/addon="xbmc.python" version="3.0.0"/addon="xbmc.python" version="2.25.0"/g' $ADDON_NAME/addon.xml
}

mkdir -p build

for addon_dir in repository.homodaba plugin.homodaba.movies
do
	rsync -qa --del $addon_dir/ build/$addon_dir/
done

cd build

for kodi_version in matrix leia
do
	echo "<?xml version='1.0' encoding='UTF-8'?>" > $kodi_version/addons.xml
	echo "<addons>" >> $kodi_version/addons.xml
	build_addon_zip repository.homodaba $kodi_version
	if [ "$kodi_version" == "leia" ]; then
		convert_from_matrix_to_leia plugin.homodaba.movies
	fi
	build_addon_zip plugin.homodaba.movies $kodi_version
	echo "</addons>" >> $kodi_version/addons.xml
	md5sum $kodi_version/addons.xml | sed -e "s/ .*//g"> $kodi_version/addons.xml.md5
done

for addon_dir in repository.homodaba plugin.homodaba.movies
do
	rm -rf $addon_dir
done
