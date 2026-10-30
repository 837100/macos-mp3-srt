#!/usr/bin/env python3
"""Transcribe Korean audio to SRT using local whisper.cpp and ffmpeg."""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
import tempfile
import urllib.request
from pathlib import Path


MODELS = {
    "small": "ggml-small.bin",
    "medium": "ggml-medium.bin",
    "large-v3-turbo": "ggml-large-v3-turbo.bin",
}
MODEL_BASE_URL = "https://huggingface.co/ggerganov/whisper.cpp/resolve/main"
APP_SUPPORT = Path.home() / "Library" / "Application Support" / "KoreanSRT"


def get_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="로컬 Whisper 모델로 오디오를 한국어 SRT 자막으로 변환합니다."
    )
    parser.add_argument("audio", type=Path, help="입력 MP3 파일")
    parser.add_argument("-o", "--output", type=Path, help="출력 SRT 경로 (기본: 입력 파일과 같은 폴더)")
    parser.add_argument("-m", "--model", choices=MODELS, default="medium", help="모델 (기본: medium)")
    parser.add_argument("--threads", type=int, help="CPU 스레드 수 (기본: 자동)")
    parser.add_argument("--overwrite", action="store_true", help="기존 SRT 파일 덮어쓰기")
    return parser.parse_args()


def require_program(name: str) -> str:
    path = shutil.which(name)
    if path is None:
        raise RuntimeError(f"'{name}' 명령을 찾을 수 없습니다. ./setup.sh 를 실행하세요.")
    return path


def ensure_model(model_name: str) -> Path:
    model_dir = APP_SUPPORT / "models"
    model_dir.mkdir(parents=True, exist_ok=True)
    model_path = model_dir / MODELS[model_name]
    if model_path.is_file() and model_path.stat().st_size > 0:
        return model_path

    url = f"{MODEL_BASE_URL}/{model_path.name}"
    partial = model_path.with_suffix(model_path.suffix + ".part")
    print(f"모델 다운로드 중: {model_name} (첫 실행에만 필요합니다)")
    try:
        request = urllib.request.Request(url, headers={"User-Agent": "KoreanSRT/1.0"})
        with urllib.request.urlopen(request, timeout=60) as response, partial.open("wb") as out:
            total = int(response.headers.get("Content-Length", "0"))
            downloaded = 0
            while True:
                block = response.read(1024 * 1024)
                if not block:
                    break
                out.write(block)
                downloaded += len(block)
                if total:
                    print(f"\r  {downloaded / total * 100:5.1f}%", end="", flush=True)
        if total and partial.stat().st_size != total:
            raise RuntimeError("모델 다운로드 크기가 예상과 다릅니다. 다시 실행해 주세요.")
        partial.replace(model_path)
        print(f"\n모델 저장 완료: {model_path}")
    except Exception:
        partial.unlink(missing_ok=True)
        raise
    return model_path


def main() -> int:
    args = get_args()
    audio = args.audio.expanduser().resolve()
    if not audio.is_file():
        print(f"오디오 파일을 찾을 수 없습니다: {audio}", file=sys.stderr)
        return 2
    if audio.suffix.lower() != ".mp3":
        print("현재 입력 형식은 MP3만 지원합니다.", file=sys.stderr)
        return 2

    output = (args.output.expanduser() if args.output else audio.with_suffix(".srt")).resolve()
    if output.exists() and not args.overwrite:
        print(f"출력 파일이 이미 있습니다: {output}\n덮어쓰려면 --overwrite를 지정하세요.", file=sys.stderr)
        return 2

    try:
        whisper_cli = require_program("whisper-cli")
        ffmpeg = require_program("ffmpeg")
        model = ensure_model(args.model)
        output.parent.mkdir(parents=True, exist_ok=True)

        with tempfile.TemporaryDirectory(prefix="korean-srt-") as temp_dir:
            temp = Path(temp_dir)
            wav = temp / "audio.wav"
            base = temp / "captions"
            print("MP3를 Whisper 입력 형식으로 변환 중...")
            subprocess.run(
                [ffmpeg, "-nostdin", "-hide_banner", "-loglevel", "error", "-y", "-i", str(audio),
                 "-ar", "16000", "-ac", "1", "-c:a", "pcm_s16le", str(wav)],
                check=True,
            )
            command = [whisper_cli, "-m", str(model), "-f", str(wav), "-l", "ko", "-osrt", "-of", str(base)]
            if args.threads:
                if args.threads < 1:
                    raise RuntimeError("--threads 값은 1 이상이어야 합니다.")
                command.extend(["-t", str(args.threads)])
            print("한국어 음성 인식 중...")
            subprocess.run(command, check=True)
            generated = base.with_suffix(".srt")
            if not generated.is_file():
                raise RuntimeError("whisper.cpp가 SRT 파일을 만들지 않았습니다.")
            if output.exists() and not args.overwrite:
                raise RuntimeError(f"출력 파일이 이미 있습니다: {output}")
            shutil.move(str(generated), str(output))
        print(f"완료: {output}")
        return 0
    except subprocess.CalledProcessError as exc:
        print(f"명령 실행에 실패했습니다 (종료 코드 {exc.returncode}).", file=sys.stderr)
        return exc.returncode or 1
    except (OSError, RuntimeError, urllib.error.URLError) as exc:
        print(f"오류: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
