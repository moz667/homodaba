# Nueva funcionalidad: Importar con actualización de existentes

## Pasos procesamiento

1. Procesamos un registro nuevo del csv de importacion
2. Si encuentra peli local (por storage o no... creo que da lo mismo)
   1. Si se trata de una peli que podemos buscar en la API (`!not_an_imdb_movie`)
      1. Buscamos en la API
      2. Si la encontramos en la API
         1. Actualizamos los datos
      3. Si no la encontramos en la API, mostramos mensaje de que ya no se encuentra?
   2. Sino se trata de una peli que podemos buscar en la API
      1. Actualizamos los datos con los que vienen en el CSV
3. Si no encuentra peli local, se trata de un registro nuevo y actuamos como normalmente

## Que actualizamos?

* En principio todos los datos que recuperamos que hayan cambiado, a excepción de storage types (ver mas abajo el problema con ["Actualizar storage types"](#actualizar-storage-types))
* Deberiamos tener en cuenta que cuando actualicemos una pelicula, al menos en el mismo procesado del csv, no deberiamos actualizar de nuevo esa misma peli (almacenar en memoria el tmdb_id de actualizados por ejemplo para no actualizar de nuevo esa pelicula)

## Problemas

### Actualizar storage types

En la actualidad no podemos actualizar el local storage ya que puede que el local storage se encuentre en varios registros distintos... esto puede ser un problema porque no tratamos mas el csv antes de importar, es decir, lo suyo seguramente seria agrupar todos los registros del csv por titulo,año,director... etc para localizar las distintas peliculas, una vez hecho esto tener una lista de objetos que agrupe estas en un solo elemento y que tenga una lista compartida de storage types, tags y demas...

Como no tratamos el csv y lo que procesamos es una lista de registros se va a hacer dificil el saber si una peli dispone de mas storage types (hasta que no recorramos todos los registros), se podria chapuzear (recorrer en cada caso buscando por mas storage types)...

