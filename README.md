# Sistema de Gestion de entradas

Este documento describe los pasos para configurar.

## Pre-requisitos
Antes de comenzar, asegúrate de contar con los siguientes requisitos:
- **Docker** instalado y en ejecución.
- **Make** instalado.

### Instalación de Make en Windows

Si usas Windows, puedes instalar `Make` con (https://chocolatey.org/install):

Ejecuta este comando en PowerShell:
```shell
choco install make
```

## Clonación del repositorio
Para clonar el repositorio ejecuta el siguiente comando:

```shell
git clone https://github.com/juanpaxz/sistema_gestion_entradas_salidas.git
```

Crea el archivo:

```shell
.env
```

Copiando la información del archivo:

```shell
.env.example
```
<br><b>NOTA:</b> Esto para correr la aplicación en modo local.

## Actualización de tu rama de desarrollo
Para tener tu rama de desarrollo al día con la rama main sigue las siguientes instrucciones:

**NOTA:** Vamos a usar como ejemplo la rama **_new-feature_**.

1. Haz commit de tus cambios actuales.

2. Cambiate a la rama **_main_** y descarga los nuevos cambios con:

   ```shell
   git switch main         # Para cambiar a la rama main
   git pull               # Para descargar los cambios actuales de main
   ```
3. Una vez con los cambios descargados regresa a tu rama de trabajo con:

   ```shell
   git switch new-feature  # Para regresar a la rama de trabajo
   ```

4. Fusiona los cambios que estan en **_main_** directamente en tu rama **_new-feature_**.

   ```shell
   git merge main          # Para fusionar main con tu rama
   ```
5. En caso de haber conflictos por modificar el mismo archivo deberias ver algo como esto, ejemplo:

   ```shell
   <<<<<<< HEAD
   Hola, buen día.
   =======
   Hola, ¿cómo estás?
   >>>>>>> new-feature
   ```

    Para solucionar esto debes eliminar alguno de los cambios, ya sea HEAD (el entrante) o fix-feature (el actual), esto dependiendo de cual de ambos cambios sea el más actualizado.
    
    Finalmente solo haz commit del cambio elegido.

## Pasos para ejecutar el sistema
### 1. Iniciar los contenedores
Crea los contenedores con el siguiente comando:

```shell
make build
```

La primera ejecución puede tardar algunos minutos, pero las siguientes serán más rápidas.

Este comando crea siete contenedores:
- **nginx-gestion**: Puerta de entrada única del sistema, la cual recibe las peticiones.
- **gestion**: Aplicación Django del sistema de gestion de entradas.
- **gestion-db**: Base de datos MariaDB para el sistema de gestion entradas.

Sabrás que los contenedores están listos cuando veas un mensaje similar a este:

```shell
 ✔ gestion                                          Built 
 ✔ Network sistema_gestion_entradas_salidas_default Created 
 ✔ Container gestion_db                             Healthy 
 ✔ Container gestion_de_entradas                    Started 
 ✔ Container nginx-gestion                          Started 
```

Una vez listos, puedes acceder a los sistemas desde:
- [`Sistema de gestion_de_entradas`](http://localhost/8001).

⚠ **Nota:** Es necesario esperar aproximadamente 5 segundos para que los contenedores carguen completamente.

Para detener los contenedores, ejecuta el comando:

```shell
make down
```

### 2. Aplicar migraciones
Si deseas aplicar las migraciones para todos los contenedores ejecuta el comando:

```shell
make migrate
```

Si la operación es exitosa, verás un resultado similar a este:

```shell
Operations to perform:
  Apply all migrations: admin, auth, sessions
Running migrations:
  Applying contenttypes.0001_initial... OK
  Applying auth.0001_initial... OK
  Applying admin.0001_initial... OK
  Applying admin.0002_logentry_remove_auto_add... OK
```

Después de ejecutar `make build` una vez, no es necesario volverlo a ejecutar en cada ocasión. Solo usa:

```shell
make up
```

Recuerda esperar 5 segundos para que la base de datos esté lista.

## Base de Datos

En la base de datos del  **Sistema de gestion de entradas** algunos de los datos se llenan automáticamente al ejecutar las migraciones.

Si necesitas reiniciar las bases de datos por completo (borrar todos los datos), puedes ejecutar:

```shell
make destroy
```

Para volver a iniciar sin crear nuevamente los contenedores, usa:

```shell
make up
```

## Crear un superusuario
Para acceder al sistema como administrador, es necesario crear un superusuario. Sigue estos pasos:

1. Ejecuta el siguiente comando para crear el superusuario:

   ```shell
   make superuser
   ```

2. Completa los datos solicitados:
   - **Username**
   - **Email**
   - **Password**
   - **Password (again)**

Una vez finalizado, ya podrás acceder al sistema seleccionado.
