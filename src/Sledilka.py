import os
import csv
import shutil
import datetime
from threading import Thread, Timer as ThTimer
from time import sleep
from sys import executable
from copy import deepcopy
from subprocess import Popen, PIPE

##  QT6  ##
from PyQt6.QtCore import QSize, Qt, QTimer, QTime
from PyQt6.QtGui import QPainter, QIcon, QFont, QColor, QFontDatabase, QStandardItem, QStandardItemModel, QAction
from PyQt6.QtWidgets import QApplication, QSystemTrayIcon, QWidget, QMenu, QLabel, QVBoxLayout, QSpinBox, \
    QSizePolicy, QLayout, QGroupBox, QComboBox, QHBoxLayout, QTabWidget, QPushButton, \
    QDialog, QLineEdit, QScrollArea, QStyleFactory, QListView, QStyle, QCheckBox, QColorDialog, QTimeEdit  #, QAction

from activewindow import WindowType

try:
    from base_functions import *
    from file_operations import *
    from limit_operations import *
    from paths import *
except ImportError:
    from .base_functions import *
    from .file_operations import *
    from .limit_operations import *
    from .paths import *

###########

QT_VERSION: int = 6

limited = False
limit = 0  # Возможное колличество времени за день (мин)
lim_off_type = 0  # Тип выкла (выкл, гибернация, перезагрузка, заблок экран, экран блок)
lim_activated = False
sid = 0  # Время за компом (сек)
sid_sess = 0  # Время текущей сессии (сек)
stat = {}  # Сегодняшняя статистика
full_stat = {str(datetime.date.today()): {}}  # Статистика вся, кроме сегодня
stat_sids = {str(datetime.date.today()): 0}
warn_before = 0  # Показ уведомления, когда остаётся warn_before минут до чего-либо (0 - отключено)
startup_notif_enabled = True  # Уведомление, которое появляется при автозагрузке на следующий день

pros = []  # Время по дням, сколько было просижено в каждый день
poss = []  # Сколько можно было вообще просидеть
num_days = {}  # date: №date

one_sess = 0  # Длительность сессии (до выключения, минут) (если ноль - отключено)
eye_save_type = 0  # Тип выключения компа
eye_save_time = 1  # Длительность отдыха от монитора (минут)
eye_save_time_end = datetime.datetime.now().replace(microsecond=0)  # Конец отдыха от монитора
eye_save_enabled = False
eye_save_activated = False

blocked_hours_enabled = False
blocked_hours_activated = False
blocked_hours_week_state = [True for _ in range(7)]
blocked_hours_shutdown_type = 0
blocked_hours_time_range = [datetime.time(0, 0), datetime.time(0, 0)]

lock_apps = ['LockApp.exe', 'LockScr', WindowType.LockedScreen]
is_linux_locked = False  # Был ли экран заблокирован в окружениях рабочего стола на Wayland
start = datetime.date.today()
today = datetime.date.today()
delta_t = start - today
thisapp = 'Sledilka'
saved = False
dirs = []
too_little_time = 1
phrases = {
    'translation name': 'Русский',
    'shutdown': 'Выключить компьютер',
    'restart': 'Перезагрузка',
    'hiber': 'Гибернация',
    'to lock scr': 'Заблокировать экран',
    'lock scr': 'Экран блокировки',
    'block title': 'Следилка - Блокировщик ТЕБЯ',
    'add time': 'Добавить',
    'minutes': 'мин.',
    'needs rest from the monitor': 'Требуется отдых от монитора',
    'need rest from the monitor for': 'Требовать отдыха от монитора на',
    'rest from the monitor': 'Отдых от монитора',
    'limit': 'Лимит времени',
    'blocked hours': 'Заблокированные часы',
    'your time is over': 'Ваше время истекло',
    'limit will be over soon': 'Лимит скоро будет исчерпан',
    'session will be over soon': 'Сессия скоро закончится',
    'duration of session': 'Длительность сеанса',
    'by the end of the session:': 'При окончании сеанса:',
    'session is running for:': '\nСеанс уже длится:',
    'time for today': 'Сегодняшнее время:',
    'time adder title': 'Добавить время',
    'suspiciously little time': 'В прошлый раз вы подозрительно мало сидели за компьютером',
    'previous time:': 'Время проведённое за компьютером в прошлый раз:',
    'application': 'Приложение',
    'preliminary notifications': 'Предварительные оповещения',
    'behaviour': 'Поведение',
    'show notifications before': 'Показывать уведомления за',
    'info': 'Информация',
    'translations': 'Переводы',
    'translation': 'Перевод',
    'copy': 'Копировать',
    'statistic': 'Статистика',
    'settings': 'Настройки',
    'advanced settings': 'Расширенные настройки',
    'show': 'Показать',
    'hide': 'Скрыть',
    'ok': 'OK',
    'cancel': 'Отмена',
    'apply': 'Применить',
    'done': 'Готово',
    'total:': 'Всего:',
    'after': 'по прошествии',
    'which date add to?': 'На какую дату добавить?',
    'today': 'Сегодня',
    'app name': 'Следилка',
    'theme': 'Тема оформления',
    'timer theme': 'Тема таймера',
    'text color': 'Цвет текста',
    'background color': 'Цвет фона',
    'interface appearance': 'Оформление интерфейса',
    'dark': 'Тёмная',
    'light': 'Светлая',
    'custom theme': 'Настраиваемая',
    'corner smoothing': 'Сглаживание углов:',
    'startup window title': 'Начальная настройка',
    'hide on startup': 'Скрывать таймер при запуске',
    'show startup notification': 'Показывать уведомление при запуске',
    'mon': 'пн',
    'tue': 'вт',
    'wed': 'ср',
    'thu': 'чт',
    'fri': 'пн',
    'sat': 'сб',
    'sun': 'вс',
    'if the day is': 'если',
    'every day': 'каждый день',
    '[time] from': 'от',
    '[time] to': 'до',
    'blocked hours are coming': 'Заблокированные часы приближаются'
}
trans = ['Русский']
tran_name = 'Русский'
theme = 'Light'
prev_theme = theme
default_timer_theme = {
    'xRadius': 25,
    'yRadius': 25,
    'base_color': '#ffffff',
    'text_color': '#000000'
}
timer_theme = deepcopy(default_timer_theme)
prev_timer_theme = {}

need_to_show_startup = False
hidden_startup = False
font = QFont()  # Changed in notifications()

default_sett = {'one_sess': 0,
                'eye_save_type': 0,
                'eye_save_time': 1,
                'eye_save_time_end': str(datetime.datetime.now().replace(microsecond=0)),
                'eye_save_enabled': False,
                'limited': False,
                'limit': 0,
                'lim_off_type': 0,
                'blocked_hours_enabled': False,
                'blocked_hours_week_state': [True for _ in range(7)],
                'blocked_hours_shutdown_type': 0,
                'blocked_hours_time_range': [str(datetime.time(0, 0)), str(datetime.time(0, 0))],
                'theme': 'Light',
                'warn_before': 0,
                'tran_name': 'Русский',
                'hidden_startup': False,
                'timer_theme': deepcopy(default_timer_theme),
                'startup_notif_enabled': True}
sett = deepcopy(default_sett)  # Словарь сохраняемых параметров. Используется только для работы с файлами

desktop_file = f"""[Desktop Entry]
Type=Application
Exec=bash -c "sleep 5 && cd '{base_path}' && '{executable}' '{argv[0]}'"
Path={base_path}
Icon={base_path}/icon.ico
StartupNotify=true
Terminal=false
TerminalOptions=
X-DBUS-ServiceName=Sledilka
X-DBUS-StartupType=Unique
X-GNOME-Autostart-enabled=true
X-KDE-SubstituteUID=false
X-KDE-Username=
Hidden=false
NoDisplay=false
Name[en_IN]=Sledilka
Name[ru_RU]=Следилка
Name={phrases["app name"]}
Comment[en_IN]=
Comment=
"""  # .desktop file for linux


class Timer(QWidget):

    def __init__(self):
        log('Timer __init__')
        super().__init__()
        self.setFixedSize(QSize(145, 110))
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint)
        self.setWindowTitle(phrases['app name'])
        self.setWindowIcon(app_icon)

        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.oldPos = None  # Перемещение окна
        self.in_tray = False
        self.installEventFilter(self)
        self.time_show = QLabel(str(datetime.timedelta(seconds=sid)))
        self.time_show.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.sett_w = Settings()
        self.stat = Statistic()
        self.blk = Block()
        self.startup_window = Startup()

        self._actions()

        self._tray()

        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.addWidget(self.time_show)

        self.context = QMenu(self)
        self.context.addAction(self.copy)
        # self.copy_act.setShortcut(QKeySequence.StandardKey.Copy)
        self.context.addSeparator()
        self.context.addAction(self.a_stat)
        self.context.addAction(self.a_sett)
        self.context.addSeparator()
        self.context.addAction(self.a_hide)

        # threading.Timer(10, self.runtimesec).start()

        self.timer = QTimer()
        self.timer.timeout.connect(self.runtimesec)  # noqa
        self.timer.setInterval(1000)
        self.checker_timer = QTimer()
        self.checker_timer.timeout.connect(self.checker)  # noqa
        self.checker_timer.setInterval(1000)

        if not lim_activated and not eye_save_activated and not hidden_startup and not blocked_hours_activated:
            debug('shown:', hidden_startup)
            self.show()
        else:
            self.hide()
            self.in_tray = True
            debug('hidden', hidden_startup, self.in_tray)
        self.it = 0  # Итерации сохранения
        self.runtime()

    def _actions(self):
        self.copy = QAction(phrases['copy'], self)
        self.copy.triggered.connect(self.sid_add)  # noqa

        self.a_stat = QAction(phrases['statistic'], self)
        self.a_stat.triggered.connect(self.stat.show)  # noqa

        self.a_sett = QAction(phrases['settings'], self)
        self.a_sett.triggered.connect(self.sett_w.show)  # noqa

        self.a_show = QAction(phrases['show'], self)
        self.a_show.triggered.connect(self.show)  # noqa

        self.a_hide = QAction(phrases['hide'], self)
        self.a_hide.triggered.connect(self.hide)  # noqa

    def _tray(self):
        self.tray_icon = QSystemTrayIcon(self)
        self.tray_icon.setIcon(app_icon)
        self.tray_icon.activated.connect(self.restore_window)  # noqa

        self.tray_menu = QMenu()
        self.tray_menu.addAction(self.a_sett)
        self.tray_menu.addAction(self.a_stat)
        self.tray_menu.addSeparator()
        self.tray_menu.addAction(self.a_show)
        self.tray_menu.addAction(self.a_hide)

        self.tray_icon.setContextMenu(self.tray_menu)
        self.tray_icon.show()

    @staticmethod
    def sid_add():
        add_clip()

    def showEvent(self, event):
        self.in_tray = False

    def hideEvent(self, event):
        debug('hide_event', self.in_tray)
        self.in_tray = True
        debug('hide_event_end', self.in_tray)

    def closeEvent(self, event):  # Запрет закрытия окна
        event.ignore()
        self.hide()

    def paintEvent(self, ev):  # Создание окна
        # print('paintEvent')
        if sid > 36000:
            self.setFixedSize(165, 120)
        painter = QPainter(self)
        if QT_VERSION == 6:  # Сглаживание краёв
            ##  QT6  ##
            # painter.setRenderHint(QPainter.renderHints(painter).Antialiasing)
            ...
            ###########
        elif QT_VERSION == 5:
            ##  QT5  ##
            painter.setRenderHint(QPainter.Antialiasing)  # noqa
            ###########
        if theme == 'Light':
            painter.setBrush(Qt.GlobalColor.white)
            self.time_show.setStyleSheet("QLabel { color : black; }")
        elif theme == 'Dark':
            painter.setBrush(QColor(43, 43, 43))
            self.time_show.setStyleSheet("QLabel { color : white; }")
        else:
            painter.setBrush(QColor(timer_theme['base_color']))
            self.time_show.setStyleSheet("QLabel { color : "
                                         f"{timer_theme['text_color']}"
                                         "; }")
        painter.drawRoundedRect(self.rect(), timer_theme['xRadius'], timer_theme['yRadius'])  # Закругление краёв

    def mousePressEvent(self, event):  # Перетаскивание окна PySide6
        if event.button() == Qt.MouseButton.LeftButton:
            if QT_VERSION == 5:
                self.oldPos = event.globalPos()
            else:
                self.oldPos = event.globalPosition().toPoint()

    def mouseMoveEvent(self, event):
        if self.oldPos is not None:
            if QT_VERSION == 6:
                ##  QT6  ##
                delta = event.globalPosition().toPoint() - self.oldPos
                self.move(self.pos() + delta)
                self.oldPos = event.globalPosition().toPoint()  # .globalPos()
                ###########
            elif QT_VERSION == 5:
                ##  QT5  ##
                delta = event.globalPos() - self.oldPos
                self.move(self.pos() + delta)
                self.oldPos = event.globalPos()
                ###########

    def mouseReleaseEvent(self, event):
        self.oldPos = None

    def contextMenuEvent(self, e):  # Контекстное меню
        if QT_VERSION == 6:
            ##  QT6  ##
            self.context.exec(self.mapToGlobal(e.pos()))
            ###########
        elif QT_VERSION == 5:
            ##  QT5  ##
            self.context.exec_(self.mapToGlobal(e.pos()))  # noqa
            ###########

    def restore_window(self, reason):  # Возвращение окна из трея
        if reason != QSystemTrayIcon.ActivationReason.Context:
            if self.isHidden():
                self.show()
            else:
                self.hide()

    def runtime(self):
        log('runtime')
        global sid
        self.time_show.setFont(font)
        self.time_show.setFont(QFont('Segoe UI', 30))
        self.time_show.setAlignment(Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignVCenter)
        # self.time_show.setAlignment(Qt.AlignHCenter | Qt.AlignVCenter)

        self.stat.updater.start()
        self.timer.start()
        self.checker_timer.start()

    def checker(self):
        global sid, sid_sess, eye_save_time_end, start, saved, stat, thisapp, today
        # try:
        s = datetime.datetime.now()  # noqa
        if today != datetime.date.today():
            today = datetime.date.today()
        if thisapp not in lock_apps and not is_blocked():
            if self.isHidden() and not self.in_tray:
                debug('restored from tray: checker', hidden_startup)
                self.show()
            # ???
            Thread(target=add_to_stat).start()
            # ???
            if self.it == 60:
                debug('datasavee')
                Thread(target=datasave).start()  # Сейвы каждую минуту
                self.it = 0
            if sid_sess >= one_sess * 60 and eye_save_enabled:  # Если время сессии подошло к концу, то:
                log('end of sess')
                debug('eeeeeeeeeeeeeeeeeeeendofsess')
                sid_sess = 0
                eye_save_time_end = datetime.datetime.strptime(
                    datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'), '%Y-%m-%d %H:%M:%S') + \
                    datetime.timedelta(minutes=eye_save_time)
                debug('datasavee')
                Thread(target=datasave).start()
                eye_save()
            # elif sid_sess > one_sess * 60:
            #     log('sideeed')
            #     sid_sess = 0
            try:
                # debug(f'{json.dumps(poss, indent=4)}\n{pformat(num_days, indent=4)}\n{datetime.date.today() = }')
                if limit_should_be_activated():
                    #                                       ~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^~~~~~~
                    debug(f'{limited = }\n',
                          f'{sid >= limit * 60 = }\n',
                          f'{sid >= poss[num_days[datetime.date.today()]] * 60 = }\n',
                          f'\n{enumerate(poss) = }',
                          f'\n{num_days = }', f'\n{datetime.date.today()}')
                    log('liiiiiimit')
                    limit_out()
            except KeyError:
                set_all_sids()
            except IndexError:  # Лимит не был включён с начала Следилки, затем был включён
                skok_poss()
        if now_in_blocked_hours_range() and blocked_hours_enabled:
            activate_blocked_hours()
        elif is_blocked():
            if not self.in_tray:
                self.hide()
                self.in_tray = True
        elif not saved and thisapp not in lock_apps:
            debug('datasavee')
            Thread(target=datasave).start()
            saved = True
        if datetime.date.today() != start:
            sid = 0
            full_stat[str(start)] = stat
            start = datetime.date.today()
            stat = {'Sledilka': 0}
            if limited:
                set_all_sids()
        if warn_before != 0 and eye_save_enabled and sid_sess + warn_before * 60 == one_sess * 60:
            # сек + мин * 60 == мин * 60
            notif(phrases['rest from the monitor'], phrases['session will be over soon'])
            debug('NOOOOOOOOOOOOOOTIFED1', sid_sess, warn_before, one_sess)
        elif warn_before != 0 and limited and limit * 60 == sid + warn_before * 60:  # мин * 60 == сек + мин * 60
            notif(phrases['limit'], phrases['limit will be over soon'])
            debug('NOOOOOOOOOOOOOOTIFED2')
        elif warn_before != 0 and blocked_hours_enabled and \
                now_in_blocked_hours_range(datetime.datetime.now() + datetime.timedelta(minutes=warn_before)):
            notif(phrases['blocked hours'], phrases['blocked hours are coming'])
            debug('NOOOOOOOOOOOOOOTIFED3')
        # print((datetime.datetime.now() - s).total_seconds(), 'cекунд итерация checker')
        # except Exception as exc:
        #     print('error in checker:', exc)

    def runtimesec(self):
        global sid, sid_sess
        # debug(f'runtimesec: {thisapp = }')
        self.sett_w.advanced.globals.setText(pformat(clean_globals()))
        if thisapp not in lock_apps and not is_blocked():
            self.time_show.setText(str(datetime.timedelta(seconds=sid)))
            # debug('updated')
            self.tray_icon.setToolTip(f"{phrases['time for today']} {datetime.timedelta(seconds=sid)}"
                                      f"{phrases['session is running for:']} {datetime.timedelta(seconds=sid_sess)}")
            sid += 1
            sid_sess += 1
            self.it += 1

    def show_block(self):
        log('show_block')
        if (eye_save_activated and sid_sess >= one_sess * 60 and eye_save_enabled) or \
                (lim_activated and limited and sid >= limit * 60) or \
                (blocked_hours_activated and blocked_hours_enabled and now_in_blocked_hours_range()):
            self.blk.set_texts()
            if not self.blk.isActiveWindow():
                self.blk.up()


class Settings(QWidget):
    def __init__(self):
        super().__init__()
        self.s_eye_rest_label = QLabel(phrases['need rest from the monitor for'])
        log('Settings __init__')
        self.setWindowTitle(phrases['settings'])
        self.setWindowIcon(app_icon)
        self.setWindowFlags(Qt.WindowType.CustomizeWindowHint | Qt.WindowType.WindowCloseButtonHint)

        self.translator = Translator()
        self.advanced = AdvancedSettings()

        self.layout = QVBoxLayout()
        self.layout.setSizeConstraint(QLayout.SizeConstraint.SetDefaultConstraint)
        self.mainlay = QVBoxLayout()

        self._set_eye_save()
        self._set_limits()
        self._set_blocked_hours()
        self._set_notifications()
        self._set_behaviour()
        self._set_color()
        self._set_buttons()

        self._set_scroll()
        self.update_interface()
        self._set_main_buttons()
        self.setLayout(self.mainlay)
        self.setMaximumSize(self.mainlay.maximumSize())

    def _set_eye_save(self):
        self.s_one_sess_gr = QGroupBox()  # Отдых от монитора:
        self.s_one_sess_gr.setTitle(phrases['rest from the monitor'])
        self.s_one_sess_gr.setCheckable(True)

        self.s_eye_sess = QLabel()
        self.s_eye_sess.setText(phrases['duration of session'])
        self.s_eye = QSpinBox()
        self.s_eye.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        self.s_eye.setRange(1, 1440)
        self.s_eye.setSuffix(f" {phrases['minutes']}")

        self.s_eye_lay = QHBoxLayout()
        self.s_eye_lay.setAlignment(Qt.AlignmentFlag.AlignLeft)
        self.s_eye_lay.addWidget(self.s_eye_sess)
        self.s_eye_lay.addWidget(self.s_eye)
        # self.s_eye_lay.setSizeConstraint(QLayout.SizeConstraint.SetFixedSize)

        self.s_eye_sess_end_label = QLabel(phrases['by the end of the session:'])

        self.s_eye_sess_end_list = QShutdownBox()

        self.s_eye_sess_end_lay = QHBoxLayout()
        self.s_eye_sess_end_lay.addWidget(self.s_eye_sess_end_label)
        self.s_eye_sess_end_lay.addWidget(self.s_eye_sess_end_list)

        self.s_eye_rest_spin = QSpinBox()
        self.s_eye_rest_spin.setRange(1, 1440)
        self.s_eye_rest_spin.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        self.s_eye_rest_spin.setSuffix(f" {phrases['minutes']}")

        self.s_eye_rest_lay = QHBoxLayout()
        self.s_eye_rest_lay.setAlignment(Qt.AlignmentFlag.AlignLeft)
        self.s_eye_rest_lay.addWidget(self.s_eye_rest_label)
        self.s_eye_rest_lay.addWidget(self.s_eye_rest_spin)

        self.s_one_sess_gr_lay = QVBoxLayout(self.s_one_sess_gr)
        self.s_one_sess_gr_lay.addLayout(self.s_eye_lay)
        self.s_one_sess_gr_lay.addLayout(self.s_eye_sess_end_lay)
        self.s_one_sess_gr_lay.addLayout(self.s_eye_rest_lay)

        self.layout.addWidget(self.s_one_sess_gr)

    def _set_limits(self):  # Настройка дневных лимитов
        self.s_lim_gr = QGroupBox(phrases['limit'])
        self.s_lim_gr.setCheckable(True)

        self.s_lim_end_list = QShutdownBox()

        self.s_lim_lab = QLabel(phrases['after'])

        self.s_limit = QSpinBox()
        self.s_limit.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        self.s_limit.setRange(1, 1440)
        self.s_limit.setSuffix(f" {phrases['minutes']}")

        self.s_lim_lay = QHBoxLayout(self.s_lim_gr)
        self.s_lim_lay.setAlignment(Qt.AlignmentFlag.AlignLeft)
        self.s_lim_lay.addWidget(self.s_lim_end_list)
        self.s_lim_lay.addWidget(self.s_lim_lab)
        self.s_lim_lay.addWidget(self.s_limit)
        # self.s_lim_lay.setSizeConstraint(QLayout.SizeConstraint.SetFixedSize)

        self.layout.addWidget(self.s_lim_gr)

    def _set_blocked_hours(self):
        self.s_blk_hrs_gr = QGroupBox(phrases['blocked hours'])
        self.s_blk_hrs_gr.setCheckable(True)

        self.s_blk_hrs_setts = BlockedHoursSetting(week_state=blocked_hours_week_state)

        self.s_blk_hrs_gr_lay = QVBoxLayout()
        self.s_blk_hrs_gr.setLayout(self.s_blk_hrs_gr_lay)
        self.s_blk_hrs_gr_lay.addWidget(self.s_blk_hrs_setts)

        self.layout.addWidget(self.s_blk_hrs_gr)

    def _set_notifications(self):  # Предварительные оповещения и т. д.
        self.s_warn_gr = QGroupBox(phrases['preliminary notifications'])
        self.s_warn_gr.setCheckable(True)

        self.s_warn = QSpinBox()
        self.s_warn.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        self.s_warn.setRange(1, 1440)
        self.s_warn.setPrefix(f"{phrases['show notifications before']} ")
        self.s_warn.setSuffix(f" {phrases['minutes']}")

        self.s_warn_gr_lay = QVBoxLayout(self.s_warn_gr)
        self.s_warn_gr_lay.addWidget(self.s_warn)

        self.layout.addWidget(self.s_warn_gr)

    def _set_behaviour(self):
        self.s_behav_gr = QGroupBox(phrases['behaviour'])

        self.s_behav_hide_timer = QCheckBox()
        self.s_behav_hide_timer.setText(phrases['hide on startup'])

        self.s_behav_show_startup_notif = QCheckBox()
        self.s_behav_show_startup_notif.setText(phrases['show startup notification'])

        self.s_behav_gr_lay = QVBoxLayout(self.s_behav_gr)
        self.s_behav_gr_lay.addWidget(self.s_behav_hide_timer)
        self.s_behav_gr_lay.addWidget(self.s_behav_show_startup_notif)

        self.layout.addWidget(self.s_behav_gr)

    def _set_color(self):
        self.s_theme_gr = QGroupBox(phrases['theme'])

        self.s_theme_lay = QHBoxLayout()
        self.s_theme_text = QLabel(phrases['timer theme'])
        self.s_theme_list = QComboBox()
        self.s_theme_list.addItem(phrases['dark'])
        self.s_theme_list.addItem(phrases['light'])
        self.s_theme_list.addItem(phrases['custom theme'])
        self.s_theme_list.currentIndexChanged.connect(self.color_changes)  # noqa

        self.s_custom_theme_lay = QHBoxLayout()

        self.s_custom_theme_text_color = QPushButton(phrases['text color'])
        self.s_custom_theme_text_color.clicked.connect(set_text_color)  # noqa
        self.s_custom_theme_lay.addWidget(self.s_custom_theme_text_color)
        self.s_custom_theme_background_color = QPushButton(phrases['background color'])
        self.s_custom_theme_background_color.clicked.connect(set_background_color)  # noqa
        self.s_custom_theme_lay.addWidget(self.s_custom_theme_background_color)

        self.s_theme_lay.addWidget(self.s_theme_text)
        self.s_theme_lay.addWidget(self.s_theme_list)

        self.s_style_lay = QHBoxLayout()
        self.s_style_text = QLabel(phrases['interface appearance'])
        self.s_style_list = QComboBox()
        for i in QStyleFactory.keys():
            self.s_style_list.addItem(i)
        self.s_style_lay.addWidget(self.s_style_text)
        self.s_style_lay.addWidget(self.s_style_list)

        self.s_tran_label = QLabel(phrases['translation'])
        self.s_tran_list = QComboBox()

        self.s_tran_lay = QHBoxLayout()
        self.s_tran_lay.addWidget(self.s_tran_label)
        self.s_tran_lay.addWidget(self.s_tran_list)

        self.s_theme_gr_lay = QVBoxLayout(self.s_theme_gr)
        self.s_theme_gr_lay.addLayout(self.s_theme_lay)
        self.s_theme_gr_lay.addLayout(self.s_custom_theme_lay)
        self.s_theme_gr_lay.addLayout(self.s_style_lay)
        self.s_theme_gr_lay.addLayout(self.s_tran_lay)

        self.layout.addWidget(self.s_theme_gr)

    def _set_scroll(self):
        self.area = QScrollArea()
        self.area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        widget = QWidget()
        widget.setLayout(self.layout)
        # widget.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        self.area.setWidget(widget)
        self.area.setWidgetResizable(True)

        self.mainlay.addWidget(self.area)
        self.area.setMaximumSize(widget.width() + 20, widget.height() + 5)
        # self.area.resize(self.area.maximumWidth(), self.area.maximumHeight())
        # self.resize(self.maximumWidth(), self.height())

    def _set_buttons(self):
        self.btnlay = QHBoxLayout()  # Перевод

        self.s_tran_bt = QPushButton(phrases['translations'])
        self.s_tran_bt.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        self.s_tran_bt.clicked.connect(self.translator.show)  # noqa
        self.btnlay.addWidget(self.s_tran_bt)

        self.adv_butt = QPushButton(phrases['advanced settings'])
        self.adv_butt.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        self.adv_butt.clicked.connect(self.advanced.show)  # noqa
        self.btnlay.addWidget(self.adv_butt)

        self.about = QPushButton('About Qt')
        self.about.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        self.about.clicked.connect(app.aboutQt)  # noqa
        self.btnlay.addWidget(self.about)

        self.layout.addLayout(self.btnlay)

    def _set_main_buttons(self):
        self.main_btn_lay = QHBoxLayout()
        self.main_btn_lay.setAlignment(Qt.AlignmentFlag.AlignRight)

        self.butt_ok = QPushButton()
        self.butt_ok.setText(phrases['ok'])
        self.butt_ok.clicked.connect(self.sett_save)  # noqa
        self.butt_ok.clicked.connect(self.close)  # noqa
        self.butt_ok.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        self.butt_ok.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_DialogOkButton))
        self.main_btn_lay.addWidget(self.butt_ok)

        self.butt_cancel = QPushButton()
        self.butt_cancel.setText(phrases['cancel'])
        self.butt_cancel.clicked.connect(self.close)  # noqa
        self.butt_cancel.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        self.butt_cancel.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_DialogCancelButton))
        self.main_btn_lay.addWidget(self.butt_cancel)

        self.butt_apply = QPushButton()
        self.butt_apply.setText(phrases['apply'])
        self.butt_apply.clicked.connect(self.sett_save)  # noqa
        self.butt_apply.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        self.butt_apply.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_DialogApplyButton))
        self.main_btn_lay.addWidget(self.butt_apply)

        self.mainlay.addLayout(self.main_btn_lay)

    def sett_save(self):
        global one_sess, eye_save_type, eye_save_time, eye_save_time_end, eye_save_enabled, limited, lim_off_type, \
            limit, theme, warn_before, tran_name, window, sid, phrases, hidden_startup, prev_timer_theme, prev_theme, \
            startup_notif_enabled, blocked_hours_enabled, blocked_hours_week_state, blocked_hours_shutdown_type, \
            blocked_hours_time_range
        # Отдых от монитора
        one_sess = self.s_eye.value()
        eye_save_enabled = self.s_one_sess_gr.isChecked()  # Длительность сеанса
        # eye_save_time_end = datetime.datetime.now().replace(microsecond=0) + \
        #     datetime.timedelta(minutes=eye_save_time)
        eye_save_type = self.s_eye_sess_end_list.currentIndex()  # Определение типа выкла
        eye_save_time = self.s_eye_rest_spin.value()

        # Лимит
        limited = self.s_lim_gr.isChecked()
        lim_off_type = self.s_lim_end_list.currentIndex()  # Определение типа выкла
        limit = self.s_limit.value()
        log(f'{sett["limited"] = }, {self.s_lim_end_list.currentText() = } - {sett["lim_off_type"] = }, '
            f'{sett["limit"] = }')
        log(f'{sett["eye_save_enabled"] = }')

        # Заблокированные часы
        blocked_hours_enabled = self.s_blk_hrs_gr.isChecked()
        blocked_hours_week_state = self.s_blk_hrs_setts.getState()
        blocked_hours_shutdown_type = self.s_blk_hrs_setts.getShutdownType()
        blocked_hours_time_range = self.s_blk_hrs_setts.getTimeRange()

        hidden_startup = self.s_behav_hide_timer.isChecked()
        startup_notif_enabled = self.s_behav_show_startup_notif.isChecked()

        if self.s_theme_list.currentIndex() == 0:  # Dark theme
            theme = 'Dark'
            # window.time_show.setStyleSheet("QLabel { color : white; }")
        elif self.s_theme_list.currentIndex() == 1:  # Light theme
            theme = 'Light'
            # window.time_show.setStyleSheet("QLabel { color : black; }")
        else:
            theme = 'Custom'
            debug(f'{prev_timer_theme = }')
            prev_timer_theme = deepcopy(timer_theme)
        prev_theme = theme
        if self.s_warn_gr.isChecked():
            warn_before = self.s_warn.value()
        else:
            warn_before = 0
        app.setStyle(self.s_style_list.currentText())
        changed = False  # Был ли текущий перевод изменён
        if tran_name != self.s_tran_list.currentText():
            tran_name = self.s_tran_list.currentText()
            gettran(tran_name)
            changed = True
        debug('datasavee')
        datasave()

        if changed:
            sid += 2
            restart(sid_sess)

    def update_interface(self):
        global tran_name
        # Отдых от монитора
        self.s_one_sess_gr.setChecked(eye_save_enabled)
        self.s_eye.setValue(one_sess)
        self.s_eye_sess_end_list.setCurrentIndex(eye_save_type)
        self.s_eye_rest_spin.setValue(eye_save_time)

        # Лимиты
        self.s_lim_gr.setChecked(limited)
        self.s_lim_end_list.setCurrentIndex(lim_off_type)
        self.s_limit.setValue(limit)

        # Заблокированные часы
        self.s_blk_hrs_gr.setChecked(blocked_hours_enabled)
        self.s_blk_hrs_setts.setState(blocked_hours_week_state)
        self.s_blk_hrs_setts.setShutdownType(blocked_hours_shutdown_type)
        self.s_blk_hrs_setts.setTimeRange(blocked_hours_time_range)

        # Поведение
        self.s_behav_hide_timer.setChecked(hidden_startup)
        self.s_behav_show_startup_notif.setChecked(startup_notif_enabled)

        # Тема таймера
        if theme == 'Dark':
            self.s_theme_list.setCurrentText(phrases['dark'])
            self.s_custom_theme_text_color.setVisible(False)
            self.s_custom_theme_background_color.setVisible(False)
        elif theme == 'Light':
            self.s_theme_list.setCurrentText(phrases['light'])
            self.s_custom_theme_text_color.setVisible(False)
            self.s_custom_theme_background_color.setVisible(False)
        else:
            self.s_theme_list.setCurrentText(phrases['custom theme'])
            self.s_custom_theme_text_color.setVisible(True)
            self.s_custom_theme_background_color.setVisible(True)

        self.s_tran_list.clear()
        # if phrases['translation name'] != tran_name:
        #     tran_name = phrases['translation name']
        if tran_name not in trans:
            trans.append(tran_name)
        for t in trans:
            self.s_tran_list.addItem(t)
        self.s_tran_list.setCurrentText(tran_name)
        debug(f'update_interface: {tran_name = },', phrases['translation name'])

        if warn_before > 0:
            self.s_warn_gr.setChecked(True)
            self.s_warn.setValue(warn_before)
        else:
            self.s_warn_gr.setChecked(False)
            self.s_warn.setValue(1)

        # self.setMaximumSize(self.mainlay.maximumSize())

    def color_changes(self):
        debug(timer_theme)
        debug(self.s_theme_list.currentIndex())
        if self.s_theme_list.currentIndex() == 2:
            self.s_custom_theme_text_color.setVisible(True)
            self.s_custom_theme_background_color.setVisible(True)
        else:
            self.s_custom_theme_text_color.setVisible(False)
            self.s_custom_theme_background_color.setVisible(False)

    def showEvent(self, event):
        self.update_interface()

    def closeEvent(self, event):  # Если удалить - при закрытии будет завершаться приложение
        event.ignore()
        self.hide()

    def hideEvent(self, event):
        debug('sett hide event')
        global timer_theme, theme
        debug(f'{theme} - {prev_theme}, {timer_theme}-{prev_timer_theme}')
        if timer_theme != prev_timer_theme or theme != prev_theme:
            timer_theme = deepcopy(prev_timer_theme)
            theme = prev_theme
            log('timer_theme changed')

    # def resizeEvent(self, event):
    #     debug(self.size())


class Block(QWidget):
    def __init__(self):
        super().__init__()
        log('Block __init__')
        self.setWindowFlags(Qt.WindowType.WindowStaysOnTopHint)
        self.setStyleSheet("background: black;")
        # self.setStyleSheet("background-color: rgba(0, 0, 0, 200);")
        self.setWindowTitle(phrases['block title'])
        self.setWindowIcon(app_icon)
        self.setWindowOpacity(0.8)  # TODO: make this work on Wayland
        self.setAttribute(Qt.WidgetAttribute.WA_DontCreateNativeAncestors, True)
        if is_blocked() and 3 in [eye_save_type, lim_off_type, blocked_hours_shutdown_type]:
            self.showFullScreen()
            self.activateWindow()
        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignCenter)
        self.setLayout(layout)
        self.label = QLabel()
        self.label.setStyleSheet("color: red;")

        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.label.setFont(QFont("Arial", 40))
        layout.addWidget(self.label)
        self.b_timer = QLabel()
        self.b_timer.setStyleSheet("color: blue;")

        self.set_texts()

        self.b_timer.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.b_timer.setFont(QFont("Arial", 40))
        layout.addWidget(self.b_timer)
        self.noclo()

        self.blocksec_timer = QTimer()
        self.blocksec_timer.timeout.connect(self.blocksec)  # noqa
        self.blocksec_timer.start(1000)

    def noclo(self):
        global eye_save_activated, lim_activated, blocked_hours_activated
        if (not self.isActiveWindow()) and \
                ((eye_save_activated and eye_save_type == 3) or
                 (lim_activated and lim_off_type == 3) or
                 (blocked_hours_activated and blocked_hours_shutdown_type == 3)):
            self.up()
        if (eye_save_activated and eye_save_type == 3) or \
                (lim_activated and lim_off_type == 3) or \
                (blocked_hours_activated and blocked_hours_shutdown_type == 3):
            if (eye_save_time_end - datetime.datetime.now()).total_seconds() < 1:
                eye_save_activated = False
            if sid < limit * 60:
                lim_activated = False
            if not now_in_blocked_hours_range():
                blocked_hours_activated = False
            QTimer.singleShot(100, self.noclo)
        elif not eye_save_activated and not lim_activated and not blocked_hours_activated:
            QTimer.singleShot(1000, self.noclo)

    def up(self):
        debug('up')
        debug(f'1 {self.isHidden() = }, {self.isActiveWindow() = }')
        # if not self.isActiveWindow() and wintitle != phrases['block title']:
        self.hide()
        self.showNormal()
        self.showFullScreen()
        debug(f'2 {self.isHidden() = }, {self.isActiveWindow() = }')

    def closeEvent(self, event):
        if is_blocked():
            event.ignore()
        else:
            self.hide()

    def blocksec(self):
        global eye_save_activated, lim_activated, blocked_hours_activated
        if (eye_save_activated and eye_save_type == 3) \
                or (lim_activated and lim_off_type == 3) \
                or (blocked_hours_activated and blocked_hours_shutdown_type == 3):
            self.show()
        self.set_texts()
        if (eye_save_time_end - datetime.datetime.now()).total_seconds() < 1 or \
                not eye_save_enabled:  # Если время отдыха закончилось,
            eye_save_activated = False  # то закрывать
        if limited and sid < limit * 60 or not limited:
            lim_activated = False
        if blocked_hours_enabled and not now_in_blocked_hours_range() or not blocked_hours_enabled:
            blocked_hours_activated = False
        if not eye_save_activated and not lim_activated and not blocked_hours_activated:
            self.hide()

    def set_texts(self):
        if lim_activated:
            self.label.setText(phrases['your time is over'])
            self.b_timer.setText('')
        elif eye_save_activated:
            self.label.setText(phrases['rest from the monitor'])
            self.b_timer.setText(str(
                datetime.timedelta(seconds=int((eye_save_time_end - datetime.datetime.now()).total_seconds()))))
        elif blocked_hours_activated:
            self.label.setText(phrases['blocked hours'])
            self.b_timer.setText('')


class Statistic(QWidget):
    def __init__(self):
        super().__init__()
        log('Statistic __init__')
        self.setWindowTitle(phrases['statistic'])
        self.setWindowIcon(app_icon)
        self.setWindowFlags(Qt.WindowType.CustomizeWindowHint | Qt.WindowType.WindowCloseButtonHint)

        self.adder = TimeAdder()

        self.mainlay = QHBoxLayout()
        self.layout = QVBoxLayout()
        self.layout.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)

        self.tabs = QTabWidget()
        self.tabs.setDocumentMode(True)
        self.tabs.setMovable(True)

        self.stat_l = QLabel()
        self.stat_l.setAlignment(Qt.AlignmentFlag.AlignLeft)

        self.add_time = QPushButton()
        self.add_time.setText(phrases['add time'])
        self.add_time.clicked.connect(self.adder.show)  # noqa
        self.layout.addWidget(self.stat_l)
        self.layout.addWidget(self.add_time)
        self.mainlay.addLayout(self.layout)
        self.setLayout(self.mainlay)
        self.stat_make()
        self.updater = QTimer()
        self.updater.timeout.connect(self.stat_upd)  # noqa
        self.updater.setInterval(1000)

    def stat_make(self):
        debug(f'{self.tabs.count() = }')
        while self.tabs.count() > 0:
            self.tabs.removeTab(0)
        # for tab in range(self.tabs.count()):
        #     self.tabs.removeTab(tab)
        for i in reversed(full_stat):
            # for key in full_stat[i]:
            #     text = QLabel()
            #     # print('eeeeeeee',key, full_stat[i][key])
            #     if full_stat[i][key] != 0 and key not in lock_apps:
            #         text.setText(self.stat_l.text() +
            #                         f'{key.replace(".exe", "")} - {datetime.timedelta(seconds=full_stat[i][key])}\n')
            self.make_tab(sort(full_stat[i]), i)
        self.mainlay.addWidget(self.tabs)
        debug(f'{self.tabs.count() = }')

    def make_tab(self, d, name):
        text = QLabel('')
        text.setAlignment(Qt.AlignmentFlag.AlignLeft)
        summ = 0
        for key in d:
            if d[key] != 0 and key not in lock_apps:
                text.setText(text.text() +
                             f'{key.replace(".exe", "")} - {datetime.timedelta(seconds=d[key])}\n')
                summ += d[key]
        if text.text().replace(' ', '') != '':
            text.setText(text.text() + f"\n{phrases['total:']} {datetime.timedelta(seconds=summ)}")
            self.tabs.addTab(text, name)

    def stat_upd(self):
        try:
            self.stat_l.setText(f"{phrases['today']}:\n")
            for key in sort(stat):
                if stat[key] != 0 and key not in lock_apps:
                    self.stat_l.setText(self.stat_l.text() +
                                        f'{key.replace(".exe", "")} - {datetime.timedelta(seconds=stat[key])}\n')
            self.stat_l.setText(self.stat_l.text() + f"\n{phrases['total:']} {datetime.timedelta(seconds=sid)}")
        except Exception as exc:
            error('failed to update stat:', exc)

    def closeEvent(self, event):  # Если удалить - при закрытии будет завершаться приложение
        event.ignore()
        self.hide()


class TimeAdder(QDialog):
    def __init__(self):
        super().__init__()
        log('TimeAdder __init__')

        self.setWindowTitle(phrases['time adder title'])

        self.layout = QVBoxLayout()
        self.app_name = QLineEdit()
        self.app_name.setPlaceholderText(phrases['application'])

        self.time = QSpinBox()
        self.time.setRange(1, 1440)
        self.time.setSuffix(f" {phrases['minutes']}")

        self.dates = QComboBox()
        self.dates.setWhatsThis(phrases['which date add to?'])
        self.dates.setEditable(True)
        ln = QLineEdit()
        ln.setPlaceholderText('YYYY-MM-DD')
        self.dates.setLineEdit(ln)
        a_today = str(datetime.date.today())
        for date in reversed(dirs):
            if a_today == date:
                self.dates.addItem(phrases['today'])
            else:
                self.dates.addItem(date)

        buttons = QHBoxLayout()
        self.ok_b = QPushButton(phrases['ok'])
        self.ok_b.clicked.connect(self.ok)  # noqa
        self.cancel_b = QPushButton(phrases['cancel'])
        self.cancel_b.clicked.connect(self.reject)  # noqa
        buttons.addWidget(self.ok_b)
        buttons.addWidget(self.cancel_b)

        self.layout.addWidget(self.dates)
        self.layout.addWidget(self.app_name)
        self.layout.addWidget(self.time)
        self.layout.addLayout(buttons)
        self.setLayout(self.layout)

    def ok(self):
        global stat, sid
        app_name = self.app_name.text().strip()
        date = self.dates.currentText()
        if app_name != '' and ':' not in app_name:
            if date == phrases['today']:
                if app_name in stat:
                    stat[app_name] += self.time.value() * 60
                else:
                    stat[app_name] = self.time.value() * 60
                sid += self.time.value() * 60
            else:
                if date not in full_stat:
                    full_stat[date] = {app_name: 0}
                if app_name in full_stat[date]:
                    full_stat[date][app_name] += self.time.value() * 60
                else:
                    full_stat[date][app_name] = self.time.value() * 60
                log(f'full_stat: {json.dumps(full_stat, indent=4)}')
                daysave(date)
                if limited:
                    set_all_sids()
            window.stat.stat_make()  # вносим изменения во всю статистику (визуально)
            self.accept()


class Translator(QWidget):
    def __init__(self):
        super().__init__()
        log('Translator __init__')
        self.setWindowTitle(phrases['translations'])
        self.setWindowIcon(app_icon)
        self.setWindowFlags(Qt.WindowType.CustomizeWindowHint | Qt.WindowType.WindowCloseButtonHint)

        self.mainlay = QVBoxLayout()
        self.layout = QVBoxLayout()

        self.lines = []

        for key in phrases.keys():
            widget = QLineEdit()
            widget.setPlaceholderText(key)
            widget.setText(phrases[key])
            self.layout.addWidget(widget)
            self.lines.append(widget)

        self.apply_b = QPushButton()
        self.apply_b.setText(phrases['apply'])
        self.apply_b.clicked.connect(self.apply)  # noqa

        widget = QWidget()
        widget.setLayout(self.layout)
        self.area = QScrollArea()
        # self.area.setLayout(self.layout)
        self.area.setWidget(widget)
        self.area.setWidgetResizable(True)

        self.mainlay.addWidget(self.area)
        self.mainlay.addWidget(self.apply_b)

        self.setLayout(self.mainlay)

    def closeEvent(self, event):  # Если удалить - при закрытии будет завершаться приложение
        event.ignore()
        self.hide()

    def apply(self):
        global window, sid, tran_name, phrases
        # self.save()
        translation = {}
        for w in self.lines:
            # print(w.placeholderText(), w.text())
            if w.text() != '':
                translation[w.placeholderText()] = w.text()
            else:
                translation[w.placeholderText()] = w.placeholderText()
        tran_name = translation['translation name']
        # sid += 2
        if translation != phrases and '.sltr' not in tran_name:
            if tran_name not in trans:
                trans.append(tran_name)
                transave(phrases, tran_name, tran_path)
            phrases = translation
            transave(phrases, tran_name, tran_path)
            debug('datasavee')
            datasave()
            # window = Timer()
            restart(sid_sess)
        else:
            log('translation did not changed or something')


class Startup(QWidget):
    def __init__(self):
        super().__init__()
        log('Startup __init__')
        self.setWindowTitle('Choose a language')

        self.layout = QVBoxLayout(self)
        # self.layout.setSizeConstraint(QLayout.SizeConstraint.SetFixedSize)

        self.list = QListView()
        self.lang = ''
        self.model = QStandardItemModel()
        self.list.setModel(self.model)
        debug(tran_list(tran_path))
        for t in tran_list(tran_path):
            item = QStandardItem(t)
            item.setEditable(False)
            self.model.appendRow(item)
        self.list.clicked.connect(self.on_clicked)  # noqa
        self.layout.addWidget(self.list)

        self.done_lay = QHBoxLayout()
        self.done_lay.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.done = QPushButton('Done')
        self.done.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        self.done.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_DialogApplyButton))
        self.done.clicked.connect(self.close)  # noqa
        self.done_lay.addWidget(self.done)

        self.layout.addLayout(self.done_lay)

    def on_clicked(self, index):
        self.lang = self.model.itemFromIndex(index).text()
        gettran(self.lang)
        self.setWindowTitle(phrases['startup window title'])
        self.done.setText(phrases['done'])
        log('Choosed language:', self.lang, 'done:', phrases['done'])

    def closeEvent(self, event):  # Если удалить - при закрытии будет завершаться приложение
        global window
        event.ignore()
        self.hide()
        # window = Timer()
        # window.show()
        restart(sid_sess)


class AdvancedSettings(QWidget):
    def __init__(self):
        super().__init__()
        log('AdvancedSettings __init__')
        self.setWindowTitle(phrases['advanced settings'])

        self.layout = QVBoxLayout()

        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.layout.addWidget(self.scroll)

        self.sc_lay = QVBoxLayout(self.scroll)

        self.globals = QLabel()
        self.globals.setWordWrap(True)
        self.globals.setGeometry(10, 10, 200, 200)
        self.sc_lay.addWidget(self.globals)
        # self.paths = QListView()
        # self.layout.addWidget(self.paths)

        self.setLayout(self.layout)

    def closeEvent(self, event):  # Если удалить - при закрытии будет завершаться приложение
        event.ignore()
        self.hide()

    # def showEvent(self, evebt):
    #     print(pformat(clean_globals()))


class BlockedHoursSetting(QWidget):
    def __init__(self, weekdays=None, week_state=None):
        super().__init__()
        if weekdays is None:
            self.weekdays = [phrases['mon'],
                             phrases['tue'],
                             phrases['wed'],
                             phrases['thu'],
                             phrases['fri'],
                             phrases['sat'],
                             phrases['sun']]
        else:
            self.weekdays = weekdays
        if week_state is None:
            self.week_state = [True for _ in range(7)]
        else:
            self.week_state = week_state

        self.layout = QHBoxLayout(self)
        self.layout.setAlignment(Qt.AlignmentFlag.AlignLeft)

        self.shutdowns = QShutdownBox()

        self.time1_l = QLabel(phrases['[time] from'])
        self.time1 = QTimeEdit()
        self.time1.timeChanged.connect(self.time)  # noqa

        self.time2_l = QLabel(phrases['[time] to'])
        self.time2 = QTimeEdit()
        self.time2.timeChanged.connect(self.time)  # noqa

        self.week_menu = QMenu()
        for i, v in enumerate(self.weekdays):
            act = self.week_menu.addAction(v)
            act.setCheckable(True)
            act.setChecked(True if self.week_state[i] is True else False)

        self.week = QLabel(phrases['if the day is'])
        self.week.mousePressEvent = self.week_menu_f
        self.update_week_l()

        self.layout.addWidget(self.shutdowns)
        self.layout.addWidget(self.time1_l)
        self.layout.addWidget(self.time1)
        self.layout.addWidget(self.time2_l)
        self.layout.addWidget(self.time2)
        self.layout.addWidget(self.week)
        self.time()

    def time(self):
        self.tm1 = self.time1.time().toPyTime()  # noqa
        self.tm2 = self.time2.time().toPyTime()  # noqa
        self.right_days = []  # noqa
        for a in self.week_menu.actions():
            if a.isChecked():
                self.right_days.append(self.week_menu.actions().index(a))

    def nowInRange(self) -> bool:  # noqa
        self.time()
        now = datetime.datetime.now()
        return True if is_between(now.time(), (self.tm1, self.tm2)) and now.weekday() in self.right_days else False

    def week_menu_f(self, event):
        self.week_menu.exec(event.globalPos())
        self.update_week_l()
        self.time()

    def update_week_l(self):
        text = []
        for i in self.week_menu.actions():
            if i.isChecked():
                text.append(i.text())
        if len(text) in (0, 7):
            self.week.setText(phrases['every day'])
            if len(text) == 0:
                for i in self.week_menu.actions():
                    i.setChecked(True)
        else:
            self.week.setText(f"{phrases['if the day is']} {', '.join(text)}")

    def setWeek(self, week: list):  # noqa
        self.weekdays = week
        self.time()
        self.update_week_l()

    def setState(self, state: list):  # noqa
        self.week_state = state
        for act in self.week_menu.actions():
            self.week_menu.removeAction(act)
        for i, v in enumerate(self.weekdays):
            act = self.week_menu.addAction(v)
            act.setCheckable(True)
            act.setChecked(True if self.week_state[i] is True else False)
        self.time()
        self.update_week_l()

    def getState(self) -> list:  # noqa
        self.week_state = []
        for act in self.week_menu.actions():
            self.week_state.append(act.isChecked())
        return self.week_state

    def getShutdownType(self) -> int:  # noqa
        return self.shutdowns.currentIndex()

    def setShutdownType(self, type_: int): # noqa
        self.shutdowns.setCurrentIndex(type_)

    def getTimeRange(self):  # noqa
        return [self.time1.time().toPyTime(), self.time2.time().toPyTime()]

    def setTimeRange(self, timeRange):  # noqa
        debug(f'{blocked_hours_time_range = }')
        self.time1.setTime(QTime(blocked_hours_time_range[0].hour, blocked_hours_time_range[0].minute))
        self.time2.setTime(QTime(blocked_hours_time_range[1].hour, blocked_hours_time_range[1].minute))


class QShutdownBox(QComboBox):
    def __init__(self):
        super().__init__()
        self.addItem(phrases['shutdown'])
        self.addItem(phrases['hiber'])
        self.addItem(phrases['restart'])
        self.addItem(phrases['to lock scr'])
        self.addItem(phrases['lock scr'])


def add_to_stat():
    global stat
    if thisapp in stat and thisapp not in lock_apps:
        stat[thisapp] += 1
    else:
        stat[thisapp] = 1


def startwin():
    global thisapp
    while True:
        try:
            thisapp = thiswin()
            sleep(0.7)
        except Exception as exc:
            error('Exception from "thiswin()": ', exc)


def thiswin() -> str:
    def smaller(s):
        if s != WindowType.LockedScreen:
            s = str(s)
            return s[0:49] if len(s) > 50 else s
        return WindowType.LockedScreen

    from activewindow import getAppName
    name = getAppName()['App2']
    if platform == 'linux' and os.getenv('XDG_SESSION_TYPE') == 'wayland' and name == WindowType.LockedScreen:
        name = WindowType.LockedScreen if is_linux_locked else "system"
    return smaller(name)


def lock_manager():
    global is_linux_locked
    # https://superuser.com/questions/820596/kde-screen-lock-log
    desktop_name = os.getenv('XDG_SESSION_PATH').split('/')[2]  # freedesktop / gnome / mint...
    cmd = Popen(["dbus-monitor \"type='signal',interface="
                 f"'org.{desktop_name}.ScreenSaver'\""], shell=True, stdout=PIPE)
    running = False
    while True:
        # debug(f'lock_manager: {is_linux_locked = }')
        if running:
            output = cmd.stdout.readline()
            is_linux_locked = b'true' in output
            running = False
        line = cmd.stdout.readline()
        if b"ActiveChange" in line and b'org.freedesktop.ScreenSaver' in line:
            running = True


@logger.catch
def pre_start():
    global today, delta_t, start, eye_save_time_end, sid_sess, sid, startwin_proc
    log('pre_start')
    try:
        sid_sess = abs(int(argv[1]))
        if sid_sess > sid:
            sid = sid_sess
    except Exception:  # noqa
        pass

    log(f'до конца отдыха от мон: {(eye_save_time_end - datetime.datetime.now()).total_seconds()}')
    log(f'{sett["eye_save_time"] = }\n'
        f'{str(sett["eye_save_time_end"]) = }\n'
        f'{sett["one_sess"] = }\n'
        f'{eye_save_activated = }')
    if eye_save_time * 60 > (eye_save_time_end - datetime.datetime.now()).total_seconds() > 0 \
            and eye_save_enabled:
        log('prestart-eyesave')
        eye_save()
    elif eye_save_enabled and \
            eye_save_time * 60 < (eye_save_time_end - datetime.datetime.now()).total_seconds():
        log('prestart_seeeeeeeecondif')
        eye_save_time_end = datetime.datetime.now().replace(microsecond=0) + \
                            datetime.timedelta(minutes=eye_save_time)  # noqa
    log(f'eye_save_time_end after upd: {sett["eye_save_time_end"]}\n'
        f'{eye_save_activated = }')
    if limit_should_be_activated():
        limit_out()
    if now_in_blocked_hours_range() and blocked_hours_enabled:
        activate_blocked_hours()

    Thread(target=startwin, daemon=True).start()
    if platform == 'linux' and os.getenv('XDG_SESSION_TYPE') == 'wayland':
        Thread(target=lock_manager, daemon=True).start()
    try:
        add_to_startup(desktop_file)
    except Exception as exc:
        error('failed to sturtup:', exc)


def block_s():
    log('block_s')
    window.show_block()


def add_clip():
    global app
    if app.clipboard() is not None:
        app.clipboard().setText(str(datetime.timedelta(seconds=sid)))
        log(f'Copied: {str(datetime.timedelta(seconds=sid))}')


def notif(title, msg, sec=2):
    try:
        window.tray_icon.showMessage(str(title), str(msg), app_icon, sec * 1000)
    except Exception as exc:
        error('Error in notif(): ', exc)
        ThTimer(1, notif, args=(title, msg, sec)).start()


def set_text_color():
    global timer_theme, theme
    debug('before:', prev_timer_theme, default_timer_theme)
    color = QColor()
    color.setNamedColor(timer_theme['text_color'])
    color_d = QColorDialog()
    color_d.setCurrentColor(color)

    if color_d.exec() == 1:
        color = color_d.currentColor().name()
        timer_theme['text_color'] = color
        debug(color)
        theme = 'Custom'
        debug('after:', prev_timer_theme, default_timer_theme)
    else:
        debug('QColorDialog (text) was canceled')


def set_background_color():
    global timer_theme, theme
    debug('before:', prev_timer_theme, default_timer_theme)
    color = QColor()
    color.setNamedColor(timer_theme['base_color'])
    color_d = QColorDialog()
    color_d.setCurrentColor(color)

    if color_d.exec() == 1:
        color = color_d.currentColor().name()
        timer_theme['base_color'] = color
        debug(color)
        theme = 'Custom'
        debug('after:', prev_timer_theme, default_timer_theme)
    else:
        debug('QColorDialog (background) was canceled')


@logger.catch
def notifications():
    global font
    global today, delta_t, start
    today = datetime.date.today()
    delta_t = today - start
    if delta_t.days > 0:
        log(f'if delta_t.days ({delta_t.days}) > 0: ')
        for i in dirs:
            debug(f'from dirs {i = }')
            if i == str(datetime.date.today()):
                dirs.remove(i)
                debug(f'from dirs deleted {i}')
        past_sid = 0
        past_day = max(dirs)
        debug(f'{past_day = }')
        for key in full_stat[past_day]:
            past_sid += full_stat[past_day][key]
            debug(f'added: {full_stat[past_day][key]}')
        debug(f'{past_sid = }\n{too_little_time = }')
        if past_sid < too_little_time and startup_notif_enabled:
            debug('too low')
            notif(phrases['info'], phrases['suspiciously little time'], 3)
        elif startup_notif_enabled:
            notif(phrases['info'], f"{phrases['previous time:']} "
                                   f"{datetime.timedelta(seconds=past_sid)}", 3)
        debug('datasavee')
        datasave()
        start = datetime.date.today()
        delta_t = today - start
    if need_to_show_startup:
        window.startup_window.show()
        window.hide()


def sett_upd():
    global sett
    debug('sett_upd', sett)
    sett = {}
    for key in default_sett.keys():
        if key == 'eye_save_time_end':
            sett[key] = str(globals()[key])
        elif key == 'blocked_hours_time_range':
            sett[key] = []
            for i in blocked_hours_time_range:
                sett[key].append(str(i))
        else:
            sett[key] = globals()[key]
    debug('sett2:', sett)


def limit_out():
    log('limit_out')
    debug(clean_globals())
    global eye_save_time, eye_save_time_end, lim_activated, today
    log(f'{eye_save_time_end = }, {eye_save_time = }')
    log(f'{sid = }, возможно: {poss[num_days[datetime.date.today()]]}')
    debug('datasavee')
    datasave()

    def locker():
        global lim_activated
        log('limit_out - locker')
        if lim_activated and limited and (sid > limit * 60 or sid >= poss[num_days[datetime.date.today()]]):
            lock_comp()
            ThTimer(1, locker).start()
        else:
            log('locker lim_activated - false')
            lim_activated = False

    def hibernator():
        # global lim_activated, today
        log('limit_out - hibernator')
        if lim_activated and limited and (sid > limit * 60 or sid >= poss[num_days[datetime.date.today()]]):
            log('hiber', f'{today = }', f'{datetime.date.today() = }\n\n\n\n')
            hiber()
            sleep(1)
            restart()

        # try:
        #     if lim_activated and limited and (sid > limit * 60 or sid >= poss[num_days[datetime.date.today()]]):
        #         # and \
        #         # datetime.date.today() == today:
        #         # hiber()
        #         print('hiber', datetime.date.today())
        #         ThTimer(2, hibernator).start()
        #     else:
        #         print('hibernator eye_save_activated - false')
        #         today = datetime.date.today()
        #         # set_all_sids()
        #         lim_activated = False
        #
        # except Exception as exc:
        #     print('hibernator Exception:', exc)
        #     lim_activated = False
        #     today = datetime.date.today()

    lim_activated = True
    if lim_off_type == 0:
        log('sutdown')
        shutdown(phrases)
    elif lim_off_type == 1:
        log('hiber')
        ThTimer(5, hibernator).start()
        notif(phrases['hiber'], phrases["needs rest from the monitor"])
    elif lim_off_type == 2:
        log('reboot')
        reboot(phrases)
    elif lim_off_type == 3:
        log('block')
        ThTimer(0.01, block_s).start()
    elif lim_off_type == 4:
        log('lock_scr')
        locker()
    else:
        lim_activated = False


def activate_blocked_hours():
    debug('activate_blocked_hours')
    debug(clean_globals())
    global blocked_hours_activated
    debug('datasavee')
    datasave()

    def locker():
        global blocked_hours_activated
        log('activate_blocked_hours - locker')
        if blocked_hours_activated and blocked_hours_enabled and now_in_blocked_hours_range():
            lock_comp()
            ThTimer(1, locker).start()
        else:
            log('locker blocked_hours_activated - false')
            blocked_hours_activated = False

    def hibernator():
        # global blocked_hours_activated, today
        log('activate_blocked_hours - hibernator')
        if blocked_hours_activated and blocked_hours_enabled and now_in_blocked_hours_range():
            log('hiber', f'{today = }', f'{datetime.date.today() = }\n\n\n\n')
            hiber()
            sleep(1)
            restart()
        #     today = datetime.date.today()

    blocked_hours_activated = True
    if blocked_hours_shutdown_type == 0:
        log('sutdown')
        shutdown(phrases)
    elif blocked_hours_shutdown_type == 1:
        log('hiber')
        ThTimer(5, hibernator).start()
        notif(phrases['hiber'], phrases["needs rest from the monitor"])
    elif blocked_hours_shutdown_type == 2:
        log('reboot')
        reboot(phrases)
    elif blocked_hours_shutdown_type == 3:
        log('block')
        ThTimer(0.01, block_s).start()
    elif blocked_hours_shutdown_type == 4:
        log('lock_scr')
        locker()
    else:
        blocked_hours_activated = False


def eye_save():
    global eye_save_time, eye_save_time_end, eye_save_activated
    log('eye_save')
    log(f'{eye_save_activated = }')
    log(f'{eye_save_time_end = }', f'{eye_save_time = }', f'{eye_save_type = }')
    debug('datasavee')
    datasave()

    def locker():
        global eye_save_activated
        log('eye_save - locker')
        if eye_save_activated and eye_save_enabled and (eye_save_time_end-datetime.datetime.now()).total_seconds() > 0:
            lock_comp()
            ThTimer(0.1, locker).start()
        else:
            log('locker eye_save_activated - false')
            set_all_sids()
            eye_save_activated = False

    def hibernator():
        global eye_save_activated
        log('eye_save - hibernator')
        if eye_save_activated and eye_save_enabled and (eye_save_time_end-datetime.datetime.now()).total_seconds() > 0:
            log('hiber - eye_save', f'{today = }', f'{datetime.date.today() = }')
            hiber()
            sleep(1)
            restart()
            # ThTimer(2, hibernator).start()
        # else:
        #     print('hibernator eye_save_activated - false')
        #     eye_save_activated = False

    eye_save_activated = True
    if eye_save_type == 0:
        log('sutdown')
        shutdown(phrases)
    elif eye_save_type == 1:
        log('hiber')
        ThTimer(5, hibernator).start()
        notif(phrases['hiber'], phrases["needs rest from the monitor"])
    elif eye_save_type == 2:
        log('reboot')
        reboot(phrases)
    elif eye_save_type == 3:
        log('block')
        ThTimer(0.01, block_s).start()
    elif eye_save_type == 4:
        log('lock_scr')
        locker()
    else:
        eye_save_activated = False


def set_all_sids():
    global num_days, pros
    log('set_all_sids')
    s = datetime.datetime.now()
    days = []
    for day in full_stat:  # добавляем даты
        days.append(datetime.datetime.strptime(day, '%Y-%m-%d').date())
    if datetime.date.today() not in days:
        days.append(datetime.date.today())  # добавляем сегодня
    num_sid = {}
    num_days = {}
    min_day = min(days)
    for day in days:
        try:
            num_sid[(day - min_day).days] = stat_sids[str(day)]
        except KeyError:
            error('KeyError')
            stat_sids[str(day)] = 0
        finally:
            num_sid[(day - min_day).days] = stat_sids[str(day)]
        num_days[day] = (day - min_day).days
        log('to num_sid added', (day - min_day).days, day)
    log(f'{num_sid = }')
    log(f'{num_days = }')
    log(f'{days = }')
    pros = []
    for day_ in num_sid:
        add_time(day_, num_sid[day_] // 60)
    if limited:
        skok_poss()
        log('index\tpros\tposs')
        for e in range(len(pros)):
            log(f'{e}\t{pros[e]}\t{poss[e]}')
        # error(f'poss: {json.dumps(dict(enumerate(poss)), indent=4)}')
    # print(f'{pros = }\n{poss = }')
    # print(get_key(num_sid, str(datetime.date.today())), '\n\n\n')
    # print(poss[get_key(num_sid, str(datetime.date.today()))], '\n\n\n')
    debug('setted all sids in', (datetime.datetime.now() - s).total_seconds(), 'sec\n')


def add_time(day, mins):
    while day > len(pros):
        pros.append(0)
    # if mins > 1440:
    #     mins = 1440
    try:
        mins += pros[day]
        pros.pop(day)
        pros.insert(day, mins)
    except IndexError:
        pros.insert(day, mins)


def skok_poss():
    log("skok_poss")
    global poss
    poss = []
    for a in range(len(pros) + 1):
        poss.append(limit)
    for i in range(len(pros)):
        if pros[i] > poss[i]:  # Если просижено больше, чем можно, то
            poss[i + 1] -= pros[i] - poss[i]  # На следующий день отнимается перебор
    # i = 0
    # while poss[-1] >= 0:
    #     if poss[i] < 0:
    #         poss[i+1] += poss[i]
    #         poss[i] = 0
    #     i += 1
    for i in range(len(poss)):
        if poss[i] < 0 and poss.index(poss[-1]) == poss.index(poss[i]):  # Если текущий элемент отр и он последний то:
            while poss[-1] < 0:  # Пока последний элемент меньше нуля:
                print(pformat(poss))
                poss.append(limit)
                poss[-1] += poss[-2]
                poss[-2] = 0
        elif poss[i] < 0 and poss.index(poss[-1]) != poss.index(poss[i]):
            poss[i + 1] += poss[i]
            poss[i] = 0
    # for e in poss:
    #     if e < 0:
    #         print('in skok_poss() element < 0')
    #         skok_poss()
    #         break


@logger.catch
def dataload():
    log('dataload')
    global sid, stat, start, delta_t, today, one_sess, eye_save_type, eye_save_time, sett, full_stat, stat_sids, \
        warn_before, eye_save_time_end, eye_save_enabled, limited, limit, lim_off_type, theme, tran_name, \
        need_to_show_startup

    def readsett():
        global one_sess, eye_save_type, eye_save_time, eye_save_time_end, sett, sid, eye_save_enabled, limited, limit, \
            lim_off_type, theme, warn_before, tran_name, timer_theme, prev_timer_theme, prev_theme, \
            blocked_hours_time_range, need_to_show_startup
        try:
            log(listdir())
            with open(sett_path, 'r') as file:  # Настройки
                sett1 = dict(json.load(file))
                for k, v in sett1.items():
                    if k in default_sett.keys():
                        # Индивидуальные параметры настроек
                        if k == 'eye_save_time_end':
                            globals()[k] = datetime.datetime.strptime(v, '%Y-%m-%d %H:%M:%S')
                        elif k == 'timer_theme':
                            prev_timer_theme = deepcopy(dict(v))
                            timer_theme = deepcopy(prev_timer_theme)
                            debug('tttttttttttt', prev_timer_theme is timer_theme)
                        elif k == 'theme':
                            theme = v
                            prev_theme = v
                        elif k == 'blocked_hours_time_range':
                            blocked_hours_time_range = [datetime.datetime.strptime(i, '%H:%M:%S').time() for i in v]
                        else:
                            globals()[k] = v
                log(f'{sett1 = }')
        except FileNotFoundError:
            log('Cannot find settings. Giving startup window')
            need_to_show_startup = True
            make_file('sett')
        except Exception as exc1:
            try:
                error('Failed to read settings because', exc1, ' trying to read as old settings', getcwd())
                with open(sett_path, 'r') as file:
                    sett_l = list(csv.reader(file, delimiter=','))[0]
                    one_sess = int(sett_l[0])
                    eye_save_type = int(sett_l[1])
                    eye_save_time = int(sett_l[2])
                    eye_save_time_end = datetime.datetime.strptime(sett_l[3], '%Y-%m-%d %H:%M:%S')
                    eye_save_enabled = to_bool(sett_l[4])
                    limited = to_bool(sett_l[5])
                    limit = int(sett_l[6])
                    lim_off_type = int(sett_l[7])
                    log(f'{sett = }')
                    log('удалось загрузить старые настройки ')
            except Exception as exc2:
                error('Дважды настройки на загружены:', exc2)
            make_file('sett')

    def readallstat():
        global start, dirs, stat_sids
        try:
            chdir(stat_path)
        except FileNotFoundError:
            mkdir(stat_path)
            chdir(stat_path)
        dirs = [e for e in listdir() if path.isdir(e)]
        debug(f'{dirs = }')
        if len(dirs) > 1:
            for d in dirs:
                full_stat[d] = {}
                stat_sids[d] = 0
                chdir(d)  # Заходим в папку со статистикой
                try:
                    with open('stat.csv', 'r', newline='') as file:
                        reader = csv.reader(file, delimiter=':')
                        for row in reader:
                            # print('rrrrrrrrrrrrrrrrrrrrrr', row[0])
                            if row[0] not in ['LockApp.exe']:
                                full_stat[d][row[0]] = int(row[1])
                                stat_sids[d] += int(row[1])

                    if d == str(datetime.date.today()):
                        full_stat[str(datetime.date.today())] = stat
                        del full_stat[str(datetime.date.today())]
                    chdir('..')  # Выходим из папки со статистикой
                except FileNotFoundError:
                    make_file('stat')
                    full_stat[d]['Sledilka'] = 0
                    chdir('..')  # Выходим из папки со статистикой
        chdir(base_path)  # Выходим в начальную папку

    log('sett')
    try:
        log('try readsett')
        readsett()
        gettran(tran_name)
    except Exception as exc:
        log(f'except {exc}')
        make_file('sett')
    finally:
        log('finally readsett, sett:', sett, 'edn')
        readsett()
        gettran(tran_name)
    # if tran_name != phrases['translation name']:
    #     tran_name = phrases['translation name']
    log('stat')
    try:
        readstat()
    except Exception as exc:
        log('Exception:', exc)
        make_file('stat')
    finally:
        readstat()
        # try:
        readallstat()
    # if limited:
    set_all_sids()
    # except FileNotFoundError:
    #     log('except FileNotFoundError:')
    #     make_file('stat')
    # except ValueError:
    #     log('ValueError')
    #     make_file('stat')
    # except IndexError:
    #     log('IndexError')
    #     make_file('stat')
    # finally:
    #     readallstat()

    log(f'stat: {stat}')
    log(f'sett: {sett}')
    # log(f'full_stat: {json.dumps(full_stat, indent=4)}')
    log(f'stat_sids: {json.dumps(stat_sids, indent=4)}')
    log('dataload.end\n')


def readstat():
    global sid, start
    sid = 0
    stat_exists = True
    try:
        chdir(stat_path)
    except FileNotFoundError:
        mkdir(stat_path)
        chdir(stat_path)
        stat_exists = False
    try:
        chdir(str(datetime.date.today()))
    except FileNotFoundError:
        mkdir(str(datetime.date.today()))
        chdir(str(datetime.date.today()))
        if stat_exists:
            start = datetime.date.today() - datetime.timedelta(days=1)
            debug('noooooooooooot toaaaaaay')
    try:
        with open('stat.csv', 'r', newline='') as file:
            reader = csv.reader(file, delimiter=':')
            for row in reader:
                stat[row[0]] = int(row[1])
                sid += int(row[1])
    except FileNotFoundError:
        make_file('stat')
        debug('mkfl')
    chdir(base_path)


def gettran(name: str):  # Устанавливает словарь перевода в phrases
    global phrases, trans, tran_name

    prev = getcwd()

    def get():
        global phrases, tran_name
        # print('aaaaaaaaaaaaaaa', tran_name, phrases)
        with open(f'{name}.sltr', 'r') as file:
            phrases1 = dict(json.load(file))
            for k in phrases1.keys():
                phrases[k] = phrases1[k]
        tran_name = name
        if phrases['translation name'] != name:
            phrases['translation name'] = name
            transave(phrases, tran_name, tran_path)

    try:
        chdir(tran_path)
    except FileNotFoundError:
        transave(phrases, tran_name, tran_path)
        chdir(tran_path)
    debug(listdir(), 'llllllllllll', getcwd())
    trans = tran_list(tran_path)
    log(f'{trans = }')
    try:
        get()
    except FileNotFoundError:
        error(f'FileNotFoundError from gettran("{name}")')
        transave(phrases, tran_name, tran_path)
    except Exception as exc:
        error('cannot get translation:', exc)
    finally:
        get()
        chdir(prev)


def make_file(type_f='stat'):
    log('makefile')
    if type_f == 'stat':
        with open('stat.csv', 'w') as file:
            writer = csv.writer(file, delimiter=':', lineterminator='\n')
            writer.writerow(['Sledilka', 0])
    elif type_f == 'sett':
        debug(f'{sett = }')
        sett_upd()
        log('sett_updated')
        with open(sett_path, 'w') as file:
            json.dump(sett, file, ensure_ascii=False)
        # debug('wrote', sett, '\nglobals:', clean_globals())


def datasave():
    log('datasave')
    sett_upd()
    log('sett1')
    with open(sett_path, 'w') as file:  # Настройки
        json.dump(sett, file, ensure_ascii=False)
    log('sett2')
    statsave()


def daysave(day):
    day = str(day)
    try:
        chdir(stat_path)
    except FileNotFoundError:
        mkdir(stat_path)
        chdir(stat_path)
    try:
        chdir(day)
    except FileNotFoundError:
        # значит начался новый день
        mkdir(day)
        chdir(day)
    with open('stat.csv', 'w') as file:
        writer = csv.writer(file, delimiter=':', lineterminator='\n')
        for key in full_stat[day].keys():
            writer.writerow([key, full_stat[day][key]])
    chdir(base_path)


def statsave():
    try:
        chdir(stat_path)
    except FileNotFoundError:
        mkdir(stat_path)
        chdir(stat_path)
    try:
        # значит не начался новый день
        chdir(str(datetime.date.today()))
    except FileNotFoundError:
        # значит начался новый день
        mkdir(str(datetime.date.today()))
        chdir(str(datetime.date.today()))
    with open('stat.csv', 'w') as file:
        writer = csv.writer(file, delimiter=':', lineterminator='\n')
        for key in stat.keys():
            writer.writerow([key, stat[key]])
    chdir(base_path)


@logger.catch
def lib_import():
    def copy(src, dst):
        if path.isdir(src):
            try:
                shutil.copytree(src, dst)
            except Exception as exc:
                log('copytree:', exc)
        else:
            try:
                shutil.copy(src, dst)
            except Exception as exc:
                log('copy:', exc)

    debug('PATHS:', base_path, sett_path, stat_path, log_path, tran_path)
    log('lib_import:')
    lib_dir = os.path.split(__file__)[0]
    debug('paths:', lib_dir, getcwd())
    debug(listdir())
    copy(path.join(lib_dir, 'Translations'), tran_path)
    copy(path.join(lib_dir, 'icon.ico'), path.join(base_path, 'icon.ico'))
    copy(path.join(lib_dir, 'Segoe UI.ttf'), path.join(base_path, 'Segoe UI.ttf'))

    if 'Sledilka.desktop' not in listdir(base_path):
        with open(desktop_file_path, 'w') as file:
            file.write(desktop_file)
    debug(listdir())


def new_day():
    global today
    today = datetime.date.today()


def restart(sid_sess_: int = 0):
    datasave()
    try:
        # os.execv(executable, [executable, __file__, str(sid_sess_)])
        # run(f'{executable} {__file__} {str(sid_sess_)}')
        # sys.exit(0)
        # exec(argv[0], {'sid_sess': sid_sess_})
        # os.execl(executable, f'{__file__} {str(sid_sess_)}')  # works if not compiled
        os.execl(executable, executable, argv[0], str(sid_sess_))  # works if not compiled
    except Exception as exc:
        error(exc)
        error(argv + [str(sid_sess_)])
        os.execv(argv[0], [argv[0], str(sid_sess_)])  # works if compiled
        debug('worked if compiled')


def clean_globals():
    g = {}
    for k, v in globals().copy().items():
        try:
            k, v = deepcopy(k), deepcopy(v)
            if k not in ['__annotations__', '__cached__', '__doc__', 'g', '__loader__', 'full_stat'] and \
                    str(type(v)) != "<class 'function'>" and \
                    ('Q' not in k if not k.isupper() else True):  # allow QT_VERSION
                g[k] = v
        except Exception: # noqa
            pass
    return g


def is_blocked() -> bool:
    return eye_save_activated or lim_activated or blocked_hours_activated


def now_in_blocked_hours_range(now=None):
    if now is None:
        now = datetime.datetime.now()
    tm1 = blocked_hours_time_range[0]
    tm2 = blocked_hours_time_range[1]
    right_days = []  # list of integers; integer = num_of_weekday - 1 (6 = sunday)
    for i, v in enumerate(blocked_hours_week_state):
        if to_bool(str(v)):
            right_days.append(i)
    return is_between(now.time(), (tm1, tm2)) and now.weekday() in right_days
    # return window.sett_w.s_blk_hrs_setts.nowInRange()


def limit_should_be_activated() -> bool:
    return limited and (sid >= limit * 60 or sid >= poss[num_days[datetime.date.today()]] * 60)


if __name__ == '__main__':
    # while True:
    log('\n'*5)
    debug(f'{argv = }')
    lib_import()
    dataload()

    app = QApplication(argv)
    app_icon = QIcon(path.join(base_path, 'icon.ico'))
    app.setDesktopFileName(desktop_file_path)
    app.setWindowIcon(app_icon)
    app.setApplicationDisplayName(phrases['app name'])
    app.setApplicationName('Sledilka')
    QFontDatabase.addApplicationFont('Segoe UI.ttf')
    font = QFont('Segoe UI', 30)
    font.setLetterSpacing(QFont.SpacingType.AbsoluteSpacing, -1.5)
    font.setBold(False)
    font.setWeight(40)

    pre_start()
    window = Timer()
    notifications()
    # input(argv)
    if QT_VERSION == 5:
        app.exec_()
    else:
        app.exec()
