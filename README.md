# idempiere-cli

CLI profesional para detectar, validar e instalar ambientes de iDempiere en servidores Linux.

El ejecutable se llama `idempiere-cli` para evitar confusión con el usuario Linux `idempiere`, carpetas como `/opt/idempiere`, servicios systemd y el ERP.

## Estado actual

MVP funcional con:

- `idempiere-cli detect`
- `idempiere-cli check`
- `idempiere-cli install --dry-run`
- `idempiere-cli install --profile perfil.yml`
- `idempiere-cli install --interactive`
- Opciones interactivas para instalar Nginx y crear un site reverse proxy.
- Lectura de perfiles YAML.
- Instalación de dependencias opcional durante `idempiere-cli install`, no durante instalación del CLI.
- Generación de `idempiereEnv.properties`.
- Creación opcional de servicio systemd.
- Logs en `~/.idempiere-cli/logs/idempiere-cli.log`.

## Requisitos del CLI

- Python 3.10+
- Linux para instalación real de iDempiere
- `pipx` recomendado

## Instalación

```bash
curl -fsSL https://raw.githubusercontent.com/josianascanio/idempiere-cli/main/bootstrap.sh | sudo bash
```

El `bootstrap.sh` instala las dependencias necesarias para ejecutar el CLI. Las dependencias propias de iDempiere, como Java, PostgreSQL, Nginx o `unzip`, se seleccionan y validan dentro de `idempiere-cli install`.

Si `pipx` muestra un aviso indicando que `/root/.local/bin` no está en el `PATH`, normalmente puedes ignorarlo cuando usas `sudo bash`: el bootstrap crea un enlace global en `/usr/local/bin/idempiere-cli` y lo verifica al final.

## Uso básico

```bash
idempiere-cli
idempiere-cli --help
idempiere-cli detect
idempiere-cli check
idempiere-cli install --interactive --dry-run
idempiere-cli install --profile profiles/idempiere12-test.example.yml --dry-run
```

Si ejecutas `idempiere-cli` sin argumentos, se abre un menú interactivo para detectar infraestructura, validar el servidor, instalar iDempiere o simular una instalación con `--dry-run`.

Por ahora el instalador interactivo solo permite iDempiere 12. El soporte para iDempiere 10, 11 y 13 se agregará en fases posteriores con sus dependencias específicas.

## Qué hace `--dry-run`

`--dry-run` valida y muestra el plan sin modificar el servidor.

Sí hace:

- Lee el perfil YAML.
- Detecta OS, distribución, arquitectura, RAM, disco, Java, PostgreSQL, Nginx y puertos.
- Resuelve `installer: auto`.
- Muestra validaciones.
- Muestra el resumen de instalación.
- Muestra comandos y archivos que generaría.

No hace:

- No instala paquetes `apt`.
- No crea carpetas.
- No descarga ZIP.
- No extrae archivos.
- No ejecuta scripts de iDempiere.
- No crea servicio systemd.
- No reinicia servicios.

Ejemplo:

```bash
idempiere-cli install --profile profiles/idempiere12-test.example.yml --dry-run
```

## Dependencias de iDempiere

El CLI no instala dependencias de iDempiere cuando instalas el comando con `pipx`.

Las dependencias se validan y se pueden instalar solo cuando ejecutas `idempiere-cli install`.

En modo interactivo:

```bash
idempiere-cli install --interactive
```

El CLI detecta faltantes y pregunta cuáles instalar. En el selector aparecen con nombres descriptivos, por ejemplo `Java 17 JDK`, `PostgreSQL 15 server` y `PostgreSQL 15 client tools (psql, pg_dump, pg_restore)`.

Si seleccionas `postgresql-15` y el paquete no existe en los repositorios base del sistema, el CLI configura automáticamente el repositorio oficial PostgreSQL PGDG antes de instalarlo.

Durante la instalación real, `apt` se muestra de forma compacta y guarda la salida completa en logs. La descarga, extracción y scripts internos de iDempiere muestran salida en vivo para facilitar diagnóstico.

En modo perfil:

```yaml
dependencies:
  install_missing: true
  base: true
  java: true
  postgres: true
  nginx: false
```

También puedes forzar por CLI:

```bash
idempiere-cli install --profile profiles/idempiere12-test.example.yml --install-dependencies
```

## Detect

```bash
idempiere-cli detect
```

Muestra:

- Sistema operativo.
- Distribución Linux.
- Arquitectura.
- Kernel.
- CPU.
- RAM total y disponible.
- Disco disponible en `/opt`.
- PostgreSQL instalado y versiones.
- Clústeres PostgreSQL con `pg_lsclusters`.
- Java detectado.
- Nginx detectado.
- Puertos relevantes.
- Instalador recomendado.

Reglas de instalador:

- `x86_64` o `amd64` en Ubuntu/Debian compatible: `12-x86`.
- `aarch64` o `arm64`: `12-arm`.
- Debian puro: `12-debian`.
- Si no puede decidir, requiere selección manual.

## Check

```bash
idempiere-cli check
idempiere-cli check --profile profiles/idempiere12-test.example.yml
idempiere-cli check --target-version 12
idempiere-cli check --installer 12-x86
```

Valida:

- Linux compatible.
- Arquitectura compatible.
- RAM mínima y recomendada como advertencia, no bloqueante.
- Disco mínimo y recomendado como advertencia, no bloqueante.
- PostgreSQL.
- Java requerido.
- Puertos web, SSL y DB.
- Nginx.
- Directorio base.
- Comandos requeridos: `curl`, `wget`, `unzip`, `tar`, `git`, `psql`, `pg_dump`, `pg_restore`, `systemctl`, `ss`.

## Perfil YAML

Ejemplo principal:

```bash
profiles/idempiere12-test.example.yml
```

Campos importantes:

- `version`: versión iDempiere.
- `installer`: `auto`, `12-x86`, `12-arm`, `12-debian`.
- `code` y `env`: forman nombres como `80_idempiere`.
- `base_dir`: base de instalación, por ejemplo `/opt/sas`.
- `java.home`: `JAVA_HOME` para `idempiereEnv.properties`.
- `database`: conexión y nombre de base.
- `ports`: puertos web y SSL. Se derivan con `80{code}` y `84{code}` en el modo interactivo.
- `idempiere.download_url`: ZIP de iDempiere.
- `dependencies.install_missing`: permite instalar faltantes durante `install`.

En modo interactivo, estos valores se calculan automáticamente y no se preguntan:

- Ruta de instalación: `{base_dir}/{code}_{env}`.
- Base de datos: `{code}_{env}`.
- Servicio: `{code}_{env}`.
- Puerto web: `80{code}`.
- Puerto SSL: `84{code}`.

Con los defaults `code=80`, `env=idempiere` y `base_dir=/opt/sas`, el CLI propone:

- Ruta: `/opt/sas/80_idempiere`.
- Base de datos: `80_idempiere`.
- Puerto web: `8080`.
- Puerto SSL: `8480`.

## Instalación iDempiere 12 con perfil

Primero prueba:

```bash
idempiere-cli install --profile profiles/idempiere12-test.example.yml --dry-run
```

Luego en el servidor de prueba:

```bash
sudo idempiere-cli install --profile profiles/idempiere12-test.example.yml --install-dependencies
```

La instalación real requiere root porque escribe en `/opt`, instala paquetes y puede crear servicios systemd.

## Flujo de instalación real

El instalador Python hace:

1. Detecta infraestructura.
2. Lee perfil YAML o crea perfil interactivo.
3. Valida recursos y dependencias.
4. Pregunta confirmación si no se usa `--force`.
5. Instala dependencias faltantes si se autorizó.
6. Crea carpeta destino.
7. Descarga ZIP de iDempiere.
8. Extrae ZIP.
9. Copia `idempiere-server` al destino.
10. Genera `idempiereEnv.properties`.
11. Ejecuta `silent-setup-alt.sh`.
12. Ejecuta `RUN_ImportIdempiere.sh` desde `utils` si `install.create_database: true`.
13. Ejecuta `utils/RUN_SyncDB.sh`.
14. Ejecuta `sign-database-build-alt.sh`.
15. Crea el usuario Linux `idempiere` si no existe.
16. Aplica propietario `idempiere:idempiere` a la carpeta instalada.
17. Crea, habilita y arranca el servicio systemd si `install.create_service: true`.

## Nginx

Desde el menú interactivo puedes usar:

- `Nginx`.

Dentro del submenú puedes:

- Instalar Nginx.
- Crear site Nginx.
- Probar configuración.
- Recargar Nginx.

El site Nginx genera un reverse proxy para iDempiere hacia el puerto web, por defecto `8080`. Puede generarse en HTTP o con bloque HTTPS si proporcionas rutas de certificado y llave SSL.

## Requisitos recomendados

- RAM sugerida pruebas: 4 GB mínimo.
- RAM recomendada pruebas: 6 GB.
- RAM producción: 8 GB o más.
- Disco sugerido: 20 GB mínimo.
- Disco recomendado: 50 GB o más.
- iDempiere 10: Java 11.
- iDempiere 12: Java 17.
- PostgreSQL 13 o superior.
- Recomendado separar ambientes por clúster/puerto PostgreSQL.

## Seguridad

- Usa `--dry-run` antes de instalar.
- La instalación real pide confirmación.
- La instalación real requiere root.
- No se instalan dependencias de iDempiere durante la instalación del CLI.
- Si la base de datos destino ya existe, se bloquea salvo `--force`.
- Si la ruta destino no está vacía, se bloquea salvo `--force`.

## Logs

```bash
~/.idempiere-cli/logs/idempiere-cli.log
```

Puedes revisar:

```bash
tail -f ~/.idempiere-cli/logs/idempiere-cli.log
```

## Próximas fases

- `db backup`, `db restore`, `db sync`.
- `migrate` de iDempiere 10 a 12.
- `service start/stop/status`.
- `nginx create-site/test/reload`.
- `status` para ambientes detectados.
