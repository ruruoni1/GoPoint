# -*- coding: utf-8 -*-
import locale
import sys
import os
import json
import collections
import math
import shutil
import webbrowser # For opening links
from pathlib import Path

# ... Imports ...
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QSystemTrayIcon, 
                             QMenu, QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                             QSlider, QComboBox, QPushButton, QColorDialog, QCheckBox,
                             QListWidget, QListWidgetItem, QInputDialog, QMessageBox,
                             QStyledItemDelegate, QStyle, QStyleOptionViewItem, QAbstractItemView,
                             QTextBrowser)
from PyQt6.QtCore import Qt, QTimer, QPoint, QSize, QEvent, QObject, pyqtSignal, QPointF, QRect
from PyQt6.QtGui import (QAction, QIcon, QColor, QPainter, QPen, QBrush, 
                         QPolygonF, QCursor, QFont, QLinearGradient)
from PyQt6.QtNetwork import QLocalServer, QLocalSocket

def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.dirname(os.path.abspath(__file__))

    return os.path.join(base_path, relative_path)

import winreg # For Registry access
import urllib.request
import urllib.error
import urllib.parse
import threading
import tempfile
import subprocess
import uuid

APP_VERSION = "1.0.16"
RELEASE_ASSET_NAME = "GoPoint.exe"
GITHUB_LATEST_RELEASE_URL = "https://api.github.com/repos/ruruoni1/GoPoint/releases/latest"
LOCAL_UPDATE_TEST_DIR_NAME = "update-test"
LOCAL_UPDATE_MANIFEST_NAME = "update.json"
STARTUP_REGISTRY_KEY = r"Software\Microsoft\Windows\CurrentVersion\Run"
STARTUP_APP_NAME = "GoPoint"
STARTUP_LAUNCH_ARGUMENT = "--startup"
SINGLE_INSTANCE_MESSAGE_SHOW_SETTINGS = "show-settings"
SINGLE_INSTANCE_MESSAGE_NOOP = "noop"
NORMAL_FRAME_INTERVAL_MS = 16
NORMAL_SMOOTHING_ITERATIONS = 2
TOPMOST_REFRESH_INTERVAL_MS = 1200
TRAIL_SETTLE_EPSILON = 0.75
LOW_SPEC_LEVEL_DEFAULT = 0
LOW_SPEC_LEVEL_LEGACY_ENABLED = 2
SINGLE_INSTANCE_SERVER = None


def is_packaged_build():
    return bool(getattr(sys, "frozen", False) or "__compiled__" in globals())


def get_packaged_executable_path():
    if not is_packaged_build():
        return None

    # Nuitka onefile exposes the original launcher path through sys.argv[0].
    exe_path = os.path.abspath(sys.argv[0]) if sys.argv and sys.argv[0] else None
    if exe_path:
        return exe_path

    exe_path = os.path.abspath(sys.executable)
    if exe_path:
        return exe_path
    return None


def get_source_script_path():
    return os.path.abspath(__file__)


def get_application_base_dir():
    base_path = get_packaged_executable_path() if is_packaged_build() else get_source_script_path()
    if base_path:
        return os.path.dirname(base_path)
    return os.getcwd()


def get_single_instance_server_name():
    if is_packaged_build():
        return "GoPoint-packaged-instance"
    return "GoPoint-source-instance"


def get_startup_runtime_path():
    if is_packaged_build():
        return get_packaged_executable_path()

    runtime_path = os.path.abspath(sys.executable)
    if not runtime_path:
        return None

    runtime_dir = os.path.dirname(runtime_path)
    runtime_name = os.path.basename(runtime_path).lower()
    pythonw_path = os.path.join(runtime_dir, "pythonw.exe")
    if runtime_name == "python.exe" and os.path.exists(pythonw_path):
        return pythonw_path
    return runtime_path


def is_startup_launch():
    startup_args = {STARTUP_LAUNCH_ARGUMENT, "/startup", "-startup"}
    return any(arg.lower() in startup_args for arg in sys.argv[1:])


def normalize_windows_path(path):
    if not path:
        return None
    return os.path.normcase(os.path.normpath(os.path.abspath(path)))


def extract_executable_path_from_command(command):
    if not command:
        return None

    command = command.strip()
    if not command:
        return None

    if command.startswith('"'):
        end_quote = command.find('"', 1)
        if end_quote > 1:
            return command[1:end_quote]

    lower_command = command.lower()
    exe_index = lower_command.find(".exe")
    if exe_index != -1:
        return command[:exe_index + 4]

    return command.split(" ", 1)[0]


def get_startup_command():
    runtime_path = get_startup_runtime_path()
    if not runtime_path:
        return None

    if is_packaged_build():
        return f'"{runtime_path}" {STARTUP_LAUNCH_ARGUMENT}'

    script_path = get_source_script_path()
    if not script_path:
        return None
    return f'"{runtime_path}" "{script_path}" {STARTUP_LAUNCH_ARGUMENT}'


def get_registered_startup_command():
    try:
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, STARTUP_REGISTRY_KEY, 0, winreg.KEY_READ)
        value, _ = winreg.QueryValueEx(key, STARTUP_APP_NAME)
        winreg.CloseKey(key)
        return value
    except FileNotFoundError:
        return None
    except OSError:
        return None


def is_startup_registered_for_current_build():
    current_command = get_startup_command()
    registered_command = get_registered_startup_command()
    if not current_command or not registered_command:
        return False

    if is_packaged_build():
        current_exe = get_packaged_executable_path()
        registered_exe = extract_executable_path_from_command(registered_command)
        return normalize_windows_path(registered_exe) == normalize_windows_path(current_exe)

    return registered_command.strip() == current_command


def set_startup_registry_enabled(enabled):
    try:
        key = winreg.CreateKeyEx(winreg.HKEY_CURRENT_USER, STARTUP_REGISTRY_KEY, 0, winreg.KEY_SET_VALUE)
        if enabled:
            startup_command = get_startup_command()
            if not startup_command:
                winreg.CloseKey(key)
                return False
            winreg.SetValueEx(key, STARTUP_APP_NAME, 0, winreg.REG_SZ, startup_command)
        else:
            try:
                winreg.DeleteValue(key, STARTUP_APP_NAME)
            except FileNotFoundError:
                pass
        winreg.CloseKey(key)
        return True
    except OSError as e:
        print(f"Registry Error: {e}")
        return False


def repair_startup_registry_entry():
    current_command = get_startup_command()
    registered_command = get_registered_startup_command()
    if not current_command or not registered_command:
        return

    if registered_command.strip() == current_command:
        return

    if is_packaged_build():
        current_exe = get_packaged_executable_path()
        registered_exe = extract_executable_path_from_command(registered_command)
        if normalize_windows_path(registered_exe) != normalize_windows_path(current_exe):
            return
        set_startup_registry_enabled(True)


def notify_existing_instance(server_name, message):
    socket = QLocalSocket()
    socket.connectToServer(server_name)
    if not socket.waitForConnected(500):
        return False

    payload = message.encode("utf-8")
    socket.write(payload)
    socket.flush()
    socket.waitForBytesWritten(500)
    socket.disconnectFromServer()
    return True


def set_single_instance_server(server):
    global SINGLE_INSTANCE_SERVER
    SINGLE_INSTANCE_SERVER = server


def release_single_instance_server():
    if SINGLE_INSTANCE_SERVER:
        SINGLE_INSTANCE_SERVER.close()


def resume_single_instance_server():
    if SINGLE_INSTANCE_SERVER:
        return SINGLE_INSTANCE_SERVER.start()
    return False


def _path_to_file_uri(path):
    return Path(os.path.abspath(path)).resolve().as_uri()


def normalize_update_reference(reference, base_url=None):
    if not reference:
        return None

    reference = reference.strip()
    if not reference:
        return None

    parsed = urllib.parse.urlparse(reference)
    if parsed.scheme in ("http", "https", "file"):
        return reference

    if os.path.isabs(reference):
        return _path_to_file_uri(reference)

    if base_url:
        return urllib.parse.urljoin(base_url, reference.replace("\\", "/"))

    return _path_to_file_uri(reference)


def append_cache_bust(url, token):
    parsed = urllib.parse.urlparse(url)
    if parsed.scheme not in ("http", "https"):
        return url

    separator = "&" if parsed.query else "?"
    return f"{url}{separator}t={token}"


def get_configured_update_manifest_url(cache_bust_token):
    override_reference = os.environ.get("GOPOINT_UPDATE_MANIFEST", "").strip()
    if override_reference:
        return normalize_update_reference(override_reference), "override"

    local_manifest_path = os.path.join(
        get_application_base_dir(),
        LOCAL_UPDATE_TEST_DIR_NAME,
        LOCAL_UPDATE_MANIFEST_NAME,
    )
    if os.path.exists(local_manifest_path):
        return _path_to_file_uri(local_manifest_path), "local"

    return append_cache_bust(GITHUB_LATEST_RELEASE_URL, cache_bust_token), "github"


def load_update_manifest_json(manifest_url, timeout, headers=None):
    parsed = urllib.parse.urlparse(manifest_url)
    if parsed.scheme in ("http", "https"):
        request = urllib.request.Request(manifest_url, headers=headers or {})
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return json.loads(response.read().decode())

    with urllib.request.urlopen(manifest_url, timeout=timeout) as response:
        return json.loads(response.read().decode())


def open_update_download_stream(download_url, timeout, headers=None):
    parsed = urllib.parse.urlparse(download_url)
    if parsed.scheme in ("http", "https"):
        request = urllib.request.Request(download_url, headers=headers or {})
        return urllib.request.urlopen(request, timeout=timeout)

    return urllib.request.urlopen(download_url, timeout=timeout)


def parse_update_manifest(data, manifest_url, cache_bust_token):
    result = {"latest_version": None, "asset_url": None, "error": None}

    if "assets" in data or "tag_name" in data:
        latest_tag = data.get("tag_name", "")
        result["latest_version"] = latest_tag.lstrip("v")

        for asset in data.get("assets", []):
            if asset.get("name") == RELEASE_ASSET_NAME:
                result["asset_url"] = append_cache_bust(asset.get("browser_download_url"), cache_bust_token)
                break

        if result["latest_version"] and not result["asset_url"]:
            result["error"] = f"Release asset '{RELEASE_ASSET_NAME}' was not found."
        return result

    latest_version = data.get("version") or data.get("latest_version") or data.get("tag_name") or ""
    result["latest_version"] = str(latest_version).lstrip("v") if latest_version else None

    asset_reference = data.get("url") or data.get("asset_url")
    if asset_reference:
        asset_url = normalize_update_reference(asset_reference, manifest_url)
        result["asset_url"] = append_cache_bust(asset_url, cache_bust_token)

    if result["latest_version"] and not result["asset_url"]:
        result["error"] = "Update manifest is missing a download URL."

    return result


class SingleInstanceServer(QObject):
    def __init__(self, server_name, activation_callback, parent=None):
        super().__init__(parent)
        self.server_name = server_name
        self.activation_callback = activation_callback
        self.pending_activation = False
        self.server = QLocalServer(self)
        self.server.newConnection.connect(self._handle_new_connection)

    def start(self):
        if self.server.listen(self.server_name):
            return True

        QLocalServer.removeServer(self.server_name)
        return self.server.listen(self.server_name)

    def close(self):
        self.server.close()
        QLocalServer.removeServer(self.server_name)

    def set_activation_callback(self, activation_callback):
        self.activation_callback = activation_callback
        if self.pending_activation and self.activation_callback:
            self.pending_activation = False
            QTimer.singleShot(0, self.activation_callback)

    def _handle_new_connection(self):
        while self.server.hasPendingConnections():
            socket = self.server.nextPendingConnection()
            socket.readyRead.connect(lambda s=socket: self._process_socket(s))
            socket.disconnected.connect(socket.deleteLater)
            if socket.bytesAvailable():
                self._process_socket(socket)

    def _process_socket(self, socket):
        message = bytes(socket.readAll()).decode("utf-8", errors="ignore").strip()
        if message == SINGLE_INSTANCE_MESSAGE_SHOW_SETTINGS:
            if self.activation_callback:
                QTimer.singleShot(0, self.activation_callback)
            else:
                self.pending_activation = True
        socket.disconnectFromServer()


def clamp_low_spec_level(level):
    try:
        return max(0, min(3, int(level)))
    except Exception:
        return LOW_SPEC_LEVEL_DEFAULT


def get_performance_preset(level, preview=False):
    level = clamp_low_spec_level(level)
    overlay_presets = {
        0: {"interval_ms": NORMAL_FRAME_INTERVAL_MS, "smoothing_iterations": NORMAL_SMOOTHING_ITERATIONS},
        1: {"interval_ms": 18, "smoothing_iterations": 2},
        2: {"interval_ms": 22, "smoothing_iterations": 2},
        3: {"interval_ms": 28, "smoothing_iterations": 1},
    }
    preview_presets = {
        0: {"interval_ms": NORMAL_FRAME_INTERVAL_MS, "smoothing_iterations": NORMAL_SMOOTHING_ITERATIONS},
        1: {"interval_ms": 24, "smoothing_iterations": 2},
        2: {"interval_ms": 33, "smoothing_iterations": 1},
        3: {"interval_ms": 45, "smoothing_iterations": 1},
    }
    return (preview_presets if preview else overlay_presets)[level]


TRANSLATIONS = {
    "ko": {
        "title": "GoPoint (고포인트)",
        "run_startup": "윈도우 시작 시 자동 실행",
        "update_history": "업데이트 내역 (History)",
        "update_title": "업데이트 기록",
        "close": "닫기",
        "preview": "미리보기",
        "profile": "프로파일",
        "save": "저장",
        "delete": "삭제",
        "trail_style": "트레일 스타일",
        "color_palette": "색상 팔레트",
        "reverse_order": "순서 반전",
        "reset": "초기화",
        "add_color": "색상 추가 (+)",
        "remove_color": "색상 제거 (-)",
        "width": "시작 두께",
        "length": "트레일 길이",
        "fade_out": "투명도 감소 효과 (Fade Out)",
        "quit": "프로그램 종료",
        "update_available": "업데이트 알림",
        "update_msg": "새로운 버전({new_version})이 출시되었습니다.\n현재 버전: {current_version}\n\n지금 업데이트 하시겠습니까?",
        "update_downloading": "업데이트 다운로드 중...",
        "update_error": "업데이트 정보를 가져오는데 실패했습니다.",
        "update_latest": "현재 최신 버전을 사용 중입니다.",
        "warn_delete_default": "기본(Default) 프로파일은 삭제할 수 없습니다.",
        "confirm_delete": "'{name}' 프로파일을 삭제하시겠습니까?",
        "dlg_save_title": "프로파일 저장",
        "dlg_save_label": "나만의 프로파일 이름:",
        "warn_min_color": "최소 1개의 색상은 있어야 합니다.",
        "language": "언어 (Language)",
        "confirm_delete_title": "삭제 확인",
        "warning": "경고",
        "style_constant": "실선 (Constant)",
        "style_dots": "점 (Dots)",
        "style_tapered": "혜성 (Tapered)",
        "developer": "개발자: 고버스 (GoVerseTV)",
        "youtube": "유튜브 채널 방문하기",
        "contact": "문의: <a href='mailto:ruruoni1@gmail.com' style='color: #4da6ff;'>ruruoni1@gmail.com</a>",
        "about_btn": "앱 정보 (About)",
        "about_msg": """<h3>\U0001f680 GoPoint 개발 이야기</h3>
<p>안녕하세요! <b>고버스TV</b>입니다. \U0001f60e</p>
<p>튜토리얼 영상을 만들 때마다, 시청자분들이<br>
제 마우스 커서를 놓치지 않게 하려고 늘 고민했었어요.</p>
<p>기존 프로그램들도 훌륭하지만,<br>
<b>"좀 더 부드럽고! 더 직관적인!"</b> 느낌을 원해서<br>
이 <b>GoPoint</b>를 직접 만들게 되었습니다. \u2728</p>
<p>여러분의 화면 속 중요한 순간이 더 빛나도록<br>
<b>GoPoint</b>가 확실하게 도와드릴게요! \U0001f4aa</p>
<p>더 많은 꿀팁과 영상 이야기는<br>
제 채널에서 만나요! \U0001f4fa</p>
<p>\U0001f449 <a href='https://www.youtube.com/@GOVERSE82' style='color: #4da6ff;'>유튜브 '고버스TV' 놀러 가기</a></p>
<p>\U0001f4ac <a href='https://open.kakao.com/o/gN0Fx9Df' style='color: #FEE500; text-decoration: none;'>카카오톡 오픈채팅방 참여하기</a></p>""",
        "apply": "적용",
        "startup_applied": "자동 실행 설정이 적용되었습니다.",
        "startup_enabled": "자동 실행이 등록되었습니다.",
        "startup_disabled": "자동 실행이 해제되었습니다.",
        "startup_failed": "자동 실행 설정을 적용하지 못했습니다.",
        "changelog": """<h2>Ver 1.0.16 (2026-03-16)</h2>
<ul>
<li><b>중복 실행 방지:</b> 트레이에 이미 실행 중인 인스턴스가 있으면 새 창을 띄우지 않고 기존 설정창만 다시 엽니다.</li>
<li><b>로컬 업데이트 테스트 지원:</b> <code>update-test/update.json</code> 또는 <code>GOPOINT_UPDATE_MANIFEST</code>로 GitHub 없이 자동 업데이트를 시험할 수 있습니다.</li>
</ul>

<h2>Ver 1.0.15 (2026-03-16)</h2>
<ul>
<li><b>시작프로그램 경로 수정:</b> Nuitka onefile 빌드가 임시 <code>python.exe</code>를 등록하지 않고 원래 <code>GoPoint.exe</code> 경로를 사용하도록 수정했습니다.</li>
<li><b>소스 실행 등록 지원:</b> <code>python GoPoint.py</code>로 실행한 경우에도 시작프로그램 등록이 가능하도록 보완했습니다.</li>
</ul>

<h2>Ver 1.0.14 (2026-03-13)</h2>
<ul>
<li><b>중요:</b> <code>v1.0.12</code> 사용자는 자동 업데이트 판별 오류 때문에 이번 한 번은 최신 설치 파일을 수동으로 받아 설치해야 합니다.</li>
<li><b>패키지 EXE 판별 수정:</b> Nuitka로 빌드된 실행 파일도 정식 패키지 EXE로 인식하도록 수정해 자동 업데이트와 시작프로그램 등록이 정상 동작하게 했습니다.</li>
</ul>

<h2>Ver 1.0.13 (2026-03-13)</h2>
<ul>
<li><b>성능 최적화:</b> 마우스가 멈춘 상태에서는 불필요한 다시 그리기를 줄이고, topmost 재적용 빈도를 낮춰 오래된 PC에서 CPU/GPU 점유를 줄였습니다.</li>
<li><b>저사양 모드 단계 추가:</b> 저사양 환경에서 부드러움과 자원 사용량 사이를 조절할 수 있도록 3단계 저사양 모드를 추가했습니다.</li>
</ul>

<h2>Ver 1.0.12 (2026-03-09)</h2>
<ul>
<li><b>업데이트 자산 검증 강화:</b> 자동 업데이트가 GitHub 릴리즈의 임의 EXE가 아니라 <code>GoPoint.exe</code> 자산만 선택하도록 제한했습니다.</li>
<li><b>시작 프로그램 경로 안전성 개선:</b> Windows 시작 프로그램 레지스트리에 실행 경로를 따옴표로 저장해 공백 경로 해석 문제를 줄였습니다.</li>
</ul>

<h2>Ver 1.0.11 (2026-03-09)</h2>
<ul>
<li><b>C++ 단일 파일 배포 전환:</b> 배포용 실행 파일을 Nuitka 기반 단일 EXE로 전환하여, 1.0.10 사용자가 자동 업데이트로 그대로 전환될 수 있도록 준비했습니다.</li>
<li><b>릴리즈 파일명 정리:</b> GitHub 릴리즈 자산은 항상 <code>GoPoint.exe</code>로 제공하고, 로컬 빌드 산출물은 버전명 파일도 함께 생성하도록 정리했습니다.</li>
</ul>

<h2>Ver 1.0.10 (2026-03-08)</h2>
<ul>
<li><b>혜성 머리 모양 개선:</b> Tapered 스타일의 시작 부분이 잘려 보이지 않도록 원형 헤드로 마감해 더 자연스럽게 보이도록 조정했습니다.</li>
</ul>

<h2>Ver 1.0.9 (2026-03-08)</h2>
<ul>
<li><b>자동 업데이트 안정성 개선:</b> 시작 시 자동 확인과 수동 확인이 겹쳐도 결과가 섞이지 않도록 업데이트 요청 흐름을 정리했습니다.</li>
<li><b>업데이트 완료 처리 보강:</b> 새 실행 파일 교체 후 재실행과 종료 순서를 안정화해 업데이트가 중간에 멈추는 문제를 줄였습니다.</li>
<li><b>설정 보존 개선:</b> 사용자가 수정한 Default 프로필이 재시작 시 기본값으로 덮어써지지 않도록 수정했습니다.</li>
</ul>

<h2>Ver 1.0.8 (2026-03-01)</h2>
<ul>
<li><b>업데이트 방식 혁신 (Rename-and-Replace):</b> Windows의 파일 잠금을 우회하는 보존 및 교체 방식을 도입하여, 업데이트 시 발생하던 DLL 오류와 권한 문제를 근본적으로 해결했습니다.</li>
<li><b>자동 찌꺼기 청소:</b> 업데이트 후 남은 이전 버전 파일(.old)을 앱 시작 시 자동으로 정리합니다.</li>
</ul>

<h2>Ver 1.0.7 (2026-03-01)</h2>
<ul>
<li><b>자동 업데이트 기능 도입:</b> 새로운 버전 출시 시 앱 내에서 즉시 확인하고 업데이트 가능</li>
<li>트레이 메뉴 및 설정 하단에 '업데이트 확인' 버튼 추가</li>
</ul>

<h2>Ver 1.0.6 (2026-03-01)</h2>
<ul>
<li>마우스 커서 트래킹 알고리즘 개선 (물리 스프링 효과 적용으로 샘플처럼 완벽히 부드러운 꼬리 구현)</li>
</ul>

<h2>Ver 1.0.5</h2>
<ul>
<li>프로그램 버전 정보 표시 (상단 제목)</li>
<li>자동 실행 '적용' 버튼 위치 개선</li>
</ul>

<h2>Ver 1.0.4</h2>
<ul>
<li>윈도우 시작 시 자동 실행 옵션 추가</li>
<li>업데이트 내역(History) 메뉴 추가</li>
<li>작업 표시줄 가림 현상 완벽 해결 (System Z-Order)</li>
</ul>

<h2>Ver 1.0.3</h2>
<ul>
<li>시스템 트레이 우클릭 오동작 수정 (좌클릭만 설정창 열림)</li>
<li>EXE 아이콘 리소스 누락 문제 해결</li>
</ul>

<h2>Ver 1.0.2</h2>
<ul>
<li>연락처 및 오픈카톡 링크 추가</li>
<li>프로그램 용량 최적화 (Clean Build)</li>
</ul>

<h2>Ver 1.0.1</h2>
<ul>
<li>트레일 곡선 스무딩(Smoothing) 알고리즘 적용</li>
<li>종료 버튼 동작 개선 (트레이 최소화)</li>
</ul>

<h2>Ver 1.0.0</h2>
<ul>
<li>GoPoint 초기 출시</li>
</ul>"""
    },
    "en": {
        "title": "GoPoint",
        "run_startup": "Run on Windows Startup",
        "update_history": "Update History",
        "update_title": "Update Log",
        "close": "Close",
        "preview": "Preview",
        "profile": "Profile",
        "save": "Save",
        "delete": "Delete",
        "trail_style": "Trail Style",
        "color_palette": "Color Palette",
        "reverse_order": "Reverse",
        "reset": "Reset",
        "add_color": "Add Color (+)",
        "remove_color": "Remove Color (-)",
        "width": "Start Width",
        "length": "Trail Length",
        "fade_out": "Fade Out Effect",
        "low_spec_mode": "Low-Spec Mode",
        "quit": "Quit Program",
        "update_available": "Update Available",
        "update_msg": "A new version ({new_version}) is available.\nCurrent version: {current_version}\n\nWould you like to update now?",
        "update_downloading": "Downloading update...",
        "update_error": "Failed to check for updates.",
        "update_latest": "You are using the latest version.",
        "warn_delete_default": "Cannot delete 'Default' profile.",
        "confirm_delete": "Delete profile '{name}'?",
        "dlg_save_title": "Save Profile",
        "dlg_save_label": "Profile Name:",
        "warn_min_color": "At least one color is required.",
        "language": "Language",
        "confirm_delete_title": "Delete Confirmation",
        "warning": "Warning",
        "style_constant": "Constant",
        "style_dots": "Dots",
        "style_tapered": "Tapered",
        "developer": "Dev: Goverse (GoVerseTV)",
        "youtube": "Visit YouTube Channel",
        "contact": "Contact: ruruoni1@gmail.com",
        "about_btn": "About App",
        "about_msg": """<h3>\U0001f680 About GoPoint</h3>
<p>Hello! This is <b>GoVerseTV</b>. \U0001f60e</p>
<p>Whenever I made tutorial videos, I worried about<br>
viewers losing track of my mouse cursor.</p>
<p>Existing programs were good, but I wanted something<br>
<b>"Smoother! And more Intuitive!"</b><br>
So I decided to build <b>GoPoint</b> myself. \u2728</p>
<p><b>GoPoint</b> is here to help your screen's<br>
important moments shine brighter! \U0001f4aa</p>
<p>Meet me on my channel for more tips and stories! \U0001f4fa</p>
<p>\U0001f449 <a href='https://www.youtube.com/@GOVERSE82' style='color: #4da6ff;'>Visit 'GoVerseTV' on YouTube</a></p>
<p>\U0001f4ac <a href='https://open.kakao.com/o/gN0Fx9Df' style='color: #FEE500; text-decoration: none;'>Join KakaoTalk Open Chat</a></p>""",
        "apply": "Apply",
        "startup_applied": "Startup setting applied.",
        "startup_enabled": "Startup registration enabled.",
        "startup_disabled": "Startup registration disabled.",
        "startup_failed": "Failed to apply the startup setting.",
        "changelog": """<h2>Ver 1.0.16 (2026-03-16)</h2>
<ul>
<li><b>Duplicate launch prevention:</b> When an instance is already running in the tray, launching the EXE again reopens the existing settings window instead of starting another copy.</li>
<li><b>Local update test support:</b> Auto-update can now use <code>update-test/update.json</code> or <code>GOPOINT_UPDATE_MANIFEST</code> for non-GitHub test runs.</li>
</ul>

<h2>Ver 1.0.15 (2026-03-16)</h2>
<ul>
<li><b>Startup path fix:</b> Nuitka onefile builds now register the original <code>GoPoint.exe</code> path instead of a temporary <code>python.exe</code>.</li>
<li><b>Source-run support:</b> Startup registration now also works when the app is launched with <code>python GoPoint.py</code>.</li>
</ul>

<h2>Ver 1.0.14 (2026-03-13)</h2>
<ul>
<li><b>Important:</b> <code>v1.0.12</code> users need a one-time manual install of the latest build because the auto-update detection in v1.0.12 is broken.</li>
<li><b>Packaged EXE detection fix:</b> Nuitka-built executables are now recognized as packaged builds so auto-update and startup registration work correctly.</li>
</ul>

<h2>Ver 1.0.13 (2026-03-13)</h2>
<ul>
<li><b>Performance optimizations:</b> Reduced redundant repaints while the cursor is idle and stopped forcing topmost every frame to lower CPU/GPU load on older PCs.</li>
<li><b>Tiered low-spec mode:</b> Added three low-spec levels so users can trade smoothness for lower resource usage.</li>
</ul>

<h2>Ver 1.0.12 (2026-03-09)</h2>
<ul>
<li><b>Safer update asset selection:</b> Auto-update now accepts only the <code>GoPoint.exe</code> release asset instead of the first EXE it finds.</li>
<li><b>Quoted startup path:</b> The Windows startup registry entry now stores the executable path with quotes to avoid path parsing issues.</li>
</ul>

<h2>Ver 1.0.11 (2026-03-09)</h2>
<ul>
<li><b>C++ single-file distribution:</b> Switched the release build to a Nuitka-generated single EXE so 1.0.10 users can migrate through the existing auto-updater.</li>
<li><b>Stable release asset naming:</b> GitHub releases now ship <code>GoPoint.exe</code> consistently, while local builds also keep a versioned copy.</li>
</ul>

<h2>Ver 1.0.10 (2026-03-08)</h2>
<ul>
<li><b>Round comet head:</b> Refined the Tapered style so the leading edge is rounded instead of looking clipped.</li>
</ul>

<h2>Ver 1.0.9 (2026-03-08)</h2>
<ul>
<li><b>Auto-update stability:</b> Serialized update checks so startup checks and manual checks no longer race or show mixed results.</li>
<li><b>Safer update completion:</b> Stabilized the restart-and-exit sequence after replacing the executable so updates finish cleanly.</li>
<li><b>Profile persistence fix:</b> Prevented customized Default profiles from being overwritten on the next launch.</li>
</ul>

<h2>Ver 1.0.8 (2026-03-01)</h2>
<ul>
<li><b>Improved Update Strategy (Rename-and-Replace):</b> Introduced a robust mechanism to bypass file lock issues on Windows, eliminating DLL and permission errors during updates.</li>
<li><b>Automated Cleanup:</b> Temporary update files are now automatically cleaned up on startup.</li>
</ul>

<h2>Ver 1.0.7 (2026-03-01)</h2>
<ul>
<li><b>Auto-Updater:</b> Check for and install new versions directly within the app.</li>
<li>Added 'Check for Updates' button in tray menu and settings.</li>
</ul>

<h2>Ver 1.0.6 (2026-03-01)</h2>
<ul>
<li>Improved Mouse Cursor Tracking (Applied spring physics for perfectly smooth, continuous trails like the preview animation)</li>
</ul>

<h2>Ver 1.0.5</h2>
<ul>
<li>Added Version Info Display</li>
<li>Improved Startup Apply Button Position</li>
</ul>

<h2>Ver 1.0.4</h2>
<ul>
<li>Added Run on Startup Option</li>
<li>Added Update History Menu</li>
<li>Fixed System Z-Order (Always on Top)</li>
</ul>

<h2>Ver 1.0.3</h2>
<ul>
<li>Fixed system tray right-click issue</li>
<li>Fixed missing EXE icon resource</li>
</ul>

<h2>Ver 1.0.2</h2>
<ul>
<li>Added Contact & KakaoTalk links</li>
<li>Optimized Program Size</li>
</ul>

<h2>Ver 1.0.1</h2>
<ul>
<li>Applied Trail Smoothing Algorithm</li>
<li>Improved Quit Button Behavior</li>
</ul>

<h2>Ver 1.0.0</h2>
<ul>
<li>GoPoint Initial Release</li>
</ul>"""
    },
    "ja": {
        "title": "GoPoint",
        "run_startup": "Windows起動時に自動実行",
        "update_history": "更新履歴",
        "update_title": "更新ログ",
        "close": "閉じる",
        "preview": "プレビュー",
        "profile": "プロファイル",
        "save": "保存",
        "delete": "削除",
        "trail_style": "トレイルスタイル",
        "color_palette": "カラーパレット",
        "reverse_order": "反転",
        "reset": "リセット",
        "add_color": "色追加 (+)",
        "remove_color": "色削除 (-)",
        "width": "開始幅",
        "length": "トレイル長",
        "fade_out": "フェードアウト効果",
        "quit": "終了",
        "update_available": "アップデートのお知らせ",
        "update_msg": "新しいバージョン({new_version})が利用可能です。\n現在のバージョン: {current_version}\n\n今すぐアップデートしますか？",
        "update_downloading": "アップデートをダウンロード中...",
        "update_error": "アップデート情報の取得に失敗しました。",
        "update_latest": "最新バージョンを使用しています。",
        "warn_delete_default": "「Default」プロファイルは削除できません。",
        "confirm_delete": "プロファイル '{name}' を削除しますか？",
        "dlg_save_title": "プロファイル保存",
        "dlg_save_label": "プロファイル名:",
        "warn_min_color": "最低1つの色が必要です。",
        "language": "言語 (Language)",
        "confirm_delete_title": "削除確認",
        "warning": "警告",
        "style_constant": "実線 (Constant)",
        "style_dots": "点 (Dots)",
        "style_tapered": "彗星 (Tapered)",
        "developer": "開発者: Goverse (GoVerseTV)",
        "youtube": "YouTubeチャンネル",
        "contact": "お問い合わせ: <a href='mailto:ruruoni1@gmail.com' style='color: #4da6ff;'>ruruoni1@gmail.com</a>",
        "about_btn": "About App",
        "about_msg": """<h3>\U0001f680 About GoPoint</h3>
<p>Hello! This is <b>GoVerseTV</b>. \U0001f60e</p>
<p>Whenever I made tutorial videos, I worried about<br>
viewers losing track of my mouse cursor.</p>
<p>Existing programs were good, but I wanted something<br>
<b>"Smoother! And more Intuitive!"</b><br>
So I decided to build <b>GoPoint</b> myself. \u2728</p>
<p><b>GoPoint</b> is here to help your screen's<br>
important moments shine brighter! \U0001f4aa</p>
<p>Meet me on my channel for more tips and stories! \U0001f4fa</p>
<p>\U0001f449 <a href='https://www.youtube.com/@GOVERSE82' style='color: #4da6ff;'>Visit 'GoVerseTV' on YouTube</a></p>"""
    },
    "es": {
        "title": "GoPoint",
        "preview": "Vista Previa",
        "profile": "Perfil",
        "save": "Guardar",
        "delete": "Eliminar",
        "trail_style": "Estilo de Rastro",
        "color_palette": "Paleta de Colores",
        "reverse_order": "Invertir",
        "reset": "Reiniciar",
        "add_color": "Añadir Color (+)",
        "remove_color": "Eliminar Color (-)",
        "width": "Ancho Inicial",
        "length": "Longitud",
        "fade_out": "Efecto de Desvanecimiento",
        "quit": "Salir",
        "warn_delete_default": "No se puede eliminar el perfil 'Default'.",
        "confirm_delete": "¿Eliminar perfil '{name}'?",
        "dlg_save_title": "Guardar Perfil",
        "dlg_save_label": "Nombre del Perfil:",
        "warn_min_color": "Se requiere al menos un color.",
        "language": "Idioma (Language)",
        "confirm_delete_title": "Confirmar Eliminación",
        "warning": "Advertencia",
        "style_constant": "Línea (Constant)",
        "style_dots": "Puntos (Dots)",
        "style_tapered": "Cometa (Tapered)",
        "developer": "Dev: Goverse (GoVerseTV)",
        "youtube": "Canal de YouTube",
        "contact": "Contacto: <a href='mailto:ruruoni1@gmail.com' style='color: #4da6ff;'>ruruoni1@gmail.com</a>",
        "about_btn": "About App",
        "about_msg": """<h3>\U0001f680 About GoPoint</h3>
<p>Hello! This is <b>GoVerseTV</b>. \U0001f60e</p>
<p>Whenever I made tutorial videos, I worried about<br>
viewers losing track of my mouse cursor.</p>
<p>Existing programs were good, but I wanted something<br>
<b>"Smoother! And more Intuitive!"</b><br>
So I decided to build <b>GoPoint</b> myself. \u2728</p>
<p><b>GoPoint</b> is here to help your screen's<br>
important moments shine brighter! \U0001f4aa</p>
<p>Meet me on my channel for more tips and stories! \U0001f4fa</p>
<p>\U0001f449 <a href='https://www.youtube.com/@GOVERSE82' style='color: #4da6ff;'>Visit 'GoVerseTV' on YouTube</a></p>"""
    },
    "zh": {
        "title": "GoPoint",
        "preview": "预览",
        "profile": "配置文件",
        "save": "保存",
        "delete": "删除",
        "trail_style": "轨迹样式",
        "color_palette": "调色板",
        "reverse_order": "反转",
        "reset": "重置",
        "add_color": "添加颜色 (+)",
        "remove_color": "移除颜色 (-)",
        "width": "初始宽度",
        "length": "轨迹长度",
        "fade_out": "淡出效果",
        "quit": "退出程序",
        "warn_delete_default": "无法删除“Default”配置文件。",
        "confirm_delete": "确定删除配置文件 '{name}' 吗？",
        "dlg_save_title": "保存配置文件",
        "dlg_save_label": "配置文件名称:",
        "warn_min_color": "至少需要一种颜色。",
        "language": "语言 (Language)",
        "confirm_delete_title": "删除确认",
        "warning": "警告",
        "style_constant": "实线 (Constant)",
        "style_dots": "点 (Dots)",
        "style_tapered": "彗星 (Tapered)",
        "developer": "开发者: Goverse (GoVerseTV)",
        "youtube": "访问 YouTube 频道",
        "contact": "联系方式: <a href='mailto:ruruoni1@gmail.com' style='color: #4da6ff;'>ruruoni1@gmail.com</a>",
        "about_btn": "About App",
        "about_msg": """<h3>\U0001f680 About GoPoint</h3>
<p>Hello! This is <b>GoVerseTV</b>. \U0001f60e</p>
<p>Whenever I made tutorial videos, I worried about<br>
viewers losing track of my mouse cursor.</p>
<p>Existing programs were good, but I wanted something<br>
<b>"Smoother! And more Intuitive!"</b><br>
So I decided to build <b>GoPoint</b> myself. \u2728</p>
<p><b>GoPoint</b> is here to help your screen's<br>
important moments shine brighter! \U0001f4aa</p>
<p>Meet me on my channel for more tips and stories! \U0001f4fa</p>
<p>\U0001f449 <a href='https://www.youtube.com/@GOVERSE82' style='color: #4da6ff;'>Visit 'GoVerseTV' on YouTube</a></p>"""
    },
    "fr": {
        "title": "GoPoint",
        "preview": "Aperçu",
        "profile": "Profil",
        "save": "Enregistrer",
        "delete": "Supprimer",
        "trail_style": "Style de traînée",
        "color_palette": "Palette de couleurs",
        "reverse_order": "Inverser",
        "reset": "Réinitialiser",
        "add_color": "Ajouter couleur (+)",
        "remove_color": "Supprimer couleur (-)",
        "width": "Largeur",
        "length": "Longueur",
        "fade_out": "Effet de fondu",
        "quit": "Quitter",
        "warn_delete_default": "Impossible de supprimer le profil 'Default'.",
        "confirm_delete": "Supprimer le profil '{name}' ?",
        "dlg_save_title": "Enregistrer le profil",
        "dlg_save_label": "Nom du profil :",
        "warn_min_color": "Au moins une couleur est requise.",
        "language": "Langue (Language)",
        "confirm_delete_title": "Confirmer la suppression",
        "warning": "Avertissement",
        "style_constant": "Ligne (Constant)",
        "style_dots": "Points (Dots)",
        "style_tapered": "Comète (Tapered)",
        "developer": "Dev: Goverse (GoVerseTV)",
        "youtube": "Chaîne YouTube",
        "contact": "Contact: <a href='mailto:ruruoni1@gmail.com' style='color: #4da6ff;'>ruruoni1@gmail.com</a>",
        "about_btn": "About App",
        "about_msg": """<h3>\U0001f680 About GoPoint</h3>
<p>Hello! This is <b>GoVerseTV</b>. \U0001f60e</p>
<p>Whenever I made tutorial videos, I worried about<br>
viewers losing track of my mouse cursor.</p>
<p>Existing programs were good, but I wanted something<br>
<b>"Smoother! And more Intuitive!"</b><br>
So I decided to build <b>GoPoint</b> myself. \u2728</p>
<p><b>GoPoint</b> is here to help your screen's<br>
important moments shine brighter! \U0001f4aa</p>
<p>Meet me on my channel for more tips and stories! \U0001f4fa</p>
<p>\U0001f449 <a href='https://www.youtube.com/@GOVERSE82' style='color: #4da6ff;'>Visit 'GoVerseTV' on YouTube</a></p>"""
    },
    "de": {
        "title": "GoPoint",
        "preview": "Vorschau",
        "profile": "Profil",
        "save": "Speichern",
        "delete": "Löschen",
        "trail_style": "Spurstil",
        "color_palette": "Farbpalette",
        "reverse_order": "Umkehren",
        "reset": "Zurücksetzen",
        "add_color": "Farbe hinzufügen (+)",
        "remove_color": "Farbe entfernen (-)",
        "width": "Breite",
        "length": "Länge",
        "fade_out": "Ausblenden-Effekt",
        "quit": "Beenden",
        "warn_delete_default": "Das Profil 'Default' kann nicht gelöscht werden.",
        "confirm_delete": "Profil '{name}' löschen?",
        "dlg_save_title": "Profil speichern",
        "dlg_save_label": "Profilname:",
        "warn_min_color": "Mindestens eine Farbe ist erforderlich.",
        "language": "Sprache (Language)",
        "confirm_delete_title": "Löschen bestätigen",
        "warning": "Warnung",
        "style_constant": "Linie (Constant)",
        "style_dots": "Punkte (Dots)",
        "style_tapered": "Komet (Tapered)",
        "developer": "Entwickler: Goverse (GoVerseTV)",
        "youtube": "YouTube-Kanal",
        "contact": "Kontakt: <a href='mailto:ruruoni1@gmail.com' style='color: #4da6ff;'>ruruoni1@gmail.com</a>",
        "about_btn": "About App",
        "about_msg": """<h3>🚀 About GoPoint</h3>
<p>Hello! This is <b>GoVerseTV</b>. 😎</p>
<p>Whenever I made tutorial videos, I worried about<br>
viewers losing track of my mouse cursor.</p>
<p>Existing programs were good, but I wanted something<br>
<b>"Smoother! And more Intuitive!"</b><br>
So I decided to build <b>GoPoint</b> myself. ✨</p>
<p><b>GoPoint</b> is here to help your screen's<br>
important moments shine brighter! 💪</p>
<p>Meet me on my channel for more tips and stories! 📺</p>
<p>👉 <a href='https://www.youtube.com/@GOVERSE82' style='color: #4da6ff;'>Visit 'GoVerseTV' on YouTube</a></p>""",
        "apply": "Anwenden",
        "startup_applied": "Starteinstellungen angewendet.",
        "startup_enabled": "Autostart wurde aktiviert.",
        "startup_disabled": "Autostart wurde deaktiviert.",
        "changelog": """<h2>Ver 1.0.16 (2026-03-16)</h2>
<ul>
<li><b>Mehrfachstart verhindert:</b> Wenn bereits eine Instanz im Tray laeuft, oeffnet ein neuer Start nur das vorhandene Einstellungsfenster.</li>
<li><b>Lokale Update-Tests:</b> Auto-Update kann jetzt ueber <code>update-test/update.json</code> oder <code>GOPOINT_UPDATE_MANIFEST</code> ohne GitHub getestet werden.</li>
</ul>

<h2>Ver 1.0.15 (2026-03-16)</h2>
<ul>
<li><b>Autostart-Pfad korrigiert:</b> Nuitka-Onefile-Builds registrieren jetzt den echten <code>GoPoint.exe</code>-Pfad statt einer temporaeren <code>python.exe</code>.</li>
<li><b>Unterstuetzung fuer Quellstart:</b> Die Autostart-Registrierung funktioniert jetzt auch bei Starts mit <code>python GoPoint.py</code>.</li>
</ul>

<h2>Ver 1.0.14 (2026-03-13)</h2>
<ul>
<li><b>Wichtig:</b> Nutzer von <code>v1.0.12</code> muessen die aktuelle Version einmal manuell installieren, weil die Update-Erkennung in v1.0.12 fehlerhaft ist.</li>
<li><b>Korrektur der EXE-Erkennung:</b> Mit Nuitka gebaute EXE-Dateien werden jetzt korrekt als Paket-Build erkannt, sodass Auto-Update und Autostart wieder funktionieren.</li>
</ul>

<h2>Ver 1.0.13 (2026-03-13)</h2>
<ul>
<li><b>Leistungsoptimierungen:</b> Unnoetige Neuzeichnungen im Leerlauf wurden reduziert und das erzwungene Topmost-Refresh pro Frame entfernt, um CPU- und GPU-Last auf aelteren PCs zu senken.</li>
<li><b>Abgestufter Low-Spec-Modus:</b> Drei Leistungsstufen erlauben jetzt einen besseren Ausgleich zwischen weicher Bewegung und geringerem Ressourcenverbrauch.</li>
</ul>

<h2>Ver 1.0.12 (2026-03-09)</h2>
<ul>
<li><b>Sicherere Auswahl des Update-Assets:</b> Das Auto-Update akzeptiert jetzt nur noch das Release-Asset <code>GoPoint.exe</code> statt irgendeiner EXE-Datei.</li>
<li><b>Startpfad mit Anfuehrungszeichen:</b> Der Autostart-Registrywert speichert den EXE-Pfad jetzt in Anfuehrungszeichen, um Fehlinterpretationen bei Leerzeichen zu vermeiden.</li>
</ul>

<h2>Ver 1.0.11 (2026-03-09)</h2>
<ul>
<li><b>C++-Einzeldatei fuer die Auslieferung:</b> Der Release-Build wird jetzt als mit Nuitka erzeugte Einzel-EXE erstellt, sodass bestehende 1.0.10-Installationen per Auto-Update wechseln koennen.</li>
<li><b>Einheitlicher Release-Dateiname:</b> GitHub-Releases liefern jetzt immer <code>GoPoint.exe</code> aus; lokale Builds erzeugen zusaetzlich eine versionierte Kopie.</li>
</ul>

<h2>Ver 1.0.10 (2026-03-08)</h2>
<ul>
<li><b>Runder Kometenkopf:</b> Der Anfang der Tapered-Spur wird jetzt mit einem runden Kopf abgeschlossen und wirkt dadurch natürlicher.</li>
</ul>

<h2>Ver 1.0.9 (2026-03-08)</h2>
<ul>
<li><b>Stabileres Auto-Update:</b> Gleichzeitige automatische und manuelle Update-Prüfungen werden jetzt sauber nacheinander verarbeitet.</li>
<li><b>Zuverlässiger Abschluss des Updates:</b> Neustart und Beenden nach dem Ersetzen der EXE wurden robuster gemacht.</li>
<li><b>Profilspeicherung korrigiert:</b> Angepasste Default-Profile werden beim nächsten Start nicht mehr überschrieben.</li>
</ul>

<h2>Ver 1.0.6</h2>
<ul>
<li>Verbessertes Mauszeiger-Tracking (Anwendung von Federphysik für perfekt weiche und kontinuierliche Spuren, analog zur Vorschau-Animation)</li>
</ul>

<h2>Ver 1.0.5</h2>
<ul>
<li>Added Version Info Display</li>
<li>Improved Startup Apply Button Position</li>
</ul>

<h2>Ver 1.0.4</h2>
<ul>
<li>Added Run on Startup Option</li>
<li>Added Update History Menu</li>
<li>Fixed System Z-Order (Always on Top)</li>
</ul>

<h2>Ver 1.0.3</h2>
<ul>
<li>Fixed system tray right-click issue</li>
<li>Fixed missing EXE icon resource</li>
</ul>

<h2>Ver 1.0.2</h2>
<ul>
<li>Added Contact & KakaoTalk links</li>
<li>Optimized Program Size</li>
</ul>

<h2>Ver 1.0.1</h2>
<ul>
<li>Applied Trail Smoothing Algorithm</li>
<li>Improved Quit Button Behavior</li>
</ul>

<h2>Ver 1.0.0</h2>
<ul>
<li>GoPoint Initial Release</li>
</ul>"""
    },
    "ru": {
        "title": "GoPoint",
        "preview": "Предпросмотр",
        "profile": "Профиль",
        "save": "Сохранить",
        "delete": "Удалить",
        "trail_style": "Стиль следа",
        "color_palette": "Цветовая палитра",
        "reverse_order": "Обратить",
        "reset": "Сброс",
        "add_color": "Добавить цвет (+)",
        "remove_color": "Удалить цвет (-)",
        "width": "Ширина",
        "length": "Длина",
        "fade_out": "Эффект затухания",
        "quit": "Выход",
        "warn_delete_default": "Нельзя удалить профиль 'Default'.",
        "confirm_delete": "Удалить профиль '{name}'?",
        "dlg_save_title": "Сохранить профиль",
        "dlg_save_label": "Имя профиля:",
        "warn_min_color": "Требуется хотя бы один цвет.",
        "language": "Язык (Language)",
        "confirm_delete_title": "Подтверждение удаления",
        "warning": "Предупреждение",
        "style_constant": "Линия (Constant)",
        "style_dots": "Точки (Dots)",
        "style_tapered": "Комета (Tapered)",
        "developer": "Разработчик: Goverse (GoVerseTV)",
        "youtube": "YouTube канал",
        "contact": "Контакты: <a href='mailto:ruruoni1@gmail.com' style='color: #4da6ff;'>ruruoni1@gmail.com</a>",
        "about_btn": "About App",
        "about_msg": """<h3>About GoPoint</h3>
<p>Whenever I made tutorial videos for 'GoVerseTV', I worried about viewers losing track of my mouse cursor. Existing programs were good, but I wanted something smoother and more intuitive, so I created <b>'GoPoint'</b> myself.</p>
<p>GoPoint is here to help your screen's important moments shine brighter. Meet me on my channel for more tips and stories!</p>
<p>👉 <a href='https://www.youtube.com/@GOVERSE82' style='color: #4da6ff;'>Visit 'GoVerseTV' on YouTube</a></p>"""
    }
}


# ... (rest of imports)



# ... (Previous imports match) ...

class ColorDelegate(QStyledItemDelegate):
    def paint(self, painter, option, index):
        # Create a copy of the option to modify it
        opt = QStyleOptionViewItem(option)
        # Remove the Selected state so the base paint renders the item "normally" (just background color)
        opt.state &= ~QStyle.StateFlag.State_Selected
        
        super().paint(painter, opt, index)
        
        # If the item was actually selected, draw a custom border
        if option.state & QStyle.StateFlag.State_Selected:
            painter.save()
            pen = QPen(Qt.GlobalColor.white)
            pen.setWidth(3)
            # Alignment: stroke is centered on the line, so verify rect bounds
            painter.setPen(pen)
            
            rect = opt.rect
            # Draw inside slightly to not clip
            painter.drawRect(rect.adjusted(1, 1, -1, -1))
            painter.restore()


from PyQt6.QtCore import Qt, QTimer, QPointF
from PyQt6.QtGui import QPainter, QPainterPath, QColor, QPen, QPolygonF, QAction, QIcon, QCursor, QPixmap, QLinearGradient

import win32gui
import win32con
import win32api

def draw_trail(painter, history, style, colors, width_factor, length, opacity_decay, smoothing_iterations=NORMAL_SMOOTHING_ITERATIONS):
    if len(history) < 2 and style != "DOTS":
        return

    painter.setRenderHint(QPainter.RenderHint.Antialiasing)

    # Smoothing helper (Chaikin's Algorithm)
    def smooth_points(points, iterations=2):
        if len(points) < 3: return list(points)
        
        smoothed = list(points)
        for _ in range(iterations):
            new_points = [smoothed[0]] # Keep start
            for i in range(len(smoothed) - 1):
                p1 = smoothed[i]
                p2 = smoothed[i+1]
                
                # Chaikin: Q = 0.75*P1 + 0.25*P2, R = 0.25*P1 + 0.75*P2
                q = p1 * 0.75 + p2 * 0.25
                r = p1 * 0.25 + p2 * 0.75
                
                new_points.append(q)
                new_points.append(r)
            
            new_points.append(smoothed[-1]) # Keep end
            smoothed = new_points
        return smoothed

    # Apply smoothing for continuous styles
    if style in ["CONSTANT", "TAPERED"] and smoothing_iterations > 0:
        history = smooth_points(history, iterations=smoothing_iterations)
    
    # Helper to interpolate color
    def interpolate_color(progress, colors):
        if not colors: return QColor(Qt.GlobalColor.white)
        if len(colors) == 1: return QColor(colors[0])
        n_segments = len(colors) - 1
        pos = progress * n_segments
        index = int(pos)
        t = pos - index
        if index >= n_segments: return QColor(colors[-1])
        c1 = colors[index]
        c2 = colors[index+1]
        return QColor(
            int(c1.red() + (c2.red() - c1.red()) * t),
            int(c1.green() + (c2.green() - c1.green()) * t),
            int(c1.blue() + (c2.blue() - c1.blue()) * t)
        )

    if style == "DOTS":
        for i, point in enumerate(history):
            progress = i / len(history)
            color = interpolate_color(progress, colors)
            alpha = 255 * (1 - progress) if opacity_decay else 255
            color.setAlpha(int(alpha))
            painter.setBrush(color)
            painter.setPen(Qt.PenStyle.NoPen)
            # Fix: Radius should be half of width_factor for diameter to match width
            base_radius = width_factor / 2.0
            radius = base_radius * (1 - progress) if style == "TAPERED" else base_radius
            painter.drawEllipse(QPointF(point), radius, radius)

    elif style == "CONSTANT":
# ... (Keep CONSTANT and TAPERED logic same, use view_file content for brevity in targeting if possible, but here replacing block for safety as I need to match Indentation)
# Actually, I will target specific blocks to avoid huge replacement.

        if len(history) < 2: return
        
        # Optimization: If single color, use fast path
        if len(colors) == 1:
            path = QPainterPath()
            path.moveTo(QPointF(history[0]))
            for point in list(history)[1:]:
                path.lineTo(QPointF(point))
            
            pen = QPen(colors[0], width_factor)
            pen.setCapStyle(Qt.PenCapStyle.RoundCap)
            pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
            painter.setPen(pen)
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawPath(path)
            return

        # Multi-color (Gradient)
        pen = QPen()
        pen.setWidth(width_factor)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
        
        points = list(history)
        for i in range(len(points) - 1):
            p1 = points[i]
            p2 = points[i+1]
            
            progress = i / len(points)
            color = interpolate_color(progress, colors)
            
            pen.setColor(color)
            painter.setPen(pen)
            painter.drawLine(QPointF(p1), QPointF(p2))

    else: # TAPERED
        points = list(history)
        if len(points) < 2: return
        
        # Calculate offset points
        left_points = []
        right_points = []
        
        for i in range(len(points) - 1):
            p1 = points[i]
            p2 = points[i+1]
            vec = p2 - p1
            length_vec = (vec.x()**2 + vec.y()**2)**0.5
            if length_vec == 0: continue
            
            dx = vec.x() / length_vec
            dy = vec.y() / length_vec
            nx = -dy
            ny = dx
            
            progress = i / len(points)
            current_width = width_factor * (1 - progress)
            
            lx = p1.x() + nx * current_width / 2
            ly = p1.y() + ny * current_width / 2
            rx = p1.x() - nx * current_width / 2
            ry = p1.y() - ny * current_width / 2
            
            left_points.append(QPointF(lx, ly))
            right_points.append(QPointF(rx, ry))
            
        if points:
            left_points.append(QPointF(points[-1]))
        
        path = QPainterPath()
        if left_points:
            path.moveTo(left_points[0])
            for p in left_points[1:]: path.lineTo(p)
            for p in reversed(right_points): path.lineTo(p)
            path.closeSubpath()
        
        if len(colors) > 1:
            try:
                # Ensure QPointF for gradient to avoid ambiguity
                start_p = QPointF(points[0])
                end_p = QPointF(points[-1])
                
                if (start_p - end_p).manhattanLength() < 1:
                    painter.setBrush(QColor(colors[0]))
                else:
                    gradient = QLinearGradient(start_p, end_p)
                    for i, color in enumerate(colors):
                        gradient.setColorAt(i / (len(colors) - 1), color)
                    painter.setBrush(gradient)
            except:
                painter.setBrush(QColor(colors[0]))
        else:
            color = QColor(colors[0])
            painter.setBrush(color)

        painter.setOpacity(0.8 if opacity_decay else 1.0)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawPath(path)
        # Cover the blunt polygon edge so the comet head reads as a circle.
        head_radius = width_factor / 2.0
        painter.drawEllipse(QPointF(points[0]), head_radius, head_radius)

class PreviewWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(150)
        self.setStyleSheet("background-color: #222; border: 1px solid #444; border-radius: 5px;")
        
        self.history = collections.deque(maxlen=20)
        self.angle = 0
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_animation)
        self.is_running = False
        self.low_spec_level = LOW_SPEC_LEVEL_DEFAULT
        
        # Default settings
        self.trail_style = "TAPERED"
        self.trail_colors = [QColor("#00FFFF")]
        self.trail_width = 15
        self.trail_length = 20
        self.opacity_decay = True
        self.smoothing_iterations = NORMAL_SMOOTHING_ITERATIONS
        self.apply_performance_mode(LOW_SPEC_LEVEL_DEFAULT)

    def apply_performance_mode(self, low_spec_level):
        self.low_spec_level = clamp_low_spec_level(low_spec_level)
        preset = get_performance_preset(self.low_spec_level, preview=True)
        self.smoothing_iterations = preset["smoothing_iterations"]
        self.timer.setInterval(preset["interval_ms"])
        if self.is_running and not self.timer.isActive():
            self.timer.start()

    def set_running(self, running):
        self.is_running = running
        if running:
            self.timer.start()
        else:
            self.timer.stop()

    def update_settings(self, style, colors, width, length, decay, low_spec_level=LOW_SPEC_LEVEL_DEFAULT):
        self.trail_style = style
        self.trail_colors = colors
        self.trail_width = width
        self.trail_length = length
        self.opacity_decay = decay
        self.history = collections.deque(self.history, maxlen=length)
        self.apply_performance_mode(low_spec_level)

    def update_animation(self):
        center_x = self.width() / 2
        center_y = self.height() / 2
        radius = 40
        
        target_x = center_x + radius * math.cos(math.radians(self.angle))
        target_y = center_y + radius * math.sin(math.radians(self.angle))
        target = QPointF(target_x, target_y)
        
        if not hasattr(self, 'trail_points') or len(self.trail_points) != self.trail_length:
            if not hasattr(self, 'trail_points') or len(self.trail_points) == 0:
                self.trail_points = [target for _ in range(self.trail_length)]
            else:
                while len(self.trail_points) < self.trail_length:
                    self.trail_points.append(self.trail_points[-1])
                self.trail_points = self.trail_points[:self.trail_length]
                
        self.trail_points[0] = target
        for i in range(1, self.trail_length):
            c = self.trail_points[i]
            t = self.trail_points[i-1]
            # Use 0.45 easing parameter for smooth tracking like sample animation
            self.trail_points[i] = QPointF(c.x() + (t.x() - c.x()) * 0.45, 
                                           c.y() + (t.y() - c.y()) * 0.45)
                                           
        self.history = collections.deque(self.trail_points, maxlen=self.trail_length)
        self.angle = (self.angle + 5) % 360
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        draw_trail(
            painter,
            self.history,
            self.trail_style,
            self.trail_colors,
            self.trail_width,
            self.trail_length,
            self.opacity_decay,
            smoothing_iterations=self.smoothing_iterations
        )


import shutil # For moving legacy config

# ... (rest of imports)

class ProfileManager:
    DEFAULT_SAMPLES = {
        # 2 Color Combinations
        "Sample 1 - Neon Blue": ["#00FFFF", "#0000FF"],
        "Sample 2 - Neon Red": ["#FF0000", "#FF8000"],
        "Sample 3 - Neon Green": ["#00FF00", "#008000"],
        "Sample 4 - Purple Haze": ["#FF00FF", "#800080"],
        "Sample 5 - Golden": ["#FFD700", "#FFA500"],
        # 3 Color Combinations
        "Sample 6 - Fire": ["#FFFF00", "#FFA500", "#FF0000"], # Default / Fire
        "Sample 6 - Twilight": ["#4B0082", "#8A2BE2", "#FF69B4"], # Indigo, BlueViolet, HotPink
        "Sample 7 - Ocean": ["#00FFFF", "#0000FF", "#000080"],
        "Sample 8 - RGB": ["#FF0000", "#00FF00", "#0000FF"],
        "Sample 9 - Pastel": ["#FFB3BA", "#FFFFBA", "#BAE1FF"],
        "Sample 10 - Aurora": ["#00FF00", "#00FFFF", "#FF00FF"]
    }
    
    FIRE_COLORS = ["#FFFF00", "#FFA500", "#FF0000"]
    LEGACY_DEFAULT_PROFILE = {
        "style": "CONSTANT",
        "colors": ["#00FFFF"],
        "width": 12,
        "length": 20,
        "opacity_decay": True
    }
    
    def __init__(self, filename="profiles.json"):
        # Relocate to AppData/Roaming/MouseTrailOverlay
        app_data = os.getenv('APPDATA')
        if not app_data:
            app_data = os.path.expanduser("~")
            
        self.config_dir = os.path.join(app_data, "GoPoint")
        if not os.path.exists(self.config_dir):
            os.makedirs(self.config_dir)
            
        self.filepath = os.path.join(self.config_dir, filename)
        
        # Migration: If profiles.json exists in CWD (current working directory), move it to AppData
        # check CWD
        cwd_config = os.path.join(os.getcwd(), filename)
        if os.path.exists(cwd_config) and not os.path.exists(self.filepath):
            try:
                shutil.move(cwd_config, self.filepath)
                print(f"Migrated config from {cwd_config} to {self.filepath}")
            except Exception as e:
                print(f"Failed to migrate config: {e}")
        
        # If it still exists in CWD (e.g. migration failed or target existed), we might want to ignore or delete. 
        # But let's just use the AppData one.
        
        self.profiles = {}
        self.current_profile = "Default"
        self.language = self.detect_system_language() # Initialize language
        self.low_spec_level = LOW_SPEC_LEVEL_DEFAULT
        self.load_profiles()
        self.init_sample_profiles() # Ensure samples exist

    def load_profiles(self):
        if os.path.exists(self.filepath):
            try:
                with open(self.filepath, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.profiles = data.get("profiles", {})
                    self.current_profile = data.get("current", "Default")
                    self.language = data.get("language", self.detect_system_language())
                    stored_level = data.get("low_spec_level")
                    if stored_level is None:
                        stored_level = LOW_SPEC_LEVEL_LEGACY_ENABLED if data.get("low_spec_mode", False) else LOW_SPEC_LEVEL_DEFAULT
                    self.low_spec_level = clamp_low_spec_level(stored_level)
            except:
                self.profiles = {}
        
        if not self.profiles:
            self.create_default_profile()

    def create_default_profile(self):
        # Default is now "Sample 6 - Fire"
        self.profiles["Default"] = {
            "style": "CONSTANT",
            "colors": ["#FFFF00", "#FFA500", "#FF0000"], # Fire colors
            "width": 12,
            "length": 20,
            "opacity_decay": True
        }
        self.current_profile = "Default"

    def init_sample_profiles(self):
        updated = False
        
        # Preserve user-customized Default profiles and only migrate the legacy cyan default.
        fire_settings = {
            "style": "CONSTANT",
            "colors": self.FIRE_COLORS,
            "width": 12,
            "length": 20,
            "opacity_decay": True
        }
        current_default = self.profiles.get("Default")
        if current_default is None or current_default == self.LEGACY_DEFAULT_PROFILE:
            self.profiles["Default"] = fire_settings
            updated = True

        for name, colors in self.DEFAULT_SAMPLES.items():
            if name not in self.profiles:
                self.profiles[name] = {
                    "style": "CONSTANT",
                    "colors": colors,
                    "width": 12,
                    "length": 20,
                    "opacity_decay": True
                }
                updated = True
        
        if updated:
            self.save_profiles()

    def save_profiles(self):
        data = {
            "profiles": self.profiles,
            "current": self.current_profile,
            "language": self.language,
            "low_spec_level": self.low_spec_level,
            "low_spec_mode": self.low_spec_level > 0
        }
        with open(self.filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4)

    def get_current_settings(self):
        return self.profiles.get(self.current_profile, self.profiles["Default"])

    def set_current_profile(self, name):
        if name in self.profiles:
            self.current_profile = name
            self.save_profiles()
            return True
        return False

    def save_profile(self, name, settings):
        self.profiles[name] = settings
        self.current_profile = name
        self.save_profiles()

    def set_low_spec_level(self, level):
        self.low_spec_level = clamp_low_spec_level(level)
        self.save_profiles()

    def set_low_spec_mode(self, enabled):
        self.low_spec_level = LOW_SPEC_LEVEL_LEGACY_ENABLED if enabled else LOW_SPEC_LEVEL_DEFAULT
        self.save_profiles()

    def delete_profile(self, name):
        if name in self.profiles and name != "Default":
            del self.profiles[name]
            if self.current_profile == name:
                self.current_profile = "Default"
            self.save_profiles()
            return True
        return False

    def detect_system_language(self):
        try:
            sys_lang, _ = locale.getlocale()
            if not sys_lang:
                sys_lang = locale.setlocale(locale.LC_CTYPE, None)

            if sys_lang:
                sys_lang = sys_lang.lower()
                if sys_lang.startswith(('ko', 'korean')): return 'ko'
                if sys_lang.startswith(('ja', 'japanese')): return 'ja'
                if sys_lang.startswith(('es', 'spanish')): return 'es'
                if sys_lang.startswith(('zh', 'chinese')): return 'zh'
                if sys_lang.startswith(('fr', 'french')): return 'fr'
                if sys_lang.startswith(('de', 'german')): return 'de'
                if sys_lang.startswith(('ru', 'russian')): return 'ru'
            return 'en' # Default fallback
        except:
            return 'en'

# Removed UPDATE_HISTORY_LOG global constant
# It is now part of TRANSLATIONS


class ChangelogDialog(QDialog):
    def __init__(self, parent=None, current_lang="ko"):
        super().__init__(parent)
        self.setWindowTitle("Update History")
        self.setFixedSize(400, 500)
        
        # Transparent background for aesthetics or just simple dialog
        # Let's clean standard dialog style
        layout = QVBoxLayout()
        
        self.title_label = QLabel("Update Log")
        font = QFont()
        font.setPointSize(14)
        font.setBold(True)
        self.title_label.setFont(font)
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.title_label)
        
        self.browser = QTextBrowser()
        self.browser.setOpenExternalLinks(True)
        # self.browser.setHtml(UPDATE_HISTORY_LOG) # Removed global constant usage
        layout.addWidget(self.browser)
        
        self.close_btn = QPushButton("Close")
        self.close_btn.clicked.connect(self.close)
        layout.addWidget(self.close_btn)
        
        self.setLayout(layout)
        self.update_language(current_lang)

    def update_language(self, lang_code):
        texts = TRANSLATIONS.get(lang_code, TRANSLATIONS["en"])
        self.setWindowTitle(texts.get("update_history", "Update History"))
        self.title_label.setText(texts.get("update_title", "Update Log"))
        self.close_btn.setText(texts.get("close", "Close"))
        self.browser.setHtml(texts.get("changelog", "<h2>No Changelog Available</h2>"))

class UpdateSignal(QObject):
    finished = pyqtSignal(str, dict)
    download_finished = pyqtSignal(str, dict)

class AutoUpdater:
    _signal = UpdateSignal()
    _check_in_progress = False
    _pending_manual_check = False
    _download_in_progress = False

    @staticmethod
    def cleanup():
        """ Remove leftover .old files from previous updates """
        try:
            current_exe = get_packaged_executable_path()
            if current_exe:
                old_exe = current_exe + ".old"
                if os.path.exists(old_exe):
                    os.remove(old_exe)
        except Exception as e:
            print(f"Cleanup failed: {e}")

    @staticmethod
    def _version_to_tuple(version_str):
        try:
            return tuple(map(int, version_str.lstrip('v').split('.')))
        except:
            return (0, 0, 0)

    @staticmethod
    def check_and_prompt(parent_widget, profile_manager, manual_check=False):
        if AutoUpdater._check_in_progress:
            AutoUpdater._pending_manual_check = AutoUpdater._pending_manual_check or manual_check
            return

        AutoUpdater._check_in_progress = True
        request_id = uuid.uuid4().hex

        # Local function to handle UI update after check
        def on_check_finished(emitted_request_id, result):
            if emitted_request_id != request_id:
                return

            try:
                # Disconnect only this specific slot to be safe
                AutoUpdater._signal.finished.disconnect(on_check_finished)
            except:
                pass

            effective_manual_check = manual_check or AutoUpdater._pending_manual_check
            AutoUpdater._check_in_progress = False
            AutoUpdater._pending_manual_check = False
            
            # Log for debugging loop
            try:
                log_path = os.path.join(tempfile.gettempdir(), "gopoint_debug.log")
                with open(log_path, "a", encoding="utf-8") as f:
                    import time
                    t_str = time.strftime("%Y-%m-%d %H:%M:%S")
                    f.write(f"[{t_str}] Check finished. Current={APP_VERSION}, Latest={result.get('latest_version')}\n")
            except:
                pass

            if result.get("error"):
                print(f"Update check error: {result.get('error')}")
                if effective_manual_check:
                    AutoUpdater._notify_error(parent_widget, profile_manager)
                return

            latest_version = result.get("latest_version")
            asset_url = result.get("asset_url")

            print(f"Checking version: Current={APP_VERSION}, Latest={latest_version}")

            if AutoUpdater._version_to_tuple(latest_version) > AutoUpdater._version_to_tuple(APP_VERSION):
                if asset_url:
                    AutoUpdater._prompt_update(parent_widget, profile_manager, latest_version, asset_url)
            elif effective_manual_check:
                AutoUpdater._notify_latest(parent_widget, profile_manager)

        AutoUpdater._signal.finished.connect(on_check_finished)

        def _run():
            result = {"latest_version": None, "asset_url": None, "error": None}
            try:
                import time
                cache_bust_token = str(int(time.time()))
                manifest_url, update_source = get_configured_update_manifest_url(cache_bust_token)
                headers = {
                    'User-Agent': 'GoPoint-Updater',
                    'Cache-Control': 'no-cache',
                    'Pragma': 'no-cache'
                }
                data = load_update_manifest_json(manifest_url, timeout=10, headers=headers)
                result = parse_update_manifest(data, manifest_url, cache_bust_token)
                if update_source != "github":
                    print(f"Using {update_source} update manifest: {manifest_url}")
            except Exception as e:
                result["error"] = str(e)
            
            AutoUpdater._signal.finished.emit(request_id, result)
                    
        threading.Thread(target=_run, daemon=True).start()

    @staticmethod
    def _get_tr(profile_manager, key):
        lang = profile_manager.language
        translations = TRANSLATIONS.get(lang, TRANSLATIONS["en"])
        return translations.get(key, TRANSLATIONS["en"].get(key, key))

    @staticmethod
    def _notify_latest(parent_widget, profile_manager):
        QMessageBox.information(parent_widget, 
                                AutoUpdater._get_tr(profile_manager, "update_available"), 
                                AutoUpdater._get_tr(profile_manager, "update_latest"))
                                
    @staticmethod
    def _notify_error(parent_widget, profile_manager, message=None):
        QMessageBox.warning(parent_widget, 
                            AutoUpdater._get_tr(profile_manager, "update_available"), 
                            message or AutoUpdater._get_tr(profile_manager, "update_error"))

    @staticmethod
    def _prompt_update(parent_widget, profile_manager, new_version, download_url):
        title = AutoUpdater._get_tr(profile_manager, "update_available")
        msg_template = AutoUpdater._get_tr(profile_manager, "update_msg")
        msg = msg_template.format(new_version=new_version, current_version=APP_VERSION)
        
        reply = QMessageBox.question(parent_widget, title, msg, 
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            AutoUpdater._perform_update(parent_widget, profile_manager, download_url)

    @staticmethod
    def _handle_download_result(parent_widget, profile_manager, result):
        if result.get("error"):
            print(f"Download error: {result.get('error')}")
            AutoUpdater._notify_error(parent_widget, profile_manager, result.get("error"))
            if hasattr(parent_widget, 'setEnabled'):
                parent_widget.setEnabled(True)
            return

        threading.Timer(0.3, lambda: os._exit(0)).start()
        QApplication.quit()

    @staticmethod
    def _perform_update(parent_widget, profile_manager, download_url):
        if AutoUpdater._download_in_progress:
            return

        AutoUpdater._download_in_progress = True
        request_id = uuid.uuid4().hex

        def on_download_finished(emitted_request_id, result):
            if emitted_request_id != request_id:
                return

            try:
                AutoUpdater._signal.download_finished.disconnect(on_download_finished)
            except:
                pass

            AutoUpdater._download_in_progress = False
            AutoUpdater._handle_download_result(parent_widget, profile_manager, result)

        AutoUpdater._signal.download_finished.connect(on_download_finished)

        if is_packaged_build() and hasattr(parent_widget, 'setEnabled'):
            parent_widget.setEnabled(False)
             
        def _download():
            result = {"error": None}
            released_instance_server = False
            try:
                current_exe = get_packaged_executable_path()
                if not current_exe:
                    result["error"] = "Auto-update is only supported in the packaged .exe build."
                    return

                old_exe = current_exe + ".old"
                
                # 1. Rename current running exe to .old (Windows allows this!)
                if os.path.exists(old_exe):
                    os.remove(old_exe)
                os.rename(current_exe, old_exe)
                
                try:
                    # 2. Download new EXE to the original path
                    # Note: download_url already has timestamp from _run
                    headers = {
                        'User-Agent': 'GoPoint-Updater',
                        'Cache-Control': 'no-cache',
                        'Pragma': 'no-cache'
                    }
                    with open_update_download_stream(download_url, timeout=120, headers=headers) as response, open(current_exe, 'wb') as out_file:
                        shutil.copyfileobj(response, out_file)
                    
                    # 3. Start the NEW exe
                    release_single_instance_server()
                    released_instance_server = True
                    subprocess.Popen([current_exe], shell=False)
                except Exception as e:
                    # Rollback if download fails
                    if os.path.exists(old_exe):
                        if os.path.exists(current_exe): os.remove(current_exe)
                        os.rename(old_exe, current_exe)
                    if released_instance_server:
                        resume_single_instance_server()
                    raise e
                 
            except Exception as e:
                result["error"] = str(e)
            finally:
                AutoUpdater._signal.download_finished.emit(request_id, result)
                     
        threading.Thread(target=_download, daemon=True).start()

class SettingsDialog(QDialog):
    def __init__(self, overlay, parent=None):
        super().__init__(parent)
        self.force_quit = False
        self.overlay = overlay
        self.setWindowTitle(f"{self.tr('title')} v{APP_VERSION}")
        self.resize(360, 600) 
        
        # Window Stays On Top
        self.setWindowFlags(self.windowFlags() | Qt.WindowType.WindowStaysOnTopHint)

        # Stylesheet
        self.setStyleSheet("""
            QDialog { background-color: #2b2b2b; color: #ffffff; font-family: 'Segoe UI', sans-serif; }
            QLabel { color: #dddddd; font-size: 14px; font-weight: bold; margin-top: 5px; }
            QComboBox, QListWidget { background-color: #3b3b3b; color: #ffffff; border: 1px solid #555555; border-radius: 5px; padding: 5px; font-size: 13px; }

            QComboBox::drop-down { border: 0px; }
            QComboBox QAbstractItemView { background-color: #3b3b3b; color: #ffffff; selection-background-color: #505050; }
            QPushButton { background-color: #007acc; color: white; border: none; border-radius: 5px; padding: 6px; font-size: 12px; font-weight: bold; }
            QPushButton:hover { background-color: #0098ff; }
            QPushButton#QuitBtn { background-color: #d32f2f; padding: 10px; font-size: 14px; margin-top: 10px; }
            QPushButton#QuitBtn:hover { background-color: #f44336; }
            QPushButton#DeleteBtn { background-color: #d32f2f; }
            QPushButton#ResetBtn { background-color: #555; }
            QPushButton#ResetBtn:hover { background-color: #777; }
            QSlider::groove:horizontal { border: 1px solid #3b3b3b; height: 8px; background: #1a1a1a; margin: 2px 0; border-radius: 4px; }
            QSlider::handle:horizontal { background: #007acc; border: 1px solid #007acc; width: 18px; height: 18px; margin: -7px 0; border-radius: 9px; }
            QCheckBox { color: #dddddd; font-size: 14px; spacing: 5px; margin-top: 10px; }
            QCheckBox { color: #dddddd; font-size: 14px; spacing: 5px; margin-top: 10px; }
            QCheckBox::indicator { width: 18px; height: 18px; }
            QLabel#FooterLabel { color: #aaaaaa; font-size: 11px; margin-top: 5px; }
            QLabel#FooterLink { color: #4da6ff; font-size: 11px; text-decoration: underline; margin-top: 0px; }
            QLabel#FooterLink:hover { color: #80bfff; }
        """)
        
        layout = QVBoxLayout()
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(5)
        
        # --- Language Section ---
        self.lang_label = QLabel(self.tr("language"))
        layout.addWidget(self.lang_label)
        self.lang_combo = QComboBox()
        self.lang_combo.addItem("한국어 (Korean)", "ko")
        self.lang_combo.addItem("English", "en")
        self.lang_combo.addItem("日本語 (Japanese)", "ja")
        self.lang_combo.addItem("Español (Spanish)", "es")
        self.lang_combo.addItem("中文 (Chinese)", "zh")
        self.lang_combo.addItem("Français (French)", "fr")
        self.lang_combo.addItem("Deutsch (German)", "de")
        self.lang_combo.addItem("Русский (Russian)", "ru")
        
        # Set current language
        curr_lang = self.overlay.profile_manager.language
        index = self.lang_combo.findData(curr_lang)
        if index >= 0:
            self.lang_combo.setCurrentIndex(index)
        self.lang_combo.currentIndexChanged.connect(self.change_language)
        layout.addWidget(self.lang_combo)

        # --- Preview Widget ---
        self.preview_label = QLabel(self.tr("preview"))
        layout.addWidget(self.preview_label)
        self.preview = PreviewWidget()
        layout.addWidget(self.preview)

        # --- Profile Section ---
        self.profile_label = QLabel(self.tr("profile"))
        layout.addWidget(self.profile_label)
        profile_layout = QHBoxLayout()
        self.profile_combo = QComboBox()
        self.profile_combo.currentIndexChanged.connect(self.change_profile)
        profile_layout.addWidget(self.profile_combo, 2)
        self.save_profile_btn = QPushButton(self.tr("save"))
        self.save_profile_btn.clicked.connect(self.save_profile)
        profile_layout.addWidget(self.save_profile_btn, 1)
        self.del_profile_btn = QPushButton(self.tr("delete"))
        self.del_profile_btn.setObjectName("DeleteBtn")
        self.del_profile_btn.clicked.connect(self.delete_profile)
        profile_layout.addWidget(self.del_profile_btn, 1)
        layout.addLayout(profile_layout)
        
        # --- Style Section ---
        self.style_label = QLabel(self.tr("trail_style"))
        layout.addWidget(self.style_label)
        self.style_combo = QComboBox()
        self.style_combo.addItem(self.tr("style_constant"), "CONSTANT")
        self.style_combo.addItem(self.tr("style_dots"), "DOTS")
        self.style_combo.addItem(self.tr("style_tapered"), "TAPERED")
        
        index = self.style_combo.findData(self.overlay.trail_style)
        if index >= 0:
            self.style_combo.setCurrentIndex(index)
        self.style_combo.currentIndexChanged.connect(self.update_style)
        layout.addWidget(self.style_combo)
        
        # --- Color Palette Section ---
        palette_label_layout = QHBoxLayout()
        self.palette_label = QLabel(self.tr("color_palette"))
        palette_label_layout.addWidget(self.palette_label)
        
        self.reverse_color_btn = QPushButton(self.tr("reverse_order"))
        self.reverse_color_btn.setFixedWidth(80)
        self.reverse_color_btn.clicked.connect(self.reverse_colors)
        palette_label_layout.addWidget(self.reverse_color_btn)
        
        self.reset_color_btn = QPushButton(self.tr("reset"))
        self.reset_color_btn.setObjectName("ResetBtn")
        self.reset_color_btn.setFixedWidth(60)
        self.reset_color_btn.clicked.connect(self.reset_colors)
        palette_label_layout.addWidget(self.reset_color_btn)
        
        layout.addLayout(palette_label_layout)
        
        self.color_list = QListWidget()
        self.color_list.setFixedHeight(80)
        self.color_list.setDragDropMode(QAbstractItemView.DragDropMode.InternalMove)
        self.color_list.setItemDelegate(ColorDelegate(self.color_list))
        self.color_list.itemDoubleClicked.connect(self.edit_color)
        self.color_list.model().rowsMoved.connect(self.sync_colors_from_list)
        layout.addWidget(self.color_list)
        
        color_btn_layout = QHBoxLayout()
        self.add_color_btn = QPushButton(self.tr("add_color"))
        self.add_color_btn.clicked.connect(self.add_color)
        color_btn_layout.addWidget(self.add_color_btn)
        self.remove_color_btn = QPushButton(self.tr("remove_color"))
        self.remove_color_btn.clicked.connect(self.remove_color)
        color_btn_layout.addWidget(self.remove_color_btn)
        layout.addLayout(color_btn_layout)
        
        # --- Sliders Section ---
        width_layout = QHBoxLayout()
        self.width_label = QLabel(self.tr("width"))
        width_layout.addWidget(self.width_label)
        self.width_value_label = QLabel(str(self.overlay.trail_width))
        width_layout.addWidget(self.width_value_label)
        width_layout.addStretch()
        layout.addLayout(width_layout)
        
        self.width_slider = QSlider(Qt.Orientation.Horizontal)
        self.width_slider.setRange(1, 100)
        self.width_slider.setValue(self.overlay.trail_width)
        self.width_slider.valueChanged.connect(self.update_width)
        layout.addWidget(self.width_slider)
        
        length_layout = QHBoxLayout()
        self.length_label = QLabel(self.tr("length"))
        length_layout.addWidget(self.length_label)
        self.length_value_label = QLabel(str(self.overlay.trail_length))
        length_layout.addWidget(self.length_value_label)
        length_layout.addStretch()
        layout.addLayout(length_layout)

        self.length_slider = QSlider(Qt.Orientation.Horizontal)
        self.length_slider.setRange(5, 100)
        self.length_slider.setValue(self.overlay.trail_length)
        self.length_slider.valueChanged.connect(self.update_length)
        layout.addWidget(self.length_slider)

        # --- Options Section ---
        self.opacity_check = QCheckBox(self.tr("fade_out"))
        self.opacity_check.setChecked(self.overlay.opacity_decay)
        self.opacity_check.stateChanged.connect(self.update_opacity)
        layout.addWidget(self.opacity_check)

        low_spec_layout = QHBoxLayout()
        self.low_spec_check = QCheckBox()
        self.low_spec_check.stateChanged.connect(self.update_low_spec_enabled)
        low_spec_layout.addWidget(self.low_spec_check)
        self.low_spec_combo = QComboBox()
        self.low_spec_combo.currentIndexChanged.connect(self.update_low_spec_level)
        low_spec_layout.addWidget(self.low_spec_combo)
        layout.addLayout(low_spec_layout)

        # Startup Section with Apply Button
        startup_layout = QHBoxLayout()
        self.startup_check = QCheckBox(self.tr("run_startup"))
        self.startup_check.setChecked(self.check_startup_registry())
        # self.startup_check.stateChanged.connect(self.toggle_startup) # Removed auto-toggle
        startup_layout.addWidget(self.startup_check)
        
        startup_layout.addStretch() # Push button to the right
        
        self.startup_apply_btn = QPushButton(self.tr("apply"))
        self.startup_apply_btn.setFixedWidth(60)
        self.startup_apply_btn.setStyleSheet("background-color: #555; font-size: 11px; padding: 4px;")
        self.startup_apply_btn.clicked.connect(self.apply_startup_setting)
        startup_layout.addWidget(self.startup_apply_btn)
        
        layout.addLayout(startup_layout)

        layout.addStretch()

        # Quit Button
        self.quit_btn = QPushButton(self.tr("quit"))
        self.quit_btn.setObjectName("QuitBtn")
        self.quit_btn.clicked.connect(self.quit_application)
        layout.addWidget(self.quit_btn)

        # --- Footer Section ---
        layout.addSpacing(10)
        
        footer_btn_layout = QHBoxLayout()
        
        self.about_btn = QPushButton(self.tr("about_btn"))
        self.about_btn.clicked.connect(self.show_about)
        self.about_btn.setStyleSheet("background-color: #555;")
        footer_btn_layout.addWidget(self.about_btn)
        
        self.history_btn = QPushButton(self.tr("update_history"))
        self.history_btn.clicked.connect(self.show_history)
        self.history_btn.setStyleSheet("background-color: #555;")
        footer_btn_layout.addWidget(self.history_btn)
        
        self.update_btn = QPushButton("업데이트 확인")
        self.update_btn.clicked.connect(self.check_for_updates)
        self.update_btn.setStyleSheet("background-color: #555;")
        footer_btn_layout.addWidget(self.update_btn)
        
        layout.addLayout(footer_btn_layout)
        
        footer_info_layout = QVBoxLayout()
        footer_info_layout.setSpacing(2)
        
        self.dev_label = QLabel(self.tr("developer"))
        self.dev_label.setObjectName("FooterLabel")
        self.dev_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        footer_info_layout.addWidget(self.dev_label)
        
        self.youtube_label = QLabel(f'<a href="http://www.youtube.com/@goverse82" style="color: #4da6ff;">{self.tr("youtube")}</a>')
        self.youtube_label.setObjectName("FooterLink")
        self.youtube_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.youtube_label.setOpenExternalLinks(True)
        footer_info_layout.addWidget(self.youtube_label)
        
        self.contact_label = QLabel(self.tr("contact"))
        self.contact_label.setObjectName("FooterLabel")
        self.contact_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.contact_label.setOpenExternalLinks(True)
        footer_info_layout.addWidget(self.contact_label)
        
        layout.addLayout(footer_info_layout)
        
        self.setLayout(layout)
        
        # Initialize UI state
        self.refresh_profile_list()
        self.refresh_color_list()
        self.refresh_low_spec_controls()
        self.update_preview()
        
    def check_startup_registry(self):
        return is_startup_registered_for_current_build()

    def apply_startup_setting(self):
        desired_enabled = self.startup_check.isChecked()
        applied = self.toggle_startup(desired_enabled)
        actual_enabled = self.check_startup_registry()
        self.startup_check.setChecked(actual_enabled)

        if applied and actual_enabled == desired_enabled:
            message_key = "startup_enabled" if desired_enabled else "startup_disabled"
            QMessageBox.information(self, self.tr("title"), self.tr(message_key))
        else:
            QMessageBox.warning(self, self.tr("warning"), self.tr("startup_failed"))

    def toggle_startup(self, enabled):
        return set_startup_registry_enabled(bool(enabled))

    def show_history(self):
        dlg = ChangelogDialog(self, self.overlay.profile_manager.language)
        dlg.exec()

    def quit_application(self):
        self.force_quit = True
        QApplication.instance().quit()

    def closeEvent(self, event):
        if self.force_quit:
            event.accept()
        else:
            event.ignore()
            self.hide()

    def showEvent(self, event):
        super().showEvent(event)
        self.preview.set_running(True)

    def hideEvent(self, event):
        self.preview.set_running(False)
        super().hideEvent(event)

    # --- Profile Methods ---
    def tr(self, key):
        lang = self.overlay.profile_manager.language
        lang_table = TRANSLATIONS.get(lang, TRANSLATIONS["en"])
        return lang_table.get(key, TRANSLATIONS["en"].get(key, key))

    def low_spec_texts(self):
        lang = self.overlay.profile_manager.language
        if lang == "ko":
            return {
                "label": "저사양 모드",
                "levels": [
                    ("1단계 (약)", 1),
                    ("2단계 (보통)", 2),
                    ("3단계 (강)", 3),
                ],
            }
        return {
            "label": self.tr("low_spec_mode"),
            "levels": [
                ("Level 1 (Light)", 1),
                ("Level 2 (Balanced)", 2),
                ("Level 3 (Strong)", 3),
            ],
        }

    def refresh_low_spec_controls(self):
        texts = self.low_spec_texts()
        current_level = self.overlay.low_spec_level
        current_combo_level = self.low_spec_combo.currentData() if self.low_spec_combo.count() > 0 else 1
        if current_combo_level in (None, 0):
            current_combo_level = 1

        self.low_spec_check.blockSignals(True)
        self.low_spec_check.setText(texts["label"])
        self.low_spec_check.setChecked(current_level > 0)
        self.low_spec_check.blockSignals(False)

        self.low_spec_combo.blockSignals(True)
        self.low_spec_combo.clear()
        for text, level in texts["levels"]:
            self.low_spec_combo.addItem(text, level)
        index = self.low_spec_combo.findData(current_level if current_level > 0 else current_combo_level)
        if index >= 0:
            self.low_spec_combo.setCurrentIndex(index)
        self.low_spec_combo.setEnabled(current_level > 0)
        self.low_spec_combo.blockSignals(False)

    def change_language(self, index):
        lang_code = self.lang_combo.currentData()
        self.overlay.profile_manager.language = lang_code
        self.update_ui_text()
        self.overlay.update_tray_text() # Update tray method
        self.overlay.save_current_state()

    def update_ui_text(self):
        self.setWindowTitle(f"{self.tr('title')} v{APP_VERSION}")
        self.lang_label.setText(self.tr("language"))
        self.preview_label.setText(self.tr("preview"))
        self.profile_label.setText(self.tr("profile"))
        self.save_profile_btn.setText(self.tr("save"))
        self.del_profile_btn.setText(self.tr("delete"))
        self.style_label.setText(self.tr("trail_style"))
        
        # Update combo box items text without changing selection
        current_idx = self.style_combo.currentIndex()
        self.style_combo.setItemText(0, self.tr("style_constant"))
        self.style_combo.setItemText(1, self.tr("style_dots"))
        self.style_combo.setItemText(2, self.tr("style_tapered"))
        self.style_combo.setCurrentIndex(current_idx)
        
        self.palette_label.setText(self.tr("color_palette"))
        self.reverse_color_btn.setText(self.tr("reverse_order"))
        self.reset_color_btn.setText(self.tr("reset"))
        self.add_color_btn.setText(self.tr("add_color"))
        self.remove_color_btn.setText(self.tr("remove_color"))
        self.width_label.setText(self.tr("width"))
        self.length_label.setText(self.tr("length"))
        self.opacity_check.setText(self.tr("fade_out"))
        self.refresh_low_spec_controls()
        self.startup_check.setText(self.tr("run_startup"))
        self.startup_apply_btn.setText(self.tr("apply"))
        self.quit_btn.setText(self.tr("quit"))
        self.about_btn.setText(self.tr("about_btn"))
        self.history_btn.setText(self.tr("update_history"))
        
        # update_btn text based on lang
        btn_tr = {
            "ko": "업데이트 확인", "en": "Check for Updates", "ja": "更新確認",
            "zh": "检查更新", "es": "Buscar actualizaciones", "fr": "Rechercher des mises à jour",
            "de": "Nach Updates suchen", "ru": "Проверить обновления"
        }
        self.update_btn.setText(btn_tr.get(self.overlay.profile_manager.language, "Check for Updates"))
        
        # Footer
        self.dev_label.setText(self.tr("developer"))
        # Re-set HTML for link to preserve formatting if text changes
        self.youtube_label.setText(f'<a href="https://www.youtube.com/@GOVERSE82" style="color: #4da6ff;">{self.tr("youtube")}</a>')
        self.contact_label.setText(self.tr("contact"))
        


    def sync_colors_from_list(self, parent_idx, start, end, dest, dest_row):
        # Triggered when rows are moved
        new_colors = []
        for i in range(self.color_list.count()):
            item = self.color_list.item(i)
            new_colors.append(item.background().color())
        
        if new_colors:
            self.overlay.trail_colors = new_colors
            self.overlay.save_current_state()
            self.update_preview()

    def reverse_colors(self):
        self.overlay.trail_colors.reverse()
        self.refresh_color_list()
        self.overlay.save_current_state()

    def refresh_profile_list(self):
        self.profile_combo.blockSignals(True)
        self.profile_combo.clear()
        profiles = list(self.overlay.profile_manager.profiles.keys())
        self.profile_combo.addItems(profiles)
        self.profile_combo.setCurrentText(self.overlay.profile_manager.current_profile)
        self.profile_combo.blockSignals(False)

    def check_for_updates(self):
        AutoUpdater.check_and_prompt(self, self.overlay.profile_manager, manual_check=True)

    def change_profile(self, index):
        name = self.profile_combo.currentText()
        if self.overlay.profile_manager.set_current_profile(name):
            self.overlay.load_settings()
            self.sync_ui_with_overlay()

    def save_profile(self):
        current = self.profile_combo.currentText()
        name, ok = QInputDialog.getText(self, self.tr("dlg_save_title"), self.tr("dlg_save_label"), text=current)
        if ok and name:
            settings = {
                "style": self.overlay.trail_style,
                "colors": [c.name() for c in self.overlay.trail_colors],
                "width": self.overlay.trail_width,
                "length": self.overlay.trail_length,
                "opacity_decay": self.overlay.opacity_decay
            }
            self.overlay.profile_manager.save_profile(name, settings)
            self.refresh_profile_list()
    
    def delete_profile(self):
        current = self.profile_combo.currentText()
        if current == "Default":
            QMessageBox.warning(self, self.tr("warning"), self.tr("warn_delete_default"))
            return
        ret = QMessageBox.question(self, self.tr("confirm_delete_title"), self.tr("confirm_delete").format(name=current), QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if ret == QMessageBox.StandardButton.Yes:
            if self.overlay.profile_manager.delete_profile(current):
                self.overlay.load_settings()
                self.sync_ui_with_overlay()
                self.refresh_profile_list()

    def show_about(self):
        msg_box = QMessageBox(self)
        msg_box.setWindowTitle(self.tr("about_btn"))
        msg_box.setTextFormat(Qt.TextFormat.RichText)
        msg_box.setText(self.tr("about_msg"))
        msg_box.exec()

    def sync_ui_with_overlay(self):
        style_map = {"CONSTANT": 0, "DOTS": 1, "TAPERED": 2}
        self.style_combo.setCurrentIndex(style_map.get(self.overlay.trail_style, 0))
        self.width_slider.setValue(self.overlay.trail_width)
        self.length_slider.setValue(self.overlay.trail_length)
        self.opacity_check.setChecked(self.overlay.opacity_decay)
        self.refresh_low_spec_controls()
        self.refresh_color_list()
        self.refresh_profile_list()
        self.update_preview()

    # --- Color Methods ---
    def refresh_color_list(self):
        self.color_list.clear()
        for color in self.overlay.trail_colors:
            item = QListWidgetItem()
            item.setBackground(color)
            item.setText(color.name())
            text_c = QColor("black") if color.lightness() > 128 else QColor("white")
            item.setForeground(text_c)
            self.color_list.addItem(item)
        self.update_preview()
    
    def add_color(self):
        # Hide overlay to prevent picking the trail itself
        self.overlay.hide()
        try:
            color = QColorDialog.getColor(Qt.GlobalColor.cyan, self, "색상 추가")
        finally:
            self.overlay.show()
            self.overlay.raise_()
            
        if color.isValid():
            self.overlay.trail_colors.append(color)
            self.refresh_color_list()
            self.overlay.save_current_state()

    def remove_color(self):
        row = self.color_list.currentRow()
        if row >= 0:
            if len(self.overlay.trail_colors) > 1:
                del self.overlay.trail_colors[row]
                self.refresh_color_list()
                self.overlay.save_current_state()
            else:
                QMessageBox.warning(self, "경고", "최소 1개의 색상은 있어야 합니다.")
    
    def reset_colors(self):
        # determine target defaults
        current_name = self.overlay.profile_manager.current_profile
        custom_reset = False
        
        if current_name == "Default":
             target_colors = self.overlay.profile_manager.FIRE_COLORS
             custom_reset = True
        elif current_name in self.overlay.profile_manager.DEFAULT_SAMPLES:
             target_colors = self.overlay.profile_manager.DEFAULT_SAMPLES[current_name]
             custom_reset = True
        else:
             # Fallback for custom profiles (maybe to fire? or simple cyan?)
             # Let's use Fire as the new "System Default"
             target_colors = self.overlay.profile_manager.FIRE_COLORS
             
        self.overlay.trail_colors = [QColor(c) for c in target_colors]
        self.refresh_color_list()
        self.overlay.save_current_state()

    def edit_color(self, item):
        row = self.color_list.row(item)
        current_color = self.overlay.trail_colors[row]
        
        # Hide overlay to prevent picking the trail itself
        self.overlay.hide()
        try:
            color = QColorDialog.getColor(current_color, self, "색상 편집")
        finally:
            self.overlay.show()
            self.overlay.raise_()
            
        if color.isValid():
            self.overlay.trail_colors[row] = color
            self.refresh_color_list()
            self.overlay.save_current_state()

    # --- Other UI Updates ---
    def update_style(self, index):
        style = self.style_combo.currentData()
        if style:
            self.overlay.trail_style = style
            self.update_preview()
            self.overlay.save_current_state()

    def update_width(self, value):
        self.overlay.trail_width = value
        self.width_value_label.setText(str(value))
        self.update_preview()
        self.overlay.save_current_state()

    def update_length(self, value):
        self.overlay.trail_length = value
        self.overlay.history = collections.deque(self.overlay.history, maxlen=value)
        self.length_value_label.setText(str(value))
        self.update_preview()
        self.overlay.save_current_state()

    def update_opacity(self, state):
        self.overlay.opacity_decay = (state == 2)
        self.update_preview()
        self.overlay.save_current_state()

    def update_low_spec_enabled(self, state):
        enabled = (state == 2)
        self.low_spec_combo.setEnabled(enabled)
        if enabled:
            level = self.low_spec_combo.currentData()
            if level in (None, 0):
                level = 1
            self.overlay.set_low_spec_level(level)
        else:
            self.overlay.set_low_spec_level(0)
        self.update_preview()

    def update_low_spec_level(self, index):
        if not self.low_spec_check.isChecked():
            return
        level = self.low_spec_combo.currentData()
        if level is None:
            return
        self.overlay.set_low_spec_level(level)
        self.update_preview()

    def update_preview(self):
        self.preview.update_settings(
            self.overlay.trail_style,
            self.overlay.trail_colors,
            self.overlay.trail_width,
            self.overlay.trail_length,
            self.overlay.opacity_decay,
            self.overlay.low_spec_level
        )

class TrailOverlay(QMainWindow):
    def __init__(self):
        super().__init__()
        
        # Window Flags: Frameless, Always on Top, Tool (no taskbar icon)
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint | 
            Qt.WindowType.WindowStaysOnTopHint | 
            Qt.WindowType.Tool
        )
        
        # Attributes: Translucent background, Transparent for mouse events (PyQt level)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        
        # Resize to full virtual desktop (Multi-monitor support)
        rect = QApplication.primaryScreen().virtualGeometry()
        self.setGeometry(rect)
        
        # Windows API for click-through (Explicitly setting WS_EX_TRANSPARENT / WS_EX_LAYERED)
        hwnd = int(self.winId()) # Use int() for PySide6 compatibility or safety
        extended_style = win32gui.GetWindowLong(hwnd, win32con.GWL_EXSTYLE)
        win32gui.SetWindowLong(hwnd, win32con.GWL_EXSTYLE, extended_style | win32con.WS_EX_TRANSPARENT | win32con.WS_EX_LAYERED)
        
        # Enforce TopMost Z-Order (Above Taskbar)
        win32gui.SetWindowPos(hwnd, win32con.HWND_TOPMOST, 0, 0, 0, 0, 
                              win32con.SWP_NOMOVE | win32con.SWP_NOSIZE | win32con.SWP_NOACTIVATE)

        # Profile Manager
        self.profile_manager = ProfileManager()
        
        # Load Initial Settings (will initialize variables)
        self.load_settings()

        # Trail Logic
        self.history = collections.deque(maxlen=self.trail_length)
        self.trail_points = []
        self.last_cursor_pos = None
        self._last_trail_bounds = None

        # Timer for updates
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_overlay)
        self.topmost_timer = QTimer(self)
        self.topmost_timer.timeout.connect(self.ensure_topmost)
        self.apply_performance_mode()

        # Settings place holders - Init before tray
        # Pass None as parent to allow independent Z-ordering to prevent covering
        self.settings_dialog = SettingsDialog(self, parent=None)

        # Tray Icon - Ensure visible icon
        self.tray_icon = QSystemTrayIcon(self)
        
        # Set Tray Icon
        icon_path = resource_path("icon.png")
        if os.path.exists(icon_path):
             self.tray_icon.setIcon(QIcon(icon_path))
        else:
             # Fallback to generated icon
             pixmap = QPixmap(32, 32)
             pixmap.fill(Qt.GlobalColor.transparent)
             painter = QPainter(pixmap)
             painter.setBrush(QColor(0, 255, 255))
             painter.setPen(Qt.PenStyle.NoPen)
             painter.drawEllipse(0, 0, 32, 32)
             painter.end()
             self.tray_icon.setIcon(QIcon(pixmap))
        
        tray_menu = QMenu()
        # Note: Tray menu is outside SettingsDialog, so we access translations via SettingsDialog instance or directly.
        # But here trail_overlay.settings_dialog is available.
        # Let's make actions dynamic or just use simple Korean for now since dynamic tray update is tricky without reopening.
        # Or better -> Update tray menu on language change.
        # For simplicity, let's just make them English/Korean hybrid or define them once based on initial lang.
        # Actually, let's make a method update_tray_menu and call it.
        
        self.settings_action = QAction("Settings / 설정", self)
        self.settings_action.triggered.connect(self.open_settings)
        self.quit_action = QAction("Quit / 종료", self)
        self.quit_action.triggered.connect(self.quit_application)
        
        tray_menu.addAction(self.settings_action)
        tray_menu.addSeparator()
        tray_menu.addAction(self.quit_action)
        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.show()
        
        # Explicitly handle activation (Left Click)
        self.tray_icon.activated.connect(self.on_tray_icon_activated)
        
        # Initial text update
        self.update_tray_text()

        repair_startup_registry_entry()

        if not is_startup_launch():
            self.open_settings()
        
        # Check for updates in background
        AutoUpdater.check_and_prompt(self.settings_dialog, self.profile_manager, manual_check=False)

    def on_tray_icon_activated(self, reason):
        if reason == QSystemTrayIcon.ActivationReason.Trigger:
            self.open_settings()

    def quit_application(self):
        self.settings_dialog.force_quit = True
        QApplication.instance().quit()

    def update_tray_text(self):
        lang = self.profile_manager.language
        tr = TRANSLATIONS.get(lang, TRANSLATIONS["en"])
        
        # Manually set tray strings
        self.settings_action.setText(tr.get("title", "GoPoint"))
        self.quit_action.setText(tr.get("quit", "Quit"))
        
        # Also update tooltip
        if lang == 'ko':
             self.tray_icon.setToolTip("GoPoint (고포인트)")
        else:
             self.tray_icon.setToolTip("GoPoint")

    def open_settings(self):
        self.settings_dialog.showNormal()
        self.settings_dialog.raise_()
        self.settings_dialog.activateWindow()
        self.ensure_topmost()

    def load_settings(self):
        settings = self.profile_manager.get_current_settings()
        self.trail_style = settings.get("style", "CONSTANT")
        color_strings = settings.get("colors", ["#00FFFF"])
        self.trail_colors = [QColor(c) for c in color_strings]
        self.trail_width = settings.get("width", 12)
        self.trail_length = settings.get("length", 20)
        self.opacity_decay = settings.get("opacity_decay", True)
        self.low_spec_level = self.profile_manager.low_spec_level
        
        # Reset history maxlen
        if hasattr(self, 'history'):
            self.history = collections.deque(self.history, maxlen=self.trail_length)
        if hasattr(self, 'timer'):
            self.apply_performance_mode()

    def save_current_state(self):
        settings = {
            "style": self.trail_style,
            "colors": [c.name() for c in self.trail_colors],
            "width": self.trail_width,
            "length": self.trail_length,
            "opacity_decay": self.opacity_decay
        }
        self.profile_manager.save_profile(self.profile_manager.current_profile, settings)

    def set_low_spec_mode(self, enabled):
        self.profile_manager.set_low_spec_mode(enabled)
        self.low_spec_level = self.profile_manager.low_spec_level
        self.apply_performance_mode()

    def set_low_spec_level(self, level):
        self.profile_manager.set_low_spec_level(level)
        self.low_spec_level = self.profile_manager.low_spec_level
        self.apply_performance_mode()

    def apply_performance_mode(self):
        self.low_spec_level = self.profile_manager.low_spec_level
        preset = get_performance_preset(self.low_spec_level, preview=False)
        self.smoothing_iterations = preset["smoothing_iterations"]
        self.timer.setInterval(preset["interval_ms"])
        if not self.timer.isActive():
            self.timer.start()
        self.topmost_timer.setInterval(TOPMOST_REFRESH_INTERVAL_MS)
        if not self.topmost_timer.isActive():
            self.topmost_timer.start()

    def ensure_topmost(self):
        hwnd = int(self.winId())
        win32gui.SetWindowPos(
            hwnd,
            win32con.HWND_TOPMOST,
            0,
            0,
            0,
            0,
            win32con.SWP_NOMOVE | win32con.SWP_NOSIZE | win32con.SWP_NOACTIVATE
        )

    def _trail_is_settled(self, target):
        if not self.trail_points:
            return False

        for point in self.trail_points:
            if abs(point.x() - target.x()) > TRAIL_SETTLE_EPSILON:
                return False
            if abs(point.y() - target.y()) > TRAIL_SETTLE_EPSILON:
                return False
        return True

    def _history_bounds(self, points):
        if not points:
            return None

        margin = max(8, int(self.trail_width) + 6)
        xs = [point.x() for point in points]
        ys = [point.y() for point in points]
        left = max(0, math.floor(min(xs) - margin))
        top = max(0, math.floor(min(ys) - margin))
        right = min(self.width() - 1, math.ceil(max(xs) + margin))
        bottom = min(self.height() - 1, math.ceil(max(ys) + margin))

        return QRect(left, top, max(1, right - left + 1), max(1, bottom - top + 1))

    def _repaint_trail(self, previous_bounds):
        new_bounds = self._history_bounds(self.history)
        dirty_rect = new_bounds or previous_bounds
        if previous_bounds and new_bounds:
            dirty_rect = previous_bounds.united(new_bounds)

        self._last_trail_bounds = new_bounds

        if dirty_rect:
            self.update(dirty_rect)
        else:
            self.update()

    def update_overlay(self):
        pos = QCursor.pos()
        mapped_pos = QPointF(self.mapFromGlobal(pos))
        previous_bounds = self._last_trail_bounds
        
        if len(self.trail_points) != self.trail_length:
            if len(self.trail_points) == 0:
                self.trail_points = [mapped_pos for _ in range(self.trail_length)]
            else:
                while len(self.trail_points) < self.trail_length:
                    self.trail_points.append(self.trail_points[-1])
                self.trail_points = self.trail_points[:self.trail_length]
            self.history = collections.deque(self.trail_points, maxlen=self.trail_length)
            self.last_cursor_pos = QPoint(pos)
            self._repaint_trail(previous_bounds)
            return

        moved = self.last_cursor_pos is None or pos != self.last_cursor_pos
        self.last_cursor_pos = QPoint(pos)

        if not moved and self._trail_is_settled(mapped_pos):
            return

        self.trail_points[0] = mapped_pos
        for i in range(1, self.trail_length):
            c = self.trail_points[i]
            t = self.trail_points[i-1]
            self.trail_points[i] = QPointF(c.x() + (t.x() - c.x()) * 0.45, 
                                           c.y() + (t.y() - c.y()) * 0.45)
            
        self.history = collections.deque(self.trail_points, maxlen=self.trail_length)
        self._repaint_trail(previous_bounds)

    def paintEvent(self, event):
        painter = QPainter(self)
        draw_trail(
            painter, 
            self.history, 
            self.trail_style, 
            self.trail_colors, 
            self.trail_width, 
            self.trail_length, 
            self.opacity_decay,
            smoothing_iterations=self.smoothing_iterations
        )

if __name__ == "__main__":
    app = QApplication(sys.argv)
    server_name = get_single_instance_server_name()
    activation_message = SINGLE_INSTANCE_MESSAGE_NOOP if is_startup_launch() else SINGLE_INSTANCE_MESSAGE_SHOW_SETTINGS
    if notify_existing_instance(server_name, activation_message):
        sys.exit(0)

    single_instance_server = SingleInstanceServer(server_name, None, app)
    if not single_instance_server.start():
        sys.exit(1)
    set_single_instance_server(single_instance_server)
    
    # Set Application Icon
    icon_path = resource_path("icon.png")
    if os.path.exists(icon_path):
        app.setWindowIcon(QIcon(icon_path))
    
    # Ensure the overlay covers the whole virtual desktop if multiple monitors
    # For now, just primary screen logic is in __init__, can be expanded.
    
    # Cleanup old update files
    AutoUpdater.cleanup()
    
    overlay = TrailOverlay()
    single_instance_server.set_activation_callback(overlay.open_settings)
    app.aboutToQuit.connect(single_instance_server.close)
    overlay.show()
    
    sys.exit(app.exec())
