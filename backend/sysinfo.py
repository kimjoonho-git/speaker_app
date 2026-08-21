"""시스템 기본 정보 수집. 웹 UI 표시용이며 앱 동작에는 관여하지 않는다."""
import os
import platform
import socket
import subprocess
import wave

APP_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _lan_ip():
    """기본 경로로 나가는 인터페이스의 주소. 실제 패킷은 보내지 않는다."""
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        sock.connect(("8.8.8.8", 80))
        return sock.getsockname()[0]
    except OSError:
        return "127.0.0.1"
    finally:
        sock.close()


def _iface():
    try:
        out = subprocess.run(["ip", "route", "get", "8.8.8.8"],
                             capture_output=True, text=True, timeout=2).stdout
        parts = out.split()
        if "dev" in parts:
            return parts[parts.index("dev") + 1]
    except Exception:
        pass
    return "-"


def _format_duration(seconds):
    seconds = int(seconds)
    if seconds >= 3600:
        return "%d시간 %d분 %d초" % (seconds // 3600, (seconds % 3600) // 60, seconds % 60)
    if seconds >= 60:
        return "%d분 %d초" % (seconds // 60, seconds % 60)
    return "%d초" % seconds


def format_duration(seconds):
    return _format_duration(seconds)


def wav_info(path):
    """음원 길이/포맷. 사이클 주기와 비교할 때 쓰인다."""
    if not path or not os.path.isfile(path):
        return None
    try:
        with wave.open(path, "rb") as w:
            frames = w.getnframes()
            rate = w.getframerate() or 1
            info = {
                "duration_sec": frames / float(rate),
                "duration_text": _format_duration(frames / float(rate)),
                "sample_rate": rate,
                "channels": w.getnchannels(),
                "bit_depth": w.getsampwidth() * 8,
            }
    except Exception as exc:
        return {"error": str(exc)}
    try:
        info["size_mb"] = round(os.path.getsize(path) / (1024 * 1024), 1)
    except OSError:
        info["size_mb"] = 0
    return info


def collect(port):
    """앱 기동 시 한 번만 모으면 되는 정보."""
    ip = _lan_ip()
    return {
        "hostname": socket.gethostname(),
        "web_url": "http://%s:%d" % (ip, port),
        "ip": ip,
        "interface": _iface(),
        "app_dir": APP_DIR,
        "config_path": os.path.join(APP_DIR, "config", "speaker.yaml"),
        "sounds_dir": os.path.join(APP_DIR, "sounds"),
        "ros_workspace": os.path.expanduser("~/ros2_ws"),
        "ros_distro": os.environ.get("ROS_DISTRO", "-"),
        "rmw": os.environ.get("RMW_IMPLEMENTATION", "rmw_fastrtps_cpp (기본값)"),
        "os": "%s %s" % (platform.system(), platform.release()),
        "python": platform.python_version(),
        "subscribe": "/motion_group/command, /motion_group/event",
        "publish": "없음 (구독 전용)",
    }
