# 스피커 트리거 앱

ROS 2 Humble 모션 제어 시스템(`motion_web`)의 DDS 트리거를 **구독만** 하여
모션 시작 시점에 음성 파일을 재생하는 웹 앱이다.

기존 3대 PC의 연동에 일절 관여하지 않는다. DDS 발행은 0건이며,
이 PC가 꺼져 있거나 고장 나도 3대의 모션 실행은 영향을 받지 않는다.

설계 근거와 대상 시스템 분석 결과는 [DESIGN.md](DESIGN.md)에 정리되어 있다.

## 기능

- **연동 모드** — `/motion_group/command` 를 구독해 `start_at` 명령에 반응. 사이클마다 재생
- **단독 모드** — DDS 없이 반복 횟수·간격을 지정해 재생
- 재생 시점 오프셋 조절 (-10.0 ~ +10.0초, 음수면 모션보다 먼저 재생)
- 웹 UI (동일 네트워크의 다른 PC·폰에서 접속 가능), 볼륨·일시정지·음원 업로드
- 모노 wav 자동 스테레오 변환 (양쪽 출력)

## 요구 환경

- Ubuntu 22.04 / Python 3.10
- ROS 2 Humble (연동 모드에만 필요 — 없어도 단독 모드와 웹 UI는 동작)
- `~/ros2_ws` 에 `motion_coordination_interfaces` 빌드 완료
- ALSA (`aplay`)

## 설치

```bash
git clone <이 저장소> ~/speaker_app
cd ~/speaker_app
pip3 install -r requirements.txt
```

메시지 정의 빌드 (연동 모드용):

```bash
cd ~/ros2_ws
colcon build --packages-select motion_coordination_interfaces
```

음성 파일을 `sounds/` 에 넣고 `config/speaker.yaml` 의 `audio.file_path` 를 맞춘다.
(용량 때문에 wav 파일은 저장소에 포함하지 않는다. 웹 UI에서 업로드해도 된다.)

## 실행

```bash
./run.sh
```

브라우저에서 `http://<이 PC의 IP>:8100` 접속.

## 자동 시작 (systemd user service)

```bash
mkdir -p ~/.config/systemd/user
cp deploy/speaker-app.service ~/.config/systemd/user/
systemctl --user daemon-reload
systemctl --user enable --now speaker-app
sudo loginctl enable-linger $USER   # 로그아웃 후에도 유지
```

## 구조

```
backend/
  main.py           진입점 — 설정 로드 → 앱 조립 → uvicorn 기동
  api.py            REST 엔드포인트
  state.py          앱 상태 단일 소스 + 락
  config.py         speaker.yaml 로드/저장
  player.py         재생 엔진 (aplay 서브프로세스)
  standalone.py     단독 모드 반복 스케줄러
  dds_listener.py   rclpy 를 import 하는 유일한 파일
  audio_prep.py     모노 → 스테레오 변환
  volume.py         ALSA 믹서 제어
  sysinfo.py        시스템 정보
  logbuf.py         최근 100건 링버퍼
frontend/           순수 HTML/JS, 빌드 도구 없음
config/speaker.yaml 설정 영속
deploy/             systemd 유닛
```

`dds_listener.py` 만 `rclpy` 를 import 한다. 나머지는 ROS를 전혀 모르므로,
ROS가 없거나 DDS가 붙지 않아도 재생과 웹 UI는 정상 동작한다.
