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
- Lectura de perfiles YAML.
- Instalación de dependencias opcional durante `idempiere-cli install`, no durante instalación del CLI.
- Generación de `idempiereEnv.properties`.
- Creación opcional de servicio systemd.
- Logs en `~/.idempiere-cli/logs/idempiere-cli.log`.

## Requisitos del CLI

- Python 3.10+
- Linux para instalación real de iDempiere
- `pipx` recomendado

## Instalación desde Git

```bash
pipx install git+https://github.com/josianascanio/idempiere-cli.git
```

## Instalación de un solo comando en servidor limpio

Para instalar solo el CLI y sus dependencias mínimas (`python3`, `pip`, `venv`, `pipx`, `git`, `curl`, certificados):

```bash
curl -fsSL https://raw.githubusercontent.com/josianascanio/idempiere-cli/main/bootstrap.sh | sudo bash
```

Para instalar el CLI y abrir el instalador interactivo en la misma línea:

```bash
curl -fsSL https://raw.githubusercontent.com/josianascanio/idempiere-cli/main/bootstrap.sh | sudo bash -s -- install --interactive
```

Para probar sin tocar el servidor:

```bash
curl -fsSL https://raw.githubusercontent.com/josianascanio/idempiere-cli/main/bootstrap.sh | sudo bash -s -- install --interactive --dry-run
```

Para instalar iDempiere permitiendo que el CLI instale dependencias faltantes del servidor durante `install`:

```bash
curl -fsSL https://raw.githubusercontent.com/josianascanio/idempiere-cli/main/bootstrap.sh | sudo bash -s -- install --interactive --install-dependencies
```

El `bootstrap.sh` instala las dependencias necesarias para ejecutar el CLI. Las dependencias propias de iDempiere, como Java, PostgreSQL, Nginx o `unzip`, se seleccionan y validan dentro de `idempiere-cli install`.

Si `pipx` muestra un aviso indicando que `/root/.local/bin` no está en el `PATH`, normalmente puedes ignorarlo cuando usas `sudo bash`: el bootstrap crea un enlace global en `/usr/local/bin/idempiere-cli` y lo verifica al final.

## Instalación local editable

```bash
git clone https://github.com/josianascanio/idempiere-cli.git
cd idempiere-cli
pipx install . --force
```

También puedes usar:

```bash
./install.sh
```

## Uso básico

```bash
idempiere-cli --help
idempiere-cli detect
idempiere-cli check
idempiere-cli install --interactive --dry-run
idempiere-cli install --profile profiles/idempiere12-test.example.yml --dry-run
```

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

El CLI detecta faltantes y pregunta cuáles instalar.

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
- RAM mínima y recomendada.
- Disco mínimo y recomendado.
- PostgreSQL.
- Java requerido.
- Puertos web, SSL, shutdown y DB.
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
- `code` y `env`: forman nombres como `90_idaan_test`.
- `base_dir`: base de instalación, por ejemplo `/opt/sas`.
- `java.home`: `JAVA_HOME` para `idempiereEnv.properties`.
- `database`: conexión y nombre de base.
- `ports`: puertos web, SSL y shutdown.
- `idempiere.download_url`: ZIP de iDempiere.
- `dependencies.install_missing`: permite instalar faltantes durante `install`.

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
12. Ejecuta `utils/RUN_ImportIdempiere.sh` si `install.create_database: true`.
13. Ejecuta `utils/RUN_SyncDB.sh`.
14. Ejecuta `sign-database-build-alt.sh`.
15. Crea y habilita servicio systemd si `install.create_service: true`.

## Requisitos recomendados

- RAM mínima pruebas: 4 GB.
- RAM recomendada pruebas: 6 GB.
- RAM producción: 8 GB o más.
- Disco mínimo: 20 GB.
- Disco recomendado: 50 GB o más.
- iDempiere 10: Java 11.
- iDempiere 12: Java 17.
- PostgreSQL 13 o superior.
- Recomendado separar ambientes por clúster/puerto PostgreSQL.

## Seguridad

- Usa `--dry-run` antes de instalar.
- La instalación real pide confirmación.
- La instalación real requiere root.
- No se instalan dependencias durante `pipx install`.
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
