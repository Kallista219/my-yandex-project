# =====================================================================
# МУЗЫКАЛЬНЫЙ MP3-ПЛЕЕР "LYCEUM BEATS"
# Автор: Хиценко Анастасия
# Проект для Яндекс.Лицея (PyQt5 + SQLite + CSV/TXT)
# =====================================================================

import csv
import os
import sqlite3
import sys
from datetime import datetime

from PyQt5.QtCore import Qt, QTimer, QUrl
from PyQt5.QtGui import QColor, QFont, QPainter, QPixmap
from PyQt5.QtMultimedia import QMediaContent, QMediaPlayer
from PyQt5.QtWidgets import (
    QAction,
    QApplication,
    QCheckBox,
    QComboBox,
    QDialog,
    QFileDialog,
    QFormLayout,
    QHBoxLayout,
    QHeaderView,
    QLCDNumber,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QSlider,
    QStatusBar,
    QTableWidget,
    QTableWidgetItem,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

# Главные настройки программы: размеры окна, файл базы данных и фильтры
APP_TITLE = "Lyceum Beats — MP3 Player"
WINDOW_MIN_WIDTH = 980
WINDOW_MIN_HEIGHT = 650

DATABASE_FILENAME = "music_library.sqlite"
DEFAULT_VOLUME_PERCENT = 70
TIMER_UPDATE_INTERVAL_MS = 500
COVER_IMAGE_SIZE = 180
DEFAULT_PLAYLIST_ID = 1

SUPPORTED_AUDIO_FILTER = "Аудиофайлы (*.mp3 *.wav *.ogg);;Все файлы (*)"
CSV_FILE_FILTER = "CSV таблицы (*.csv)"
TXT_FILE_FILTER = "Текстовые файлы (*.txt)"

# Оформление программы: Тёмная и Светлая темы (используется шрифт Segoe UI)
DARK_THEME_QSS = """
QMainWindow, QDialog {
    background-color: #121212; color: #FFFFFF;
    font-family: "Segoe UI", Arial, sans-serif; font-size: 13px;
}
QLabel, QCheckBox {
    color: #FFFFFF; font-family: "Segoe UI", Arial, sans-serif;
}
QPushButton {
    background-color: #282828; color: #FFFFFF;
    border: 1px solid #3E3E3E; border-radius: 8px;
    padding: 6px 14px; font-weight: 600; font-family: "Segoe UI", Arial, sans-serif;
}
QPushButton:hover { background-color: #3E3E3E; border-color: #FF69B4; color: #FF69B4; }
QPushButton#RoundButton {
    background-color: #1E1E1E; color: #FFFFFF;
    border-radius: 22px; font-size: 16px; font-weight: bold;
    min-width: 44px; min-height: 44px; max-width: 44px; max-height: 44px;
    border: 1px solid #333333; padding: 0px;
}
QPushButton#RoundButton:hover {
    background-color: #2C2C2C; border-color: #FF69B4; color: #FF69B4;
}
QLineEdit, QComboBox, QTextEdit, QListWidget, QTableWidget {
    background-color: #181818; color: #FFFFFF;
    border: 1px solid #282828; border-radius: 6px; padding: 6px;
    font-family: "Segoe UI", Arial, sans-serif;
}
QHeaderView::section {
    background-color: #181818; color: #FFFFFF; padding: 6px; border: none; font-weight: bold;
    font-family: "Segoe UI", Arial, sans-serif;
}
QTableWidget { gridline-color: #282828; }
QTableWidget::item { color: #FFFFFF; }
QSlider::groove:horizontal { height: 4px; background: #535353; border-radius: 2px; }
QSlider::sub-page:horizontal { background: #FF69B4; border-radius: 2px; }
QSlider::handle:horizontal {
    background: #FFFFFF; width: 12px; height: 12px; margin: -4px 0; border-radius: 6px;
}
QSlider::handle:horizontal:hover { background: #FF69B4; }
"""

LIGHT_THEME_QSS = """
QMainWindow, QDialog {
    background-color: #F8F9FA; color: #191414;
    font-family: "Segoe UI", Arial, sans-serif; font-size: 13px;
}
QLabel, QCheckBox {
    color: #191414; font-family: "Segoe UI", Arial, sans-serif;
}
QPushButton {
    background-color: #E0E0E0; color: #191414;
    border: 1px solid #CCCCCC; border-radius: 8px;
    padding: 6px 14px; font-weight: 600; font-family: "Segoe UI", Arial, sans-serif;
}
QPushButton:hover { background-color: #D0D0D0; border-color: #FF69B4; color: #FF69B4; }
QPushButton#RoundButton {
    background-color: #FFFFFF; color: #191414;
    border-radius: 22px; font-size: 16px; font-weight: bold;
    min-width: 44px; min-height: 44px; max-width: 44px; max-height: 44px;
    border: 1px solid #CCCCCC; padding: 0px;
}
QPushButton#RoundButton:hover {
    background-color: #F0F0F0; border-color: #FF69B4; color: #FF69B4;
}
QLineEdit, QComboBox, QTextEdit, QListWidget, QTableWidget {
    background-color: #FFFFFF; color: #191414;
    border: 1px solid #CCCCCC; border-radius: 6px; padding: 6px;
    font-family: "Segoe UI", Arial, sans-serif;
}
QHeaderView::section {
    background-color: #EDEDED; color: #191414; padding: 6px; border: none; font-weight: bold;
    font-family: "Segoe UI", Arial, sans-serif;
}
QTableWidget { gridline-color: #E0E0E0; }
QTableWidget::item { color: #191414; }
QSlider::groove:horizontal { height: 4px; background: #CCCCCC; border-radius: 2px; }
QSlider::sub-page:horizontal { background: #FF69B4; border-radius: 2px; }
QSlider::handle:horizontal {
    background: #191414; width: 12px; height: 12px; margin: -4px 0; border-radius: 6px;
}
"""

THEMES_DICTIONARY = {"Тёмная": DARK_THEME_QSS, "Светлая": LIGHT_THEME_QSS}


# =====================================================================
# ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ И ДОП. КЛАССЫ
# =====================================================================
class ClickableSlider(QSlider):
    """Делает шкалу времени плеера кликабельной (можно сразу мотать песню мышкой)."""

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            val = self.minimum() + (self.maximum() - self.minimum()) * event.x() / self.width()
            self.setValue(int(val))
            self.sliderMoved.emit(int(val))
            event.accept()
        super().mousePressEvent(event)


def format_milliseconds(ms):
    """Переводит миллисекунды в красивый формат времени ММ:СС."""
    sec = max(0, int(ms) // 1000)
    return f"{sec // 60:02d}:{sec % 60:02d}"


def split_filename(path):
    """Достает из имени файла автора и название песни."""
    try:
        norm_path = os.path.normpath(path)
        base_name = os.path.basename(norm_path)
        name = os.path.splitext(base_name)[0].strip()
        if " - " in name:
            artist, title = name.split(" - ", 1)
            return artist.strip(), title.strip()
        return "Неизвестный исполнитель", name or "Без названия"
    except Exception:
        return "Неизвестный исполнитель", "Аудио трек"


def calculate_percentage(part, total):
    """Считает проценты для полосы заполнения в статистике."""
    return int((part / total) * 100) if total > 0 else 0


def generate_cover(title="Трек"):
    """Рисует картинку-пластинку с названием песни для левой панели."""
    pixmap = QPixmap(COVER_IMAGE_SIZE, COVER_IMAGE_SIZE)
    pixmap.fill(Qt.transparent)
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.Antialiasing)
    painter.setBrush(QColor("#181818"))
    painter.setPen(QColor("#282828"))
    painter.drawRoundedRect(0, 0, COVER_IMAGE_SIZE, COVER_IMAGE_SIZE, 12, 12)

    painter.setBrush(QColor("#FF69B4"))
    painter.drawEllipse(55, 55, COVER_IMAGE_SIZE - 110, COVER_IMAGE_SIZE - 110)
    painter.setBrush(QColor("#121212"))
    painter.drawEllipse(82, 82, 16, 16)

    painter.setPen(QColor("#FFFFFF"))
    painter.setFont(QFont("Segoe UI", 9, QFont.Bold))
    short = title[:14] + "..." if len(title) > 14 else title
    painter.drawText(10, COVER_IMAGE_SIZE - 35, COVER_IMAGE_SIZE - 20, 25, Qt.AlignCenter, short)
    painter.end()
    return pixmap


# =====================================================================
# РАБОТА С БАЗОЙ ДАННЫХ (SQLite, 3 таблицы)
# =====================================================================
class DatabaseManager:
    """Управляет базой данных: сохраняет треки, плейлисты и настройки."""

    def __init__(self, db_path=DATABASE_FILENAME):
        self.conn = sqlite3.connect(db_path)
        self.conn.row_factory = sqlite3.Row
        self.create_tables()
        self.init_defaults()

    def create_tables(self):
        cur = self.conn.cursor()
        # Таблица 1: Плейлисты
        cur.execute(
            "CREATE TABLE IF NOT EXISTS playlists (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL UNIQUE, description TEXT DEFAULT '', created_at TEXT NOT NULL)")
        # Таблица 2: Треки (связана с плейлистами)
        cur.execute(
            "CREATE TABLE IF NOT EXISTS tracks (id INTEGER PRIMARY KEY AUTOINCREMENT, title TEXT NOT NULL, artist TEXT NOT NULL, genre TEXT DEFAULT 'Другое', file_path TEXT NOT NULL, playlist_id INTEGER NOT NULL, is_favorite INTEGER DEFAULT 0, play_count INTEGER DEFAULT 0, FOREIGN KEY(playlist_id) REFERENCES playlists(id) ON DELETE CASCADE)")
        # Таблица 3: Настройки приложения (тема, громкость)
        cur.execute(
            "CREATE TABLE IF NOT EXISTS app_settings (setting_key TEXT PRIMARY KEY, setting_value TEXT NOT NULL)")
        self.conn.commit()

    def init_defaults(self):
        cur = self.conn.cursor()
        cur.execute("SELECT COUNT(*) as c FROM playlists")
        if cur.fetchone()["c"] == 0:
            now = datetime.now().strftime("%Y-%m-%d %H:%M")
            cur.executemany("INSERT INTO playlists (name, description, created_at) VALUES (?, ?, ?)", [
                ("Все треки", "Основной плейлист", now),
                ("Любимые треки", "Избранная музыка", now)
            ])
            self.conn.commit()

    def get_all_playlists(self):
        return self.conn.cursor().execute("SELECT * FROM playlists ORDER BY id").fetchall()

    def add_playlist(self, name, desc=""):
        cur = self.conn.cursor()
        cur.execute("INSERT INTO playlists (name, description, created_at) VALUES (?, ?, ?)",
                    (name.strip(), desc.strip(), datetime.now().strftime("%Y-%m-%d %H:%M")))
        self.conn.commit()

    def update_playlist(self, pid, name, desc):
        cur = self.conn.cursor()
        cur.execute("UPDATE playlists SET name = ?, description = ? WHERE id = ?", (name.strip(), desc.strip(), pid))
        self.conn.commit()

    def delete_playlist(self, pid):
        if pid == DEFAULT_PLAYLIST_ID:
            return False
        cur = self.conn.cursor()
        cur.execute("DELETE FROM tracks WHERE playlist_id = ?", (pid,))
        cur.execute("DELETE FROM playlists WHERE id = ?", (pid,))
        self.conn.commit()
        return True

    def add_track(self, title, artist, path, pid):
        cur = self.conn.cursor()
        cur.execute("INSERT INTO tracks (title, artist, file_path, playlist_id) VALUES (?, ?, ?, ?)",
                    (title.strip(), artist.strip(), path, pid))
        self.conn.commit()

    def get_filtered_tracks(self, pid=None, search="", only_fav=False):
        cur = self.conn.cursor()
        query = "SELECT tracks.*, playlists.name AS playlist_name FROM tracks JOIN playlists ON tracks.playlist_id = playlists.id WHERE 1=1"
        params = []
        if pid and pid > DEFAULT_PLAYLIST_ID:
            query += " AND tracks.playlist_id = ?"
            params.append(pid)
        if search.strip():
            query += " AND (LOWER(tracks.title) LIKE ? OR LOWER(tracks.artist) LIKE ?)"
            pat = f"%{search.strip().lower()}%"
            params.extend([pat, pat])
        if only_fav:
            query += " AND tracks.is_favorite = 1"
        query += " ORDER BY tracks.id DESC"
        return cur.execute(query, params).fetchall()

    def get_track(self, tid):
        return self.conn.cursor().execute("SELECT * FROM tracks WHERE id = ?", (tid,)).fetchone()

    def update_track(self, tid, title, artist, pid, fav):
        cur = self.conn.cursor()
        cur.execute("UPDATE tracks SET title = ?, artist = ?, playlist_id = ?, is_favorite = ? WHERE id = ?",
                    (title.strip(), artist.strip(), pid, int(fav), tid))
        self.conn.commit()

    def toggle_fav(self, tid):
        t = self.get_track(tid)
        if t:
            val = 0 if t["is_favorite"] else 1
            self.conn.cursor().execute("UPDATE tracks SET is_favorite = ? WHERE id = ?", (val, tid))
            self.conn.commit()

    def inc_plays(self, tid):
        self.conn.cursor().execute("UPDATE tracks SET play_count = play_count + 1 WHERE id = ?", (tid,))
        self.conn.commit()

    def delete_track(self, tid):
        self.conn.cursor().execute("DELETE FROM tracks WHERE id = ?", (tid,))
        self.conn.commit()

    def get_stats(self):
        cur = self.conn.cursor()
        tot = cur.execute("SELECT COUNT(*) as c FROM tracks").fetchone()["c"]
        fav = cur.execute("SELECT COUNT(*) as c FROM tracks WHERE is_favorite = 1").fetchone()["c"]
        plays = cur.execute("SELECT COALESCE(SUM(play_count), 0) as s FROM tracks").fetchone()["s"]
        top = cur.execute("SELECT title, artist, play_count FROM tracks ORDER BY play_count DESC LIMIT 5").fetchall()
        return {"total": tot, "fav": fav, "plays": plays, "top": top}

    def save_setting(self, k, v):
        cur = self.conn.cursor()
        cur.execute(
            "INSERT INTO app_settings (setting_key, setting_value) VALUES (?, ?) ON CONFLICT(setting_key) DO UPDATE SET setting_value = excluded.setting_value",
            (k, str(v)))
        self.conn.commit()

    def get_setting(self, k, default=""):
        row = self.conn.cursor().execute("SELECT setting_value FROM app_settings WHERE setting_key = ?",
                                         (k,)).fetchone()
        return row["setting_value"] if row else default

    def close(self):
        self.conn.close()


# =====================================================================
# ОКОШКО "О ПРОГРАММЕ" (АВТОР)
# =====================================================================
class AboutDialog(QDialog):
    """Выводит информацию об авторе программы (Хиценко Анастасия)."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("О программе")
        self.setFixedSize(320, 200)

        layout = QVBoxLayout(self)

        title_label = QLabel("🎵 Lyceum Beats")
        title_label.setFont(QFont("Segoe UI", 14, QFont.Bold))
        title_label.setAlignment(Qt.AlignCenter)

        author_label = QLabel("Автор проекта:\nХиценко Анастасия")
        author_label.setFont(QFont("Segoe UI", 11))
        author_label.setAlignment(Qt.AlignCenter)

        desc_label = QLabel("Учебный проект для Яндекс.Лицея\nМузыкальный MP3-плеер на PyQt5")
        desc_label.setAlignment(Qt.AlignCenter)

        ok_btn = QPushButton("Закрыть")
        ok_btn.clicked.connect(self.accept)

        layout.addWidget(title_label)
        layout.addWidget(author_label)
        layout.addWidget(desc_label)
        layout.addWidget(ok_btn)


# =====================================================================
# ФОРМА №2: ОКНО РЕДАКТИРОВАНИЯ ТРЕКА
# =====================================================================
class TrackEditorDialog(QDialog):
    """Позволяет изменить название, исполнителя и плейлист песни."""

    def __init__(self, db, tid, parent=None):
        super().__init__(parent)
        self.db = db
        self.tid = tid
        self.data = self.db.get_track(tid)
        self.setWindowTitle("Редактирование трека")
        self.setMinimumWidth(380)
        self.setup_ui()
        self.fill_data()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        form = QFormLayout()
        self.t_input = QLineEdit()
        self.a_input = QLineEdit()
        self.p_combo = QComboBox()
        for p in self.db.get_all_playlists():
            self.p_combo.addItem(p["name"], p["id"])
        self.fav_box = QCheckBox("В избранном")
        form.addRow("Название:", self.t_input)
        form.addRow("Исполнитель:", self.a_input)
        form.addRow("Плейлист:", self.p_combo)
        form.addRow("", self.fav_box)
        layout.addLayout(form)

        btns = QHBoxLayout()
        save_b = QPushButton("Сохранить")
        cancel_b = QPushButton("Отмена")
        save_b.clicked.connect(self.save)
        cancel_b.clicked.connect(self.reject)
        btns.addWidget(save_b)
        btns.addWidget(cancel_b)
        layout.addLayout(btns)

    def fill_data(self):
        if not self.data:
            return
        self.t_input.setText(self.data["title"])
        self.a_input.setText(self.data["artist"])
        idx = self.p_combo.findData(self.data["playlist_id"])
        if idx >= 0:
            self.p_combo.setCurrentIndex(idx)
        self.fav_box.setChecked(bool(self.data["is_favorite"]))

    def save(self):
        t, a = self.t_input.text().strip(), self.a_input.text().strip()
        if not t or not a:
            QMessageBox.warning(self, "Ошибка", "Заполните название и исполнителя!")
            return
        self.db.update_track(self.tid, t, a, self.p_combo.currentData(), self.fav_box.isChecked())
        self.accept()


# =====================================================================
# ФОРМА №3: ОКНО УПРАВЛЕНИЯ ПЛЕЙЛИСТАМИ
# =====================================================================
class PlaylistManagerDialog(QDialog):
    """Здесь можно создавать новые плейлисты, менять их или удалять."""

    def __init__(self, db, parent=None):
        super().__init__(parent)
        self.db = db
        self.setWindowTitle("Управление плейлистами")
        self.setMinimumSize(460, 360)
        self.setup_ui()
        self.load_pl()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Плейлисты библиотеки:"))
        self.list_w = QListWidget()
        self.list_w.currentItemChanged.connect(self.select_item)
        layout.addWidget(self.list_w)

        form = QFormLayout()
        self.n_input = QLineEdit()
        self.d_input = QTextEdit()
        self.d_input.setMaximumHeight(60)
        form.addRow("Название:", self.n_input)
        form.addRow("Описание:", self.d_input)
        layout.addLayout(form)

        btns = QHBoxLayout()
        c_btn = QPushButton("Создать")
        u_btn = QPushButton("Изменить")
        d_btn = QPushButton("Удалить")
        c_btn.clicked.connect(self.create)
        u_btn.clicked.connect(self.update)
        d_btn.clicked.connect(self.delete)
        btns.addWidget(c_btn)
        btns.addWidget(u_btn)
        btns.addWidget(d_btn)
        layout.addLayout(btns)

    def load_pl(self):
        self.list_w.clear()
        for p in self.db.get_all_playlists():
            item = QListWidgetItem(f"{p['name']} — ({p['description'] or 'нет описания'})")
            item.setData(Qt.UserRole, dict(p))
            self.list_w.addItem(item)

    def select_item(self, item):
        if item:
            d = item.data(Qt.UserRole)
            self.n_input.setText(d["name"])
            self.d_input.setPlainText(d["description"])

    def create(self):
        n, desc = self.n_input.text().strip(), self.d_input.toPlainText().strip()
        if not n:
            return
        try:
            self.db.add_playlist(n, desc)
            self.load_pl()
            self.n_input.clear()
            self.d_input.clear()
        except sqlite3.IntegrityError:
            QMessageBox.warning(self, "Ошибка", "Плейлист уже существует!")

    def update(self):
        cur = self.list_w.currentItem()
        if not cur:
            return
        d = cur.data(Qt.UserRole)
        try:
            self.db.update_playlist(d["id"], self.n_input.text().strip(), self.d_input.toPlainText().strip())
            self.load_pl()
        except sqlite3.IntegrityError:
            QMessageBox.warning(self, "Ошибка", "Имя занято!")

    def delete(self):
        cur = self.list_w.currentItem()
        if not cur:
            return
        d = cur.data(Qt.UserRole)
        if d["id"] == DEFAULT_PLAYLIST_ID:
            QMessageBox.warning(self, "Ошибка", "Нельзя удалить базовый плейлист!")
            return
        if QMessageBox.question(self, "Удаление", f"Удалить плейлист '{d['name']}'?",
                                QMessageBox.Yes | QMessageBox.No) == QMessageBox.Yes:
            self.db.delete_playlist(d["id"])
            self.load_pl()


# =====================================================================
# ФОРМА №4: ОКНО СТАТИСТИКИ
# =====================================================================
class StatisticsDialog(QDialog):
    """Показывает общую статистику, топ треков и позволяет выгрузить отчет в TXT."""

    def __init__(self, db, parent=None):
        super().__init__(parent)
        self.db = db
        self.stats = self.db.get_stats()
        self.setWindowTitle("Статистика прослушиваний")
        self.setMinimumSize(520, 400)
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        lcd_layout = QHBoxLayout()

        t_box = QVBoxLayout()
        t_box.addWidget(QLabel("Всего треков:"))
        self.t_lcd = QLCDNumber()
        self.t_lcd.display(self.stats["total"])
        t_box.addWidget(self.t_lcd)

        p_box = QVBoxLayout()
        p_box.addWidget(QLabel("Прослушиваний:"))
        self.p_lcd = QLCDNumber()
        self.p_lcd.display(self.stats["plays"])
        p_box.addWidget(self.p_lcd)

        lcd_layout.addLayout(t_box)
        lcd_layout.addLayout(p_box)
        layout.addLayout(lcd_layout)

        layout.addWidget(QLabel("Доля избранных треков:"))
        self.prog = QProgressBar()
        self.prog.setValue(calculate_percentage(self.stats["fav"], self.stats["total"]))
        layout.addWidget(self.prog)

        layout.addWidget(QLabel("Топ-5 популярных песен:"))
        self.table = QTableWidget(0, 3)
        self.table.setHorizontalHeaderLabels(["Название", "Исполнитель", "Слушали"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        for i, row in enumerate(self.stats["top"]):
            self.table.insertRow(i)
            self.table.setItem(i, 0, QTableWidgetItem(row["title"]))
            self.table.setItem(i, 1, QTableWidgetItem(row["artist"]))
            self.table.setItem(i, 2, QTableWidgetItem(str(row["play_count"])))
        layout.addWidget(self.table)

        exp_btn = QPushButton("Сохранить текстовый отчёт (.txt)")
        exp_btn.clicked.connect(self.export_txt)
        layout.addWidget(exp_btn)

    def export_txt(self):
        path, _ = QFileDialog.getSaveFileName(self, "Сохранить отчёт", "music_report.txt", TXT_FILE_FILTER)
        if not path:
            return
        lines = [
            "=== ОТЧЁТ МУЗЫКАЛЬНОГО ПЛЕЕРА ===",
            f"Дата: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            f"Всего треков: {self.stats['total']}",
            f"Избранных: {self.stats['fav']}",
            f"Прослушиваний: {self.stats['plays']}",
            "\n--- ТОП ТРЕКОВ ---"
        ]
        for t in self.stats["top"]:
            lines.append(f"• {t['artist']} — {t['title']} ({t['play_count']} раз)")
        with open(path, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))
        QMessageBox.information(self, "Успех", "Отчёт успешно сохранен!")


# =====================================================================
# ФОРМА №1: ГЛАВНОЕ ОКНО ПЛЕЕРА
# =====================================================================
class Mp3PlayerMainWindow(QMainWindow):
    """Основное окно программы: таблица треков, плеер и управление музыкой."""

    def __init__(self):
        super().__init__()
        self.db = DatabaseManager()
        self.player = QMediaPlayer(self)
        self.tracks = []
        self.curr_idx = -1

        self.timer = QTimer(self)
        self.timer.setInterval(TIMER_UPDATE_INTERVAL_MS)
        self.timer.timeout.connect(self.update_slider)

        self.setWindowTitle(APP_TITLE)
        self.setMinimumSize(WINDOW_MIN_WIDTH, WINDOW_MIN_HEIGHT)

        self.create_menu()
        self.create_layout()
        self.connect_signals()
        self.load_settings()
        self.reload_playlists()
        self.load_tracks()

    def create_menu(self):
        m = self.menuBar()
        f_menu = m.addMenu("Файл")

        add_a = QAction("Добавить MP3...", self)
        add_a.triggered.connect(self.add_files)
        f_menu.addAction(add_a)

        exp_a = QAction("Экспорт CSV...", self)
        exp_a.triggered.connect(self.export_csv)
        f_menu.addAction(exp_a)

        imp_a = QAction("Импорт CSV...", self)
        imp_a.triggered.connect(self.import_csv)
        f_menu.addAction(imp_a)

        f_menu.addSeparator()

        # Кнопка открытия окна "О программе" (автор: Хиценко Анастасия)
        about_a = QAction("О программе", self)
        about_a.triggered.connect(self.open_about_dialog)
        f_menu.addAction(about_a)

        f_menu.addSeparator()
        exit_a = QAction("Выход", self)
        exit_a.triggered.connect(self.close)
        f_menu.addAction(exit_a)

        t_menu = m.addMenu("Тема")
        for name in THEMES_DICTIONARY:
            act = QAction(f"{name}", self)
            act.triggered.connect(lambda checked, n=name: self.set_theme(n))
            t_menu.addAction(act)

        w_menu = m.addMenu("Окна")
        pl_a = QAction("Плейлисты...", self)
        pl_a.triggered.connect(self.open_playlists)
        w_menu.addAction(pl_a)
        st_a = QAction("Статистика...", self)
        st_a.triggered.connect(self.open_stats)
        w_menu.addAction(st_a)

    def open_about_dialog(self):
        """Открывает окошко с информацией об авторе."""
        dlg = AboutDialog(self)
        dlg.exec_()

    def create_layout(self):
        central = QWidget()
        self.setCentralWidget(central)
        root = QVBoxLayout(central)
        upper = QHBoxLayout()

        # Левая часть экрана (картинка-пластинка, выбор плейлиста, переходы в окна)
        left = QVBoxLayout()
        self.cover = QLabel()
        self.cover.setFixedSize(COVER_IMAGE_SIZE, COVER_IMAGE_SIZE)
        self.cover.setAlignment(Qt.AlignCenter)
        self.cover.setPixmap(generate_cover("Lyceum Beats"))
        left.addWidget(self.cover, alignment=Qt.AlignCenter)

        left.addWidget(QLabel("Плейлист:"))
        self.pl_sel = QComboBox()
        self.pl_sel.currentIndexChanged.connect(self.load_tracks)
        left.addWidget(self.pl_sel)

        pl_btn = QPushButton("Плейлисты...")
        pl_btn.clicked.connect(self.open_playlists)
        left.addWidget(pl_btn)

        st_btn = QPushButton("Статистика...")
        st_btn.clicked.connect(self.open_stats)
        left.addWidget(st_btn)
        left.addStretch()
        upper.addLayout(left, stretch=1)

        # Правая часть экрана (строка поиска, таблица треков, кнопки действий)
        right = QVBoxLayout()
        filter_bar = QHBoxLayout()
        self.search = QLineEdit()
        self.search.setPlaceholderText("Поиск трека или исполнителя...")
        self.search.textChanged.connect(self.load_tracks)
        filter_bar.addWidget(self.search, stretch=3)

        self.fav_check = QCheckBox("★ Избранное")
        self.fav_check.stateChanged.connect(self.load_tracks)
        filter_bar.addWidget(self.fav_check)

        filter_bar.addWidget(QLabel("Тема:"))
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(list(THEMES_DICTIONARY.keys()))
        self.theme_combo.currentTextChanged.connect(self.set_theme)
        filter_bar.addWidget(self.theme_combo)
        right.addLayout(filter_bar)

        self.table = QTableWidget(0, 5)
        self.table.setHorizontalHeaderLabels(["ID", "Название", "Исполнитель", "Избранное", "Слушали"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.doubleClicked.connect(lambda: self.start_track(self.table.currentRow()))
        right.addWidget(self.table)

        acts = QHBoxLayout()
        b1 = QPushButton("+ Добавить")
        b2 = QPushButton("★ Избранное")
        b3 = QPushButton("Изменить")
        b4 = QPushButton("Удалить")
        b1.clicked.connect(self.add_files)
        b2.clicked.connect(self.toggle_fav)
        b3.clicked.connect(self.edit_track)
        b4.clicked.connect(self.delete_track)
        for b in [b1, b2, b3, b4]:
            acts.addWidget(b)
        right.addLayout(acts)
        upper.addLayout(right, stretch=4)
        root.addLayout(upper)

        # Нижняя панель плеера (таймер, шкала времени, кнопки управления)
        p_box = QVBoxLayout()
        self.now_lbl = QLabel("Ничего не играет")
        self.now_lbl.setAlignment(Qt.AlignCenter)
        p_box.addWidget(self.now_lbl)

        sl_layout = QHBoxLayout()
        self.cur_time = QLabel("00:00")
        self.slider = ClickableSlider(Qt.Horizontal)
        self.slider.setRange(0, 0)
        self.slider.sliderMoved.connect(self.player.setPosition)
        self.tot_time = QLabel("00:00")
        sl_layout.addWidget(self.cur_time)
        sl_layout.addWidget(self.slider)
        sl_layout.addWidget(self.tot_time)
        p_box.addLayout(sl_layout)

        ctrls = QHBoxLayout()
        ctrls.addStretch()

        prev_b = QPushButton("⏮")
        play_b = QPushButton("❤️")
        next_b = QPushButton("⏭")

        for btn in [prev_b, play_b, next_b]:
            btn.setObjectName("RoundButton")

        prev_b.clicked.connect(self.prev_track)
        play_b.clicked.connect(self.toggle_play)
        next_b.clicked.connect(self.next_track)
        self.play_btn = play_b

        self.rep_box = QCheckBox("Повтор")

        ctrls.addWidget(prev_b)
        ctrls.addWidget(play_b)
        ctrls.addWidget(next_b)
        ctrls.addWidget(self.rep_box)
        ctrls.addStretch()

        ctrls.addWidget(QLabel("Громкость:"))
        self.vol_slider = QSlider(Qt.Horizontal)
        self.vol_slider.setRange(0, 100)
        self.vol_slider.setFixedWidth(100)
        self.vol_slider.valueChanged.connect(self.set_vol)
        self.vol_lbl = QLabel("70%")
        ctrls.addWidget(self.vol_slider)
        ctrls.addWidget(self.vol_lbl)

        p_box.addLayout(ctrls)
        root.addLayout(p_box)

        self.statusBar().showMessage("Готово к работе")

    def connect_signals(self):
        self.player.durationChanged.connect(
            lambda d: (self.slider.setRange(0, d), self.tot_time.setText(format_milliseconds(d))))
        self.player.mediaStatusChanged.connect(
            lambda s: self.next_track() if s == QMediaPlayer.EndOfMedia and not self.rep_box.isChecked() else (
                self.start_track(self.curr_idx) if s == QMediaPlayer.EndOfMedia else None))

    def reload_playlists(self):
        self.pl_sel.blockSignals(True)
        self.pl_sel.clear()
        for p in self.db.get_all_playlists():
            self.pl_sel.addItem(p["name"], p["id"])
        self.pl_sel.blockSignals(False)

    def load_tracks(self):
        self.tracks = self.db.get_filtered_tracks(self.pl_sel.currentData(), self.search.text(),
                                                  self.fav_check.isChecked())
        self.table.setRowCount(0)
        for i, t in enumerate(self.tracks):
            self.table.insertRow(i)
            self.table.setItem(i, 0, QTableWidgetItem(str(t["id"])))
            self.table.setItem(i, 1, QTableWidgetItem(t["title"]))
            self.table.setItem(i, 2, QTableWidgetItem(t["artist"]))
            self.table.setItem(i, 3, QTableWidgetItem("★ Да" if t["is_favorite"] else "Нет"))
            self.table.setItem(i, 4, QTableWidgetItem(str(t["play_count"])))

    def add_files(self):
        try:
            paths, _ = QFileDialog.getOpenFileNames(self, "Выберите MP3 файлы", "", SUPPORTED_AUDIO_FILTER)
            if not paths:
                return
            pid = self.pl_sel.currentData() or DEFAULT_PLAYLIST_ID
            cnt = 0
            for p in paths:
                norm_p = os.path.normpath(p)
                if norm_p and os.path.exists(norm_p):
                    a, t = split_filename(norm_p)
                    self.db.add_track(t, a, norm_p, pid)
                    cnt += 1
            self.load_tracks()
            self.statusBar().showMessage(f"Успешно добавлено треков: {cnt}")
        except Exception as e:
            QMessageBox.critical(self, "Ошибка добавления", f"Не удалось загрузить файл:\n{str(e)}")

    def start_track(self, idx):
        if not (0 <= idx < len(self.tracks)):
            return
        t = self.tracks[idx]
        norm_path = os.path.normpath(t["file_path"])
        if not os.path.exists(norm_path):
            QMessageBox.warning(self, "Ошибка", "Аудиофайл не найден на диске компьютера!")
            return
        self.curr_idx = idx
        self.player.setMedia(QMediaContent(QUrl.fromLocalFile(norm_path)))
        self.player.play()
        self.timer.start()
        self.play_btn.setText("💔")
        self.now_lbl.setText(f"Играет: {t['artist']} — {t['title']}")
        self.cover.setPixmap(generate_cover(t["title"]))
        self.db.inc_plays(t["id"])
        self.load_tracks()
        self.table.selectRow(idx)

    def toggle_play(self):
        st = self.player.state()
        if st == QMediaPlayer.PlayingState:
            self.player.pause()
            self.play_btn.setText("❤️")
        elif st == QMediaPlayer.PausedState:
            self.player.play()
            self.play_btn.setText("💔")
        else:
            r = self.table.currentRow()
            self.start_track(r if r >= 0 else 0)

    def prev_track(self):
        if self.tracks:
            self.start_track((self.curr_idx - 1) % len(self.tracks))

    def next_track(self):
        if self.tracks:
            self.start_track((self.curr_idx + 1) % len(self.tracks))

    def toggle_fav(self):
        r = self.table.currentRow()
        if r >= 0:
            self.db.toggle_fav(int(self.table.item(r, 0).text()))
            self.load_tracks()
            self.table.selectRow(r)

    def edit_track(self):
        r = self.table.currentRow()
        if r < 0:
            return
        if TrackEditorDialog(self.db, int(self.table.item(r, 0).text()), self).exec_() == QDialog.Accepted:
            self.load_tracks()

    def delete_track(self):
        r = self.table.currentRow()
        if r < 0:
            return
        tid = int(self.table.item(r, 0).text())
        if QMessageBox.question(self, "Подтверждение", "Удалить выбранный трек из медиатеки?",
                                QMessageBox.Yes | QMessageBox.No) == QMessageBox.Yes:
            self.db.delete_track(tid)
            self.load_tracks()

    def update_slider(self):
        if self.player.state() == QMediaPlayer.PlayingState:
            pos = self.player.position()
            self.slider.setValue(pos)
            self.cur_time.setText(format_milliseconds(pos))

    def set_vol(self, val):
        self.player.setVolume(val)
        self.vol_lbl.setText(f"{val}%")
        self.db.save_setting("volume", val)

    def set_theme(self, name):
        QApplication.instance().setStyleSheet(THEMES_DICTIONARY.get(name, DARK_THEME_QSS))
        self.db.save_setting("theme", name)
        if self.theme_combo.currentText() != name:
            self.theme_combo.setCurrentText(name)

    def load_settings(self):
        self.set_theme(self.db.get_setting("theme", "Тёмная"))
        vol = int(self.db.get_setting("volume", str(DEFAULT_VOLUME_PERCENT)))
        self.vol_slider.setValue(vol)
        self.player.setVolume(vol)

    def open_playlists(self):
        PlaylistManagerDialog(self.db, self).exec_()
        self.reload_playlists()
        self.load_tracks()

    def open_stats(self):
        StatisticsDialog(self.db, self).exec_()

    def export_csv(self):
        path, _ = QFileDialog.getSaveFileName(self, "Экспорт плейлиста", "playlist.csv", CSV_FILE_FILTER)
        if path:
            with open(path, "w", encoding="utf-8-sig", newline="") as f:
                w = csv.writer(f, delimiter=";")
                w.writerow(["Название", "Исполнитель", "Путь"])
                for t in self.tracks:
                    w.writerow([t["title"], t["artist"], t["file_path"]])
            QMessageBox.information(self, "Успех", "Плейлист успешно экспортирован в CSV!")

    def import_csv(self):
        path, _ = QFileDialog.getOpenFileName(self, "Импорт плейлиста", "", CSV_FILE_FILTER)
        if path:
            cnt = 0
            pid = self.pl_sel.currentData() or DEFAULT_PLAYLIST_ID
            with open(path, "r", encoding="utf-8-sig") as f:
                r = csv.reader(f, delimiter=";")
                next(r, None)
                for row in r:
                    if len(row) >= 3:
                        self.db.add_track(row[0], row[1], row[2], pid)
                        cnt += 1
            self.load_tracks()
            QMessageBox.information(self, "Успех", f"Успешно импортировано треков: {cnt}")

    def closeEvent(self, e):
        self.db.close()
        e.accept()


# =====================================================================
# ТОЧКА ВХОДА В ПРИЛОЖЕНИЕ
# =====================================================================
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = Mp3PlayerMainWindow()
    window.show()
    sys.exit(app.exec_())