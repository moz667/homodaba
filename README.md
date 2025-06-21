# homodaba
Aplicación django para gestionar/clasificar los videos de @bpk667

El nombre viene de la afficción de @bpk667 a dar por saco... (es coña ^ _ ^ viene de: HOme MOvie DAtaBAse)

## Lista de comandos comunes

* Shell en el contenedor de la app
    
    ```bash
    docker compose exec app sh
    ```

* Manage Django
    
    ```bash
    docker compose exec app python homodaba/manage.py
    ```

* Crear un super usuario (desde el contenedor de la app)
    
    ```bash
    python homodaba/manage.py createsuperuser
    ```

* Importar CSV con datos de libreria (desde el contenedor de la app)
    
    ```bash
    python homodaba/manage.py import_csv --csv-file /opt/app/import/library.csv -v 3
    ```

## Docker registry

Ejemplo de registro de imagen: https://hub.docker.com/r/moz667/homodaba

```bash
# Construccion basica, sqlite sin florituras
docker build -t moz667/homodaba:latest-mini \
    -f docker/app/Dockerfile .

# Push
docker push moz667/homodaba:latest-mini
```


## Tareas pendientes
[Lista de tareas pendientes](./todo.md)