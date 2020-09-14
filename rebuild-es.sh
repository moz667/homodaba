#!/bin/bash

export ES_DSL_HOSTS='localhost:9200'
python homodaba/manage.py search_index --rebuild
