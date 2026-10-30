# Korean MP3 → SRT (macOS)

MP3 음성을 로컬 Whisper 모델로 한국어 자막(`.srt`)으로 변환하는 작은 CLI 프로젝트입니다. 음성 파일은 외부 서비스로 전송하지 않습니다. 첫 실행에는 Whisper 모델과 작은 VAD 음성 감지 모델을 다운로드하며, 이후 변환은 오프라인으로 동작합니다.

## 요구 사항

- macOS 13 이상
- Homebrew
- Python 3.9 이상
- Apple Silicon 또는 Intel Mac

Apple Silicon에서는 `whisper.cpp`가 Metal GPU 가속을 사용할 수 있습니다. Intel Mac에서도 CPU로 실행됩니다.

## 설치

터미널에서 프로젝트 폴더로 이동한 뒤:

```bash
./setup.sh
```

설치 스크립트는 Homebrew의 `whisper.cpp`와 `ffmpeg`를 준비합니다.

## 사용법

```bash
./transcribe.py recording.mp3
```

기본 출력은 `recording.srt`입니다. 출력 위치와 모델을 지정할 수도 있습니다.

```bash
./transcribe.py recording.mp3 -o subtitles/meeting.srt
./transcribe.py recording.mp3 --model small
./transcribe.py recording.mp3 --vad-threshold 0.7
```

외장하드에 모델 파일이 이미 있다면 파일 자체 또는 모델 폴더를 지정할 수 있습니다.

```bash
# 모델 파일을 직접 지정
./transcribe.py recording.mp3 --model-path "/Volumes/외장하드/models/ggml-medium.bin"

# 모델 폴더를 지정하면 --model 값에 맞는 파일을 폴더 안에서 찾습니다.
./transcribe.py recording.mp3 --model small --model-path "/Volumes/외장하드/models"
```

폴더 경로를 쓸 때는 `--model`과 일치하는 모델 파일이 있어야 합니다. 예를 들어 `--model small`이면 `ggml-small.bin`을 찾습니다. 사용자 지정 경로의 모델은 다운로드되지 않습니다.

모델 선택:

| 모델 | 디스크 용량(대략) | 권장 상황 |
| --- | ---: | --- |
| `small` | 466 MB | 빠른 시작, 메모리가 적은 Mac |
| `medium` | 1.5 GB | 한국어 자막 기본값, 품질과 속도의 균형 |
| `large-v3-turbo` | 1.6 GB | 더 빠른 고품질 모델을 원하는 경우 |

기본 모델은 `medium`입니다. 처음 실행할 때 모델 파일을 `~/Library/Application Support/KoreanSRT/models/`에 다운로드합니다. 모델 다운로드는 인터넷 연결이 필요하지만, 완료 후 음성 인식은 로컬에서 실행됩니다.

## 명령 옵션

```text
usage: transcribe.py [-h] [-o OUTPUT] [-m {small,medium,large-v3-turbo}]
                     [--model-path MODEL_PATH] [--threads THREADS]
                     [--vad-threshold VAD_THRESHOLD] [--overwrite] audio
```

- `-o`, `--output`: SRT 저장 경로
- `-m`, `--model`: Whisper 모델 (기본값 `medium`)
- `--model-path`: 기존 모델 파일 또는 모델 폴더 경로. 생략하면 앱 지원 폴더에서 모델을 찾거나 다운로드
- `--threads`: CPU 스레드 수 지정 (기본값은 자동)
- `--vad-threshold`: 음성 판정 기준 (0~1, 기본값 `0.6`). 값을 높이면 잡음을 더 엄격하게 걸러내지만 작거나 조용한 발화가 누락될 수 있습니다.
- `--overwrite`: 기존 SRT 파일 덮어쓰기

Whisper에 오디오를 넘기기 전에 VAD가 음성 구간을 골라냅니다. 비음성 구간은 인식 대상에서 제외해 잡음에서 생기는 할루시네이션 자막을 줄입니다. VAD 모델(`ggml-silero-v6.2.0.bin`, 약 864 KB)은 Whisper 모델과 함께 `~/Library/Application Support/KoreanSRT/models/`에 저장됩니다. 이전 구간의 텍스트 문맥도 사용하지 않아, 잡음 구간에서 생긴 오인식이 이후 대사로 이어지는 현상을 줄입니다.

## 문제 해결

- `whisper-cli` 또는 `ffmpeg`를 찾을 수 없다는 오류가 나면 `./setup.sh`를 다시 실행하세요.
- 출력 자막의 품질은 녹음 상태, 배경 소음, 사투리, 화자 겹침에 영향을 받습니다.
- 모델 파일은 로컬에 남습니다. 삭제하려면 `~/Library/Application Support/KoreanSRT/models/` 폴더를 지우세요.

## 기반 프로젝트

음성 인식은 [whisper.cpp](https://github.com/ggml-org/whisper.cpp), MP3 변환은 [FFmpeg](https://ffmpeg.org/)를 사용합니다. Whisper 모델 가중치는 [Hugging Face의 ggml-org 저장소](https://huggingface.co/ggerganov/whisper.cpp)에서 내려받습니다.
