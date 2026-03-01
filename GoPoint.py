# -*- coding: utf-8 -*-
import locale
import sys
import os
import json
import collections
import math
import shutil
import webbrowser # For opening links

# ... Imports ...
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QSystemTrayIcon, 
                             QMenu, QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                             QSlider, QComboBox, QPushButton, QColorDialog, QCheckBox,
                             QListWidget, QListWidgetItem, QInputDialog, QMessageBox,
                             QStyledItemDelegate, QStyle, QStyleOptionViewItem, QAbstractItemView,
                             QTextBrowser)
from PyQt6.QtCore import Qt, QTimer, QPoint, QSize, QEvent
from PyQt6.QtGui import (QAction, QIcon, QColor, QPainter, QPen, QBrush, 
                         QPolygonF, QCursor, QFont, QLinearGradient)

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
import threading
import tempfile
import subprocess

APP_VERSION = "1.0.6"


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
        "changelog": """<h2>Ver 1.0.6</h2>
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
        "changelog": """<h2>Ver 1.0.6</h2>
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
        "changelog": """<h2>Ver 1.0.6</h2>
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

def draw_trail(painter, history, style, colors, width_factor, length, opacity_decay):
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
    if style in ["CONSTANT", "TAPERED"]:
        history = smooth_points(history)
    
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

class PreviewWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(150)
        self.setStyleSheet("background-color: #222; border: 1px solid #444; border-radius: 5px;")
        
        self.history = collections.deque(maxlen=20)
        self.angle = 0
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_animation)
        self.timer.start(16)
        
        # Default settings
        self.trail_style = "TAPERED"
        self.trail_colors = [QColor("#00FFFF")]
        self.trail_width = 15
        self.trail_length = 20
        self.opacity_decay = True

    def update_settings(self, style, colors, width, length, decay):
        self.trail_style = style
        self.trail_colors = colors
        self.trail_width = width
        self.trail_length = length
        self.opacity_decay = decay
        self.history = collections.deque(self.history, maxlen=length)

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
        draw_trail(painter, self.history, self.trail_style, self.trail_colors, self.trail_width, self.trail_length, self.opacity_decay)


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
        
        # Force update Default to match Fire (explicitly)
        fire_settings = {
            "style": "CONSTANT",
            "colors": self.FIRE_COLORS,
            "width": 12,
            "length": 20,
            "opacity_decay": True
        }
        if self.profiles.get("Default") != fire_settings:
            # Check if it was the old single cyan default, or just ensure it matches fire
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
            "language": self.language
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
            sys_lang, _ = locale.getdefaultlocale()
            if sys_lang:
                if sys_lang.startswith('ko'): return 'ko'
                if sys_lang.startswith('ja'): return 'ja'
                if sys_lang.startswith('es'): return 'es'
                if sys_lang.startswith('zh'): return 'zh'
                if sys_lang.startswith('fr'): return 'fr'
                if sys_lang.startswith('de'): return 'de'
                if sys_lang.startswith('ru'): return 'ru'
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

class AutoUpdater:
    @staticmethod
    def check_and_prompt(parent_widget, profile_manager, manual_check=False):
        def _check():
            try:
                url = 'https://api.github.com/repos/ruruoni1/GoPoint/releases/latest'
                req = urllib.request.Request(url, headers={'User-Agent': 'GoPoint-Updater'})
                with urllib.request.urlopen(req, timeout=5) as response:
                    data = json.loads(response.read().decode())
                    latest_version_tag = data.get('tag_name', '')
                    latest_version = latest_version_tag.lstrip('v')
                    
                    if latest_version > APP_VERSION:
                        asset_url = None
                        for asset in data.get('assets', []):
                            if asset['name'].endswith('.exe'):
                                asset_url = asset['browser_download_url']
                                break
                        
                        if asset_url:
                            # Prompt user in main thread
                            QTimer.singleShot(0, lambda: AutoUpdater._prompt_update(parent_widget, profile_manager, latest_version, asset_url))
                    elif manual_check:
                        QTimer.singleShot(0, lambda: AutoUpdater._notify_latest(parent_widget, profile_manager))
            except Exception as e:
                print(f"Update check failed: {e}")
                if manual_check:
                    QTimer.singleShot(0, lambda: AutoUpdater._notify_error(parent_widget, profile_manager))
                    
        threading.Thread(target=_check, daemon=True).start()

    @staticmethod
    def _get_tr(profile_manager, key):
        lang = profile_manager.language
        return TRANSLATIONS.get(lang, TRANSLATIONS["en"]).get(key, key)

    @staticmethod
    def _notify_latest(parent_widget, profile_manager):
        QMessageBox.information(parent_widget, 
                                AutoUpdater._get_tr(profile_manager, "update_available"), 
                                AutoUpdater._get_tr(profile_manager, "update_latest"))
                                
    @staticmethod
    def _notify_error(parent_widget, profile_manager):
        QMessageBox.warning(parent_widget, 
                            AutoUpdater._get_tr(profile_manager, "update_available"), 
                            AutoUpdater._get_tr(profile_manager, "update_error"))

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
    def _perform_update(parent_widget, profile_manager, download_url):
        # Prevent further interaction
        if hasattr(parent_widget, 'setEnabled'):
            parent_widget.setEnabled(False)
            
        def _download():
            try:
                import shutil
                temp_exe = os.path.join(tempfile.gettempdir(), "GoPoint_update.exe")
                req = urllib.request.Request(download_url, headers={'User-Agent': 'GoPoint-Updater'})
                with urllib.request.urlopen(req, timeout=30) as response, open(temp_exe, 'wb') as out_file:
                    shutil.copyfileobj(response, out_file)
                
                # Create bat script to replace running exe
                current_exe = sys.executable if getattr(sys, 'frozen', False) else os.path.abspath(__file__)
                if not getattr(sys, 'frozen', False):
                    print("Update downloaded to temp, but running in dev mode. Skipping replace.")
                    return
                
                bat_path = os.path.join(tempfile.gettempdir(), "update_gopoint.bat")
                bat_content = f'''@echo off
echo Updating GoPoint...
ping 127.0.0.1 -n 3 > nul
move /y "{temp_exe}" "{current_exe}"
start "" "{current_exe}"
del "%~f0"
'''
                with open(bat_path, 'w', encoding='utf-8') as f:
                    f.write(bat_content)
                
                # Execute bat and quit
                subprocess.Popen(bat_path, shell=True)
                QTimer.singleShot(0, QApplication.instance().quit)
                
            except Exception as e:
                print(f"Update download failed: {e}")
                QTimer.singleShot(0, lambda: AutoUpdater._notify_error(parent_widget, profile_manager))
                if hasattr(parent_widget, 'setEnabled'):
                    QTimer.singleShot(0, lambda: parent_widget.setEnabled(True))
                    
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
        self.update_preview()
        
    def check_startup_registry(self):
        try:
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Run", 0, winreg.KEY_READ)
            value, _ = winreg.QueryValueEx(key, "GoPoint")
            winreg.CloseKey(key)
            return True
        except FileNotFoundError:
            return False
        except Exception:
            return False

    def apply_startup_setting(self):
        state = 2 if self.startup_check.isChecked() else 0
        self.toggle_startup(state)
        QMessageBox.information(self, self.tr("title"), self.tr("startup_applied"))

    def toggle_startup(self, state):
        key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
        app_name = "GoPoint"
        exe_path = sys.executable
        if not getattr(sys, 'frozen', False):
             print(f"Startup toggle: {state} (Not frozen, skipping registry write)")
             return

        try:
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_WRITE)
            if state == 2: # Checked
                winreg.SetValueEx(key, app_name, 0, winreg.REG_SZ, exe_path)
            else: # Unchecked
                try:
                    winreg.DeleteValue(key, app_name)
                except FileNotFoundError:
                    pass
            winreg.CloseKey(key)
        except Exception as e:
            print(f"Registry Error: {e}")

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

    # --- Profile Methods ---
    def tr(self, key):
        lang = self.overlay.profile_manager.language
        return TRANSLATIONS.get(lang, TRANSLATIONS["en"]).get(key, key)

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

    def update_preview(self):
        self.preview.update_settings(
            self.overlay.trail_style,
            self.overlay.trail_colors,
            self.overlay.trail_width,
            self.overlay.trail_length,
            self.overlay.opacity_decay
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

        # Timer for updates
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_overlay)
        self.timer.start(16) # ~60 FPS

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
        
        # Show settings on startup
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
        self.settings_dialog.activateWindow()

    def load_settings(self):
        settings = self.profile_manager.get_current_settings()
        self.trail_style = settings.get("style", "CONSTANT")
        color_strings = settings.get("colors", ["#00FFFF"])
        self.trail_colors = [QColor(c) for c in color_strings]
        self.trail_width = settings.get("width", 12)
        self.trail_length = settings.get("length", 20)
        self.opacity_decay = settings.get("opacity_decay", True)
        
        # Reset history maxlen
        if hasattr(self, 'history'):
            self.history = collections.deque(self.history, maxlen=self.trail_length)

    def save_current_state(self):
        settings = {
            "style": self.trail_style,
            "colors": [c.name() for c in self.trail_colors],
            "width": self.trail_width,
            "length": self.trail_length,
            "opacity_decay": self.opacity_decay
        }
        self.profile_manager.save_profile(self.profile_manager.current_profile, settings)

    def open_settings(self):
        self.settings_dialog.showNormal()
        self.settings_dialog.activateWindow()

    def update_overlay(self):
        # Update history
        pos = QCursor.pos()
        mapped_pos_int = self.mapFromGlobal(pos)
        mapped_pos = QPointF(mapped_pos_int)
        
        # Initialize or resize trail points
        if not hasattr(self, 'trail_points') or len(self.trail_points) != self.trail_length:
            if not hasattr(self, 'trail_points') or len(self.trail_points) == 0:
                self.trail_points = [mapped_pos for _ in range(self.trail_length)]
            else:
                while len(self.trail_points) < self.trail_length:
                    self.trail_points.append(self.trail_points[-1])
                self.trail_points = self.trail_points[:self.trail_length]
                    
        # Apply follow (spring) algorithm for silky smooth tracking
        self.trail_points[0] = mapped_pos
        for i in range(1, self.trail_length):
            c = self.trail_points[i]
            t = self.trail_points[i-1]
            # Easing factor: 0.45 gives a nice balance of tracking speed and smoothness
            self.trail_points[i] = QPointF(c.x() + (t.x() - c.x()) * 0.45, 
                                           c.y() + (t.y() - c.y()) * 0.45)
            
        # Update history for rendering
        self.history = collections.deque(self.trail_points, maxlen=self.trail_length)
            
        self.update()
        # Force overlay to be on top of everything, including the settings window
        self.raise_()
        
        # Enforce TopMost Z-Order continuously (Fix for Taskbar/Start Menu)
        hwnd = int(self.winId())
        win32gui.SetWindowPos(hwnd, win32con.HWND_TOPMOST, 0, 0, 0, 0, 
                              win32con.SWP_NOMOVE | win32con.SWP_NOSIZE | win32con.SWP_NOACTIVATE)

    def paintEvent(self, event):
        painter = QPainter(self)
        draw_trail(
            painter, 
            self.history, 
            self.trail_style, 
            self.trail_colors, 
            self.trail_width, 
            self.trail_length, 
            self.opacity_decay
        )

if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    # Set Application Icon
    icon_path = resource_path("icon.png")
    if os.path.exists(icon_path):
        app.setWindowIcon(QIcon(icon_path))
    
    # Ensure the overlay covers the whole virtual desktop if multiple monitors
    # For now, just primary screen logic is in __init__, can be expanded.
    
    overlay = TrailOverlay()
    overlay.show()
    
    sys.exit(app.exec())
