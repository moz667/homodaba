# Readme

## Listado de addons:
 * plugin.homodaba.movies, es una prueba para ver como funcionaba el tema de addons en kodi (spoiler: es muy doloroso ^_^), basicamente te saca una navegacion por tags y posteriormente las pelis.

## Como probar los addons:
La forma mas facil que he visto es basicamente (asumimos que tienes un kodi en local):
1. Instalar el addon:
    1. Esto puedes hacerlo copiando el addon a pelo (la forma mas sencilla)
        ```bash
        rsync -va plugin.homodaba.movies/ ~/.kodi/addons/plugin.homodaba.movies/
        ```
    1. Creando un zip con el addon, aunque esto requiere mas pasos puede ser util en algunas situaciones (probando en raspberry por ejemplo, o para instalar dependencias)
        1. Creas el zip del addon:
            ```bash
            zip -r plugin.homodaba.movies.zip plugin.homodaba.movies/
            ```
        1. Lo copias al kodi donde lo vas a instalar
        1. Instalas utilizando la ui de kodi (la primera vez, te va a pedir que autorices la instalacion de addons de terceros)
1. Seguir el log:
    ```bash
    tail -f ~/.kodi/temp/kodi.log
    ```
1. Activar el addon a traves de la interfaz de kodi
1. Probar (Si encuentras algun problema, tratar de solucionarlo y volver a instalar el addon)

En principio eso es todo, pero te pueden pasar distintas cosas:
1. Que te de error en la instalacion (si lo haces a traves de zip) y no sepas porque es... el error que me pasaba a mi raruno era un error al extraer el zip, despues de volverme loco cambiando cosas y probando varios zip la solucion fue reiniciar kodi
1. Que te funcione en un kodi y en otro no. Aqui deberias comprobar:
    - La version de los dos kodi.
    - Reiniciar los dos kodi (a ver si el error aparece en el que parecia que funcionaba)
    - Si se trata de un error en un import, revisar que tenga la dependencia definida. (OJO: para que te instale dependencias tienes que instalar desde repositorio o con zip. Alternativamente puedes buscar un plugin que tenga la misma dependencia e instalarlo antes... pero esto puede ser un poco locura)

## Cosillas:

* Por defecto el addon plugin.homodaba.movies, esta hecho para kodi matrix (python3), aunque resulta bastante trivial hacerlo funcionar en leia (python2), tuvimos que hacer los import compatibles:

    Actualmente solo cambiando esta linea de addon.xml, lo haremos compatible:
    ```xml
    <import addon="xbmc.python" version="3.0.0" />
    ```
    ```xml
    <import addon="xbmc.python" version="2.25.0" />
    ```