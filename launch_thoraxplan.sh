#!/bin/bash
# Script de Inicialização Rápida do ThoraxPlan 3D no 3D Slicer
# Abre o 3D Slicer já carregando o módulo e selecionando-o automaticamente.

MODULE_PATH="/Users/vlaudimird.marques/3D_Slicer_New/ThoraxPlan"
SLICER_APP="/Applications/Slicer.app/Contents/MacOS/Slicer"

if [ -f "$SLICER_APP" ]; then
    echo "Iniciando 3D Slicer com ThoraxPlan 3D..."
    "$SLICER_APP" --additional-module-paths "$MODULE_PATH" --python-code "slicer.util.selectModule('ThoraxPlan')" &
else
    echo "Slicer.app não encontrado em /Applications/Slicer.app"
    open -a Slicer
fi
