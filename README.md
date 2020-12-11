# homodaba
Aplicación django para gestionar/clasificar los videos de bpk

El nombre viene de la afficción de bpk a dar por saco... (es coña ^ _ ^ viene de 
HOme MOvie DAtaBAse)

#### TODO: (Lista con cosas pendientes)
1. Añadir campo para orden de visionado (para que bpk no este metiendo una 
tag por cada peli dentro de una saga :P)
1. Problema con los akas (si buscas love te saca pelis con el titulo en sloveno)
1. bot - formatear bonito
1. bot - sacar caratula en busquedas?
1. bot - logear accesos
1. bot - comando nuevo, detalle de pelicula
1. bot - hacer algo para cuando son muchos resultados (atachear fichero? paginar?)
1. Escaneo de directorios para buscar nuevos o seguir usando csvs?
1. Mostrar los directores en la busqueda de pelis
1. Busqueda por texto en participantes (peli o nombre de persona)
1. En reparto (MoviePerson) tenemos un problema (73k personas distintas en un 
    select)
    - Borrar las personas que solo sean actores y que solo aparedcan en una 
        peli? (entiendo que con esto quitaremos un monton) el problema son con
        pelis nuevas en las que debute alguien
    - Buscar la forma que solo saque un top 100 de cada tipo de rol, con ello
        nos evitamos el tener que borrar debutantes..
    - Pensar mas opciones...
1. Documentar (uff... que pereza  ^ _ ^)
1. Ver qué hacemos con las películas cuyo título original no es en inglés. El IMDB usa "World-wide (English title)" en lugar de "original title".
1. Ver qué hacemos con las películas que no están en IMDB.
