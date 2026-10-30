#!/bin/bash
set -euo pipefail

if [[ "$(uname -s)" != "Darwin" ]]; then
  echo "이 설치 스크립트는 macOS에서 실행해야 합니다." >&2
  exit 1
fi

if ! command -v brew >/dev/null 2>&1; then
  echo "Homebrew가 필요합니다. https://brew.sh 에서 설치한 뒤 다시 실행하세요." >&2
  exit 1
fi

brew install whisper.cpp ffmpeg

echo
echo "설치가 끝났습니다. 다음처럼 실행하세요:"
echo "  ./transcribe.py /path/to/audio.mp3"
