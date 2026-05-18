#!/usr/bin/env bash
set -e

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
echo "Instalando idempiere-cli..."

if ! command -v python3 >/dev/null 2>&1; then
  echo "ERROR: python3 no está instalado."
  exit 1
fi

if ! python3 -c 'import sys; raise SystemExit(0 if sys.version_info >= (3, 10) else 1)'; then
  echo "ERROR: idempiere-cli requiere Python 3.10 o superior."
  exit 1
fi

python3 -m pip install --user pipx || true
python3 -m pipx ensurepath || true
python3 -m pipx install . --force

echo "Instalación completada."
echo "Ejecuta: idempiere-cli --help"
