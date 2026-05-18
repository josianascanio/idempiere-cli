#!/usr/bin/env bash
set -euo pipefail

REPO_URL="${IDEMPIERE_CLI_REPO:-git+https://github.com/josianascanio/idempiere-cli.git}"

print_banner() {
  echo ""
  echo "  _     _                       _                        _ _ "
  echo " (_)   | |                     (_)                      | (_)"
  echo "  _  __| | ___ _ __ ___  _ __   _  ___ _ __ ___    ___| |_ "
  echo " | |/ _\` |/ _ \\ '_ \` _ \\| '_ \\ | |/ _ \\ '__/ _ \\  / __| | |"
  echo " | | (_| |  __/ | | | | | |_) || |  __/ | |  __/ | (__| | |"
  echo " |_|\\__,_|\\___|_| |_| |_| .__/ |_|\\___|_|  \\___|  \\___|_|_|"
  echo "                        | |                                 "
  echo "                        |_|    Developer CLI for iDempiere  "
  echo ""
}

log() {
  echo "[idempiere-cli bootstrap] $*"
}

die() {
  echo "ERROR: $*" >&2
  exit 1
}

run_as_root() {
  if [[ "${EUID}" -eq 0 ]]; then
    "$@"
  elif command -v sudo >/dev/null 2>&1; then
    sudo "$@"
  else
    die "Este script necesita root o sudo para instalar dependencias del CLI."
  fi
}

detect_os_family() {
  if [[ -r /etc/os-release ]]; then
    # shellcheck disable=SC1091
    . /etc/os-release
    echo "${ID:-unknown}"
  else
    echo "unknown"
  fi
}

install_cli_dependencies() {
  local distro
  distro="$(detect_os_family)"

  case "${distro}" in
    ubuntu|debian|linuxmint|pop)
      log "Instalando dependencias base del CLI con apt..."
      run_as_root apt update -y
      run_as_root apt install -y python3 python3-pip python3-venv pipx git curl ca-certificates
      ;;
    *)
      die "Distribución no soportada por bootstrap automático: ${distro}. Instala Python 3.10+, pipx y git manualmente."
      ;;
  esac
}

check_python_version() {
  command -v python3 >/dev/null 2>&1 || die "python3 no está instalado."
  python3 - <<'PY'
import sys
if sys.version_info < (3, 10):
    raise SystemExit("Python 3.10+ requerido. Detectado: %s" % sys.version.split()[0])
PY
}

pipx_cmd() {
  if python3 -m pipx --version >/dev/null 2>&1; then
    python3 -m pipx "$@"
  elif command -v pipx >/dev/null 2>&1; then
    pipx "$@"
  else
    die "pipx no quedó disponible después de instalar dependencias."
  fi
}

install_cli() {
  log "Instalando idempiere-cli desde ${REPO_URL}..."
  pipx_cmd install "${REPO_URL}" --force
}

configure_pipx_path() {
  # When bootstrap runs through sudo, pipx installs under /root/.local/bin and
  # may warn that it is not on PATH. We still create /usr/local/bin below, but
  # this reduces confusion on systems where pipx can update the global path.
  pipx_cmd ensurepath --global >/dev/null 2>&1 || pipx_cmd ensurepath >/dev/null 2>&1 || true
}

resolve_cli_path() {
  local pipx_bin cli_path
  pipx_bin="$(pipx_cmd environment --value PIPX_BIN_DIR 2>/dev/null || true)"
  cli_path="${pipx_bin}/idempiere-cli"

  if [[ -x "${cli_path}" ]]; then
    echo "${cli_path}"
    return 0
  fi

  if command -v idempiere-cli >/dev/null 2>&1; then
    command -v idempiere-cli
    return 0
  fi

  die "No se encontró el binario idempiere-cli después de instalar."
}

link_cli() {
  local cli_path
  cli_path="$(resolve_cli_path)"
  if [[ "${EUID}" -eq 0 ]]; then
    ln -sf "${cli_path}" /usr/local/bin/idempiere-cli
    log "Comando disponible en /usr/local/bin/idempiere-cli"
  elif command -v sudo >/dev/null 2>&1; then
    sudo ln -sf "${cli_path}" /usr/local/bin/idempiere-cli || true
  fi
}

global_cli_path() {
  if [[ -x /usr/local/bin/idempiere-cli ]]; then
    echo "/usr/local/bin/idempiere-cli"
    return 0
  fi

  resolve_cli_path
}

verify_cli() {
  local cli_path
  cli_path="$(global_cli_path)"
  "${cli_path}" --help >/dev/null || die "idempiere-cli se instaló pero no pudo ejecutarse. Prueba: ${cli_path} --help"
  log "Verificación correcta: ${cli_path} --help"
}

main() {
  print_banner
  install_cli_dependencies
  check_python_version
  install_cli
  configure_pipx_path
  link_cli
  verify_cli

  log "Instalación del CLI completada."
  log "Prueba: /usr/local/bin/idempiere-cli --help"
  log "Si pipx mostró un warning de PATH para /root/.local/bin, puedes ignorarlo: el comando global quedó enlazado en /usr/local/bin/idempiere-cli."

  if [[ "$#" -gt 0 ]]; then
    log "Ejecutando: idempiere-cli $*"
    "$(global_cli_path)" "$@"
  fi
}

main "$@"
