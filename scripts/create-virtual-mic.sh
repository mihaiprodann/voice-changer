#!/usr/bin/env bash
set -euo pipefail

SINK_NAME="voicechanger_sink"
SINK_DESC="VoiceChanger Sink"
SRC_NAME="voicechanger_mic"
SRC_DESC="VoiceChanger Mic"

echo "[1/2] Creare sink virtual: $SINK_DESC"
pactl load-module module-null-sink \
  sink_name="$SINK_NAME" \
  sink_properties=device.description="$SINK_DESC" \
  || echo "(already exists)"

echo "[2/2] Creare microfon virtual: $SRC_DESC"
pactl load-module module-remap-source \
  master="${SINK_NAME}.monitor" \
  source_name="$SRC_NAME" \
  source_properties=device.description="$SRC_DESC" \
  || echo "(already exists)"

echo
echo "Done."
echo "- Output in app: $SINK_DESC"
echo "- Microphone in applications: $SRC_DESC"
