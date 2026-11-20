{% docs bronze_layer %}
La capa Bronze contiene las tablas crudas cargadas por `src/ingestion.py` en
el esquema PostgreSQL `bronze`. dbt registra aquí esas tablas como fuentes;
no las copia a otra relación Bronze para evitar duplicar los datos originales.
{% enddocs %}
