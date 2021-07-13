## Preparar el entorno python
* Instalar pyenv y virtualenv
```bash
# Instalamos una version de python 3.X.X
~ pyenv install 3.8.0
# Creamos un entorno para homodaba
~ pyenv virtualenv 3.8.0 homodaba
# Configuramos el directorio actual para que use el entorno creado
~ echo "homodaba" > .python-version
# Inicializamos el entorno
~ pyenv init --path
```
* Instalar dependencias
```bash
~ pip install -r python-requirements.txt
```

## Rutina (TODO: bpk)
* Generas csv con basheline
* Importas csv
   - Verificas resultados
* Compruebas con csv_2_imdb
   - Verificas resultados
   - Si hay nuevos imdb_id, volver a importar
