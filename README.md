# api-httpcache

La vieja librería httppool convertida a microservicio.

## GET /

Devuelve el contenido de un sitio web dada la URL. Si el contenido no se encuentra en caché, realiza la descarga; en caso de existir, siempre devuelve el contenido de la caché.

### Parámetros

* q: URL que se desea consultar

### Ejemplo

* GET http://localhost:5000/q=https://google.com

## GET /update

Actualiza el contenido de todas las URL que están guardadas en caché.

* La actualización ocurre de forma asíncrona: este endpoint solamente levanta un hilo que realiza la actualización y retorna inmediatamente. Para conocer el estado del proceso, se puede consultar el **httpcache.log**.
* La actualización se realiza una sola vez: si se desea actualizar cada cierto intervalo de tiempo, se debe implementar un mecanismo que invoque al endpoint todas las veces que sean necesarias (Ej: se puede utilizar un **cron**).
