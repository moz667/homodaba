# homodaba
Aplicación django para gestionar/clasificar los videos de bpk

El nombre viene de la afficción de bpk a dar por saco... (es coña ^_^ viene de HOme MOvie DAtaBAse)


### TODO: Lista con cosas pendientes
1. Titulos conocidos (akas), viene con formato titulo (lista de cosas separadas por comas, normalmente pais o idioma) ejemplo:
"Zombieland 2 (World-wide, English title)", "Zombieland 2: Double Tap (United Kingdom)", "Retour à Zombieland (France)", "Zombieland 2: Doppelt hält besser (Germany, German title)", "Zombieland 2: Doppelt hält besser (Germany)",
este campo molaria usarlo como contexto... pero por ahora yo creo que lo vamos a dejar
Lo mismo este es un caso bueno para usar las tags de django-tagging
1. Definir delimitadores de CSV
1. Añadir campo con el certificate_rating_us : movie['certificates']
1. Actualizar info de peliculas en base al raw obtenido (esto se deberia poder hacer con from imdb.helpers import parseXML... pero nop)
1. Mostrar los tipos de medios disponibles en la busqueda de pelis
1. Mostrar los directores en la busqueda de pelis

