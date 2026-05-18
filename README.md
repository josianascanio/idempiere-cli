# iDempiere CLI

`idempiere-cli` is a guided command-line tool for detecting, validating, installing, and managing **iDempiere 12** environments on Linux servers.

It is designed as the next step after the original Bash provisioning scripts, keeping the same installation logic while adding validation, profiles, safer execution, dry-run support, interactive menus, logging, and reusable Python modules.

The executable is intentionally named `idempiere-cli` to avoid confusion with the Linux user `idempiere`, system folders such as `/opt/idempiere`, systemd services, or the ERP name itself.

## Contributors

<table>
  <tr>
    <td align="center">
      <a href="https://github.com/josianascanio">
        <img src="https://github.com/josianascanio.png" width="80" alt="Josian Ascanio" />
        <br />
        <sub><b>Josian Ascanio</b></sub>
      </a>
    </td>
    <td align="center">
      <a href="https://github.com/Carl0gonzalez">
        <img src="https://github.com/Carl0gonzalez.png" width="80" alt="Carlo Gonzalez" />
        <br />
        <sub><b>Carlo Gonzalez</b></sub>
      </a>
    </td>
  </tr>
</table>

> [!NOTE]
> The interactive installer currently targets iDempiere 12. Support for iDempiere 10, 11, and future versions will be added gradually with version-specific dependency rules.

## Quick Install

Install the CLI and its minimum runtime dependencies on a clean Debian or Ubuntu-compatible server:

```bash
curl -fsSL https://raw.githubusercontent.com/josianascanio/idempiere-cli/main/bootstrap.sh | sudo bash
```

After installation, start the interactive CLI:

```bash
sudo /usr/local/bin/idempiere-cli
```

If your shell already has `/usr/local/bin` in `PATH`, this also works:

```bash
idempiere-cli
```

> [!NOTE]
> If `pipx` warns that `/root/.local/bin` is not in `PATH`, you can usually ignore it when using the bootstrap script. The bootstrap creates and verifies a global `/usr/local/bin/idempiere-cli` link.

## Current Features

- Interactive main menu when running `idempiere-cli` without arguments.
- Server detection with installer recommendation.
- Server readiness checks for Linux, architecture, RAM, disk, Java, PostgreSQL, ports, Nginx, and required commands.
- Interactive iDempiere 12 installation flow.
- YAML profile support.
- `--dry-run` mode for safe simulation.
- Optional dependency installation during iDempiere installation.
- Automatic PostgreSQL PGDG repository configuration when PostgreSQL 15 packages are not available.
- `idempiereEnv.properties` generation.
- iDempiere setup, database import, sync, and signing script execution.
- Linux `idempiere` user creation and ownership adjustment.
- systemd service creation, enablement, and startup.
- Nginx submenu for installation, site creation, config test, and reload.
- Logs written to `~/.idempiere-cli/logs/idempiere-cli.log`.

## Available Installer Targets

| Target | Architecture | Operating system | Java | Status |
| --- | --- | --- | --- | --- |
| `12-x86` | AMD64 / x86_64 | Debian or Ubuntu-compatible systems | OpenJDK 17 | Supported |
| `12-arm` | ARM / aarch64 / arm64 | Debian or Ubuntu-compatible systems | OpenJDK 17 | Supported |
| `12-debian` | AMD64 / x86_64 | Debian-specific variant | OpenJDK or Temurin 17 | Supported |

The installer target can be detected automatically or selected manually.

## Basic Usage

```bash
idempiere-cli
idempiere-cli --help
idempiere-cli detect
idempiere-cli check
idempiere-cli install --interactive --dry-run
idempiere-cli install --profile profiles/idempiere12-test.example.yml --dry-run
```

Running `idempiere-cli` with no arguments opens the interactive menu:

- Detect infrastructure.
- Validate server.
- Install iDempiere interactively.
- Simulate interactive installation with `--dry-run`.
- Install from a YAML profile.
- Simulate profile installation with `--dry-run`.
- Open the Nginx submenu.
- View help.
- Exit.

## What `--dry-run` Does

`--dry-run` validates and shows the execution plan without changing the server.

It does:

- Read the YAML profile or collect interactive values.
- Detect OS, distribution, architecture, RAM, disk, Java, PostgreSQL, Nginx, and ports.
- Resolve `installer: auto`.
- Show validations.
- Show the installation summary.
- Show the commands and files that would be generated.

It does not:

- Install apt packages.
- Create directories.
- Download or extract iDempiere.
- Execute iDempiere scripts.
- Create system users.
- Create or start services.
- Reload Nginx.

Example:

```bash
idempiere-cli install --interactive --dry-run
```

## Server Detection

```bash
idempiere-cli detect
```

The detection command reports:

- Operating system.
- Linux distribution and version.
- Architecture.
- Kernel.
- CPU.
- Total and available RAM.
- Free disk space under `/opt`.
- PostgreSQL installation status and versions.
- PostgreSQL clusters through `pg_lsclusters`.
- Java installation and candidate `JAVA_HOME` paths.
- Nginx installation status.
- Relevant listening ports.
- Recommended installer target.

Installer recommendation rules:

- `x86_64` or `amd64` on Debian/Ubuntu-compatible systems: `12-x86`.
- `aarch64` or `arm64`: `12-arm`.
- Pure Debian: `12-debian` when applicable.
- Unknown environments require manual selection.

## Server Checks

```bash
idempiere-cli check
idempiere-cli check --profile profiles/idempiere12-test.example.yml
idempiere-cli check --target-version 12
idempiere-cli check --installer 12-arm
```

Checks include:

- Linux compatibility.
- Supported architecture.
- RAM and disk recommendations as warnings, not hard blockers.
- PostgreSQL installation and client tools.
- Java version required by iDempiere.
- Web, SSL, and PostgreSQL ports.
- Nginx status.
- Base directory status.
- Required commands such as `curl`, `wget`, `unzip`, `tar`, `git`, `fc-cache`, `psql`, `pg_dump`, `pg_restore`, `systemctl`, and `ss`.

## Interactive Installation Flow

The interactive installer asks for the values that should vary per environment:

- iDempiere version, currently `12`.
- Installer target, detected automatically when possible.
- Environment code, default `80`.
- Environment name, default `idempiere`.
- Base directory, default `/opt/sas`.
- PostgreSQL host and port.
- Database user and password.
- Missing dependencies to install.

These values are calculated automatically and are not asked directly:

- Installation path: `{base_dir}/{code}_{env}`.
- Database name: `{code}_{env}`.
- Service name: `{code}_{env}`.
- Web port: `80{code}`.
- SSL port: `84{code}`.

With the defaults, the installer proposes:

- Installation path: `/opt/sas/80_idempiere`.
- Database name: `80_idempiere`.
- Service name: `80_idempiere`.
- Web port: `8080`.
- SSL port: `8480`.

## Dependencies

The bootstrap command installs only what is required to run the CLI.

iDempiere dependencies are selected and installed during `idempiere-cli install`.

The interactive selector shows descriptive names, for example:

- `Java 17 JDK`.
- `PostgreSQL 15 server`.
- `PostgreSQL 15 client tools (psql, pg_dump, pg_restore)`.
- `fontconfig (fonts for reports/PDF)`.
- `unzip (extract iDempiere build)`.

If `postgresql-15` is selected and not available from the base repositories, the CLI configures the official PostgreSQL PGDG repository before installing it.

APT operations are displayed in compact mode and the full command output is written to the CLI log file.

## YAML Profiles

Example profile:

```bash
profiles/idempiere12-test.example.yml
```

Important fields:

- `version`: iDempiere version.
- `installer`: `auto`, `12-x86`, `12-arm`, or `12-debian`.
- `code` and `env`: generate names such as `80_idempiere`.
- `base_dir`: installation base path, for example `/opt/sas`.
- `java.home`: value used for `idempiereEnv.properties`.
- `database`: PostgreSQL connection and database values.
- `ports`: web and SSL ports.
- `idempiere.download_url`: iDempiere server ZIP URL.
- `dependencies.install_missing`: controls dependency installation in non-interactive profile mode.

Profile dry-run example:

```bash
idempiere-cli install --profile profiles/idempiere12-test.example.yml --dry-run
```

Profile installation example:

```bash
sudo idempiere-cli install --profile profiles/idempiere12-test.example.yml --install-dependencies
```

## What The Installer Does

The Python installer automates the main steps needed to prepare an iDempiere 12 server:

1. Detects infrastructure.
2. Reads a YAML profile or collects interactive values.
3. Validates resources and dependencies.
4. Shows a clear summary before applying changes.
5. Optionally installs missing dependencies.
6. Configures PostgreSQL PGDG when needed.
7. Configures local PostgreSQL basics.
8. Creates the destination folder.
9. Downloads and extracts the iDempiere server package.
10. Generates `idempiereEnv.properties`.
11. Runs `silent-setup-alt.sh`.
12. Runs `RUN_ImportIdempiere.sh` from `utils` when database creation is enabled.
13. Runs `RUN_SyncDB.sh`.
14. Runs `sign-database-build-alt.sh`.
15. Creates the Linux `idempiere` user when needed.
16. Applies `idempiere:idempiere` ownership to the installation folder.
17. Creates, enables, and starts the systemd service.

## Expected Installation Layout

The default installation layout follows the same pattern as the original provisioning scripts:

```bash
/opt/<folder>/<code>_<environment>
```

Example:

```bash
/opt/sas/80_idempiere
```

The generated service name follows the same `<code>_<environment>` pattern:

```bash
80_idempiere
```

## Nginx

The interactive menu includes a dedicated `Nginx` submenu.

Available actions:

- Install Nginx.
- Create an iDempiere reverse proxy site.
- Test Nginx configuration.
- Reload Nginx.

The generated site proxies:

- `/`.
- `/webui`.
- `/webui/zkau/comet`.

It can generate an HTTP-only site or an HTTPS site if certificate and key paths are provided.

The HTTPS template includes CORS headers:

```nginx
add_header 'Access-Control-Allow-Origin' '*';
add_header 'Access-Control-Allow-Methods' 'GET, POST, PUT, DELETE, OPTIONS';
add_header 'Access-Control-Allow-Headers' 'Authorization, Content-Type';
```

## Service Check

After installation, verify the generated service with:

```bash
systemctl status <service>
```

Example:

```bash
systemctl status 80_idempiere
```

You can also inspect logs with:

```bash
journalctl -u 80_idempiere -xe
```

## General Requirements

- Debian or Ubuntu-compatible server using `apt`.
- `root` access or a user with `sudo` permissions.
- Internet access to download packages, GPG keys, and the iDempiere server package.
- 2 CPU or more recommended.
- 4 GB RAM or more recommended.
- 20 GB free disk space or more recommended.

> [!NOTE]
> RAM and disk checks are warnings. They do not block installation, but low resources can still cause iDempiere setup or runtime failures.

## Logs

CLI logs are stored under:

```bash
~/.idempiere-cli/logs/idempiere-cli.log
```

Follow logs with:

```bash
tail -f ~/.idempiere-cli/logs/idempiere-cli.log
```

## Troubleshooting

### The service does not start

Check the service and journal:

```bash
systemctl status <service>
journalctl -u <service> -xe
```

### PostgreSQL does not connect

Verify the configured host, `pg_hba.conf`, PostgreSQL user password, and service status:

```bash
systemctl status postgresql
pg_lsclusters
```

### Java is not found

Confirm that Java 17 is installed and available in `PATH`:

```bash
java -version
```

The CLI detects `JAVA_HOME` from the active `java` executable before writing `idempiereEnv.properties`.

### Dependency installation fails

Review the full command output in:

```bash
~/.idempiere-cli/logs/idempiere-cli.log
```

## Roadmap

- Database commands: `db backup`, `db restore`, `db sync`.
- Migration workflow from iDempiere 10 to iDempiere 12.
- Service commands: `service start`, `service stop`, `service status`.
- Environment discovery through `status`.
- Version-specific support for iDempiere 10, 11, and future releases.
