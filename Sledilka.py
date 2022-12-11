import csv
import datetime
import json
from multiprocessing import Process
from multiprocessing.managers import SharedMemoryManager
from os import listdir, chdir, mkdir, path, popen, getcwd
from sys import argv, platform as pt
from threading import Thread
from time import sleep
from PyQt6.QtCore import QSize, Qt, QEvent, QTimer
from PyQt6.QtGui import QPainter, QIcon, QFont, QColor, QAction
from PyQt6.QtWidgets import QApplication, QSystemTrayIcon, QWidget, QMenu, QLabel, QVBoxLayout, QSpinBox, \
    QSizePolicy, QLayout, QGroupBox, QComboBox, QHBoxLayout, QTabWidget, QPushButton, \
    QDialog, QLineEdit, QMessageBox  # QAction,
from darkdetect import theme as th

platform = pt
if platform == 'win32':
    from ctypes import windll
    import winshell
    from win32com.client import Dispatch

limited = False
limit = 0  # Возможное колличество времени за день (мин)
lim_off_type = 0  # Тип выкла (выкл, гибернация, перезагрузка, заблок экран, экран блок)
lim_activated = False
sid = 0  # Время за компом (сек)
sid_sess = 0  # Время текущей сессии (сек)
stat = {}  # Сегодняшняя статистика
full_stat = {str(datetime.date.today()): {}}  # Статистика вся, кроме сегодня
stat_sids = {str(datetime.date.today()): 0}
warn_before = 3  # Показ уведомления, когда остаётся warn_before минут до чего-либо

pros = []  # Время по дням, сколько было просижено в каждый день
vozm = []  # Сколько можно было вообще просидеть
num_days = {}  # №date: date

one_sess = 0  # Длительность сессии (до выключения, минут) (если ноль - отключено)
eye_save_type = 0  # Тип выключения компа
eye_save_time = 1  # Длительность отдыха от монитора (минут)
eye_save_time_end = datetime.datetime.now().replace(microsecond=0)  # Конец отдыха от монитора
eye_save_enabled = False
# eye_save_time_end = datetime.datetime.strptime(
#     datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'), '%Y-%m-%d %H:%M:%S')
blocked = False
start = datetime.date.today()
today = datetime.date.today()
delta_t = start - today
sett = {'one_sess': 0,
        'eye_save_type': 0,
        'eye_save_time': 1,
        'eye_save_time_end': datetime.datetime.now().replace(microsecond=0),
        'eye_save_enabled': False,
        'limited': False,
        'limit': 0,
        'lim_off_type': 0,
        'theme': 'Light',
        'warn_before': 0}
thisapp = 'Sledilka.exe'
wintitle = ''
saved = False
dirs = []
too_little_time = 1
phrases = {
    'stat title': 'Статистика',
    'shutdown': 'Выключить компьютер',
    'restart': 'Перезагрузка',
    'hiber': 'Гибернация',
    'to lock scr': 'Заблокировать экран',
    'lock scr': 'Экран блокировки',
    'block title': 'Следилка - Блокировщик ТЕБЯ',
    'add time': 'Добавить',
    'needs monitor rest': 'Требуется отдых от монитора',
    'time adder title': 'Добавить время',
    'application': 'Приложение',
    'ok': 'OK',
    'cancel': 'Отмена',
    'apply': 'Применить',
    'whats datas?': 'На какую дату добавить?',
    'today': 'Сегодня',
    'app name': 'Следилка',
    'dark': 'Тёмная',
    'light': 'Светлая'
}
theme = th()


class Timer(QWidget):

    def __init__(self):
        log('Timer __init__')
        super().__init__()
        self.setFixedSize(QSize(145, 110))
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint)
        self.setWindowTitle(phrases['app name'])
        self.setWindowIcon(QIcon('icon.ico'))

        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.offset = None
        self.in_tray = False
        self.installEventFilter(self)
        self.time_show = QLabel(str(datetime.timedelta(seconds=sid)))
        self.time_show.setAlignment(Qt.AlignmentFlag.AlignCenter)
        if theme == 'Light':
            self.time_show.setStyleSheet("QLabel { color : black; }")
        else:
            self.time_show.setStyleSheet("QLabel { color : white; }")

        self.sett_w = Settings()
        self.stat = Statistic()
        self.blk = Block()

        self._actions()

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.time_show)

        self.tray_icon = QSystemTrayIcon(self)
        self.tray_icon.setIcon(QIcon('icon.ico'))
        self.tray_icon.activated.connect(self.restore_window)

        self.context = QMenu(self)
        self.context.addAction(self.copy)
        # self.copy_act.setShortcut(QKeySequence.StandardKey.Copy)
        self.context.addSeparator()
        self.context.addAction(self.a_stat)
        self.context.addAction(self.a_sett)
        self.context.addSeparator()
        self.context.addAction(self.a_hide)

        self.tray_menu = QMenu()

        self.tray_menu.addAction(self.a_sett)
        self.tray_menu.addAction(self.a_stat)
        self.tray_menu.addSeparator()
        self.tray_menu.addAction(self.a_show)
        self.tray_menu.addAction(self.a_hide)
        self.tray_icon.setContextMenu(self.tray_menu)
        self.tray_icon.show()

        # threading.Timer(10, self.runtimesec).start()

        self.timer = QTimer()
        self.timer.timeout.connect(self.runtimesec)
        self.timer.setInterval(1000)
        self.checker_timer = QTimer()
        self.checker_timer.timeout.connect(self.checker)
        self.checker_timer.setInterval(1000)

        if not lim_activated and not blocked:
            self.show()
        else:
            self.hide()
        self.it = 0  # Итерации
        self.runtime()

    def _actions(self):
        self.copy = QAction('Копировать', self)
        self.copy.triggered.connect(self.sid_add)

        self.a_stat = QAction('Статистика', self)
        self.a_stat.triggered.connect(self.stat.show)

        self.a_sett = QAction('Настройки', self)
        self.a_sett.triggered.connect(self.sett_w.show)

        self.a_show = QAction('Показать', self)
        self.a_show.triggered.connect(self.show)

        self.a_hide = QAction('Скрыть', self)
        self.a_hide.triggered.connect(self.hide)

    @staticmethod
    def sid_add():
        add_clip()

    def showEvent(self, event):
        self.in_tray = False

    def hideEvent(self, event):
        self.in_tray = True

    def closeEvent(self, event):  # Запрет закрытия окна
        event.ignore()
        self.hide()

    def paintEvent(self, ev):  # Создание окна
        if sid > 36000:
            self.setFixedSize(165, 120)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.renderHints(painter).Antialiasing)  # Убирание некрасивых краёв PyQt6
        # painter.setRenderHint(QPainter.Antialiasing)
        if theme == 'Light':
            painter.setBrush(Qt.GlobalColor.white)
        else:
            painter.setBrush(QColor(43, 43, 43))
        painter.drawRoundedRect(self.rect(), 25, 25)  # Закругление краёв

    def eventFilter(self, source, event):  # Перетаскивание окна
        if event.type() == QEvent.Type.MouseButtonPress and event.button() == Qt.MouseButton.LeftButton:
            self.offset = event.pos()            # PyQt6
        elif event.type() == QEvent.Type.MouseMove and self.offset is not None:
            self.move(self.pos() - self.offset + event.pos())
            return True
        elif event.type() == QEvent.Type.MouseButtonRelease:
            self.offset = None
        return super().eventFilter(source, event)

    def contextMenuEvent(self, e):  # Контекстное меню
        self.context.exec(self.mapToGlobal(e.pos()))

    def restore_window(self, reason):  # Возвращение окна из трея
        if reason != QSystemTrayIcon.ActivationReason.Context:
            if self.isHidden():
                self.show()
            else:
                self.hide()

    def runtime(self):
        log('runtime')
        global sid
        self.time_show.setFont(QFont('Segoe UI', 30))
        self.time_show.setAlignment(Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignVCenter)
        # self.time_show.setAlignment(Qt.AlignHCenter | Qt.AlignVCenter)

        self.stat.updater.start()
        self.timer.start()
        self.checker_timer.start()

    def checker(self):
        global sid, sid_sess, eye_save_time_end, start, saved, stat, thisapp, wintitle
        # thisapp = win_info[0]
        # wintitle = win_info[1]
        s = datetime.datetime.now()
        if thisapp not in ['LockApp.exe', 'LockScr'] and not blocked and not lim_activated:
            saved = False
            if self.isHidden() and not self.in_tray:
                self.show()
            # ???
            Thread(target=add_to_stat).start()
            # ???
            if self.it == 60:  # Сейвы каждую минуту
                Thread(target=datasave).start()
                self.it = 0
            if sid_sess >= one_sess * 60 and eye_save_enabled:  # Если время сессии подошло к концу, то:
                log('end of sess')
                print('eeeeeeeeeeeeeeeeeeeendofsess')
                sid_sess = 0
                eye_save_time_end = datetime.datetime.strptime(
                    datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'), '%Y-%m-%d %H:%M:%S') + \
                    datetime.timedelta(minutes=eye_save_time)
                Thread(target=datasave).start()
                eye_save()
            elif sid_sess > one_sess * 60:
                sid_sess = 0
            if limited and (sid >= limit * 60 or sid >= vozm[num_days[datetime.date.today()]] * 60):
                print(limited, sid >= limit * 60, sid >= vozm[num_days[datetime.date.today()]] * 60)
                limit_out()
                print('liiiiiimit')
        elif blocked or lim_activated:
            if not self.in_tray:
                self.hide()
                self.in_tray = True
        elif not saved and thisapp not in ['LockApp.exe', 'LockScr']:
            Thread(target=datasave).start()
            saved = True
        if datetime.date.today() != start:
            sid = 0
            full_stat[str(start)] = stat
            start = datetime.date.today()
            stat = {'Sledilka.exe': 0}
            if limited:
                set_all_sids()
        if theme == 'Light':
            self.time_show.setStyleSheet("QLabel { color : black; }")
        else:
            self.time_show.setStyleSheet("QLabel { color : white; }")
        if sid_sess + warn_before * 60 == one_sess * 60:  # сек + мин * 60 == мин * 60
            notif('Отдых от монитора', 'Сессия скоро закончится')
            print('NOOOOOOOOOOOOOOTIFED')
        elif limited and limit * 60 == sid + warn_before * 60:  # мин * 60 == сек + мин * 60
            notif('Лимит времени', 'Лимит времени скоро закончится')
            print('NOOOOOOOOOOOOOOTIFED')
        # print((datetime.datetime.now() - s).total_seconds(), 'cекунд итерация checker')

    def runtimesec(self):
        global sid, sid_sess
        # print(f'{thisapp = }, {blocked = }')
        if thisapp not in ['LockApp.exe', 'LockScr'] and not blocked and not lim_activated:
            self.time_show.setText(str(datetime.timedelta(seconds=sid)))
            sid += 1
            sid_sess += 1
            self.it += 1

    def show_block(self):
        print('show_block')
        if (blocked and sid_sess >= one_sess * 60 and eye_save_enabled) or \
                (lim_activated and limited and sid >= limit * 60):
            if not self.blk.isActiveWindow():
                self.blk.up()


class Settings(QWidget):
    def __init__(self):
        super().__init__()
        self.s_eye_rest_label = QLabel('Требовать отдыха от монитора на')
        log('Settings __init__')
        self.setWindowTitle("Настройки")
        self.setWindowIcon(app_icon)
        self.setWindowFlags(Qt.WindowType.CustomizeWindowHint | Qt.WindowType.WindowCloseButtonHint)

        self.layout = QVBoxLayout()
        self.layout.setSizeConstraint(QLayout.SizeConstraint.SetFixedSize)

        self._set_eye_save()
        self._set_limits()
        self._set_warn_before()
        self._set_color()

        self.update_interface()
        self._set_buttons()

        self.setLayout(self.layout)

    # def set_s_eye_type(self):
    # if self.s_one_sess_ch.isChecked():
    #     self.s_eye_sess.setEnabled(True)
    #     self.s_eye.setEnabled(True)
    # else:
    #     self.s_eye_sess.setEnabled(False)
    #     self.s_eye.setEnabled(False)

    def _set_eye_save(self):
        self.s_one_sess_gr = QGroupBox('Отдых от монитора')  # Отдых от монитора:
        self.s_one_sess_gr.setCheckable(True)

        self.s_eye_sess = QLabel('Длительность сеанса')
        self.s_eye = QSpinBox()
        self.s_eye.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        self.s_eye.setRange(1, 1440)
        self.s_eye.setSuffix(' мин.')

        self.s_eye_lay = QHBoxLayout()
        self.s_eye_lay.setAlignment(Qt.AlignmentFlag.AlignLeft)
        self.s_eye_lay.addWidget(self.s_eye_sess)
        self.s_eye_lay.addWidget(self.s_eye)
        self.s_eye_lay.setSizeConstraint(QLayout.SizeConstraint.SetFixedSize)

        self.s_eye_sess_end_label = QLabel('При окончании сеанса:')

        self.s_eye_sess_end_list = QComboBox()
        self.s_eye_sess_end_list.addItem(phrases['shutdown'])
        self.s_eye_sess_end_list.addItem(phrases['hiber'])
        self.s_eye_sess_end_list.addItem(phrases['restart'])
        self.s_eye_sess_end_list.addItem(phrases['to lock scr'])
        self.s_eye_sess_end_list.addItem(phrases['lock scr'])

        self.s_eye_sess_end_lay = QHBoxLayout()
        self.s_eye_sess_end_lay.addWidget(self.s_eye_sess_end_label)
        self.s_eye_sess_end_lay.addWidget(self.s_eye_sess_end_list)

        self.s_eye_rest_spin = QSpinBox()
        self.s_eye_rest_spin.setRange(1, 1440)
        self.s_eye_rest_spin.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        self.s_eye_rest_spin.setSuffix(' мин.')

        self.s_eye_rest_lay = QHBoxLayout()
        self.s_eye_rest_lay.setAlignment(Qt.AlignmentFlag.AlignLeft)
        self.s_eye_rest_lay.addWidget(self.s_eye_rest_label)
        self.s_eye_rest_lay.addWidget(self.s_eye_rest_spin)

        self.s_one_sess_gr_lay = QVBoxLayout(self.s_one_sess_gr)
        self.s_one_sess_gr_lay.addLayout(self.s_eye_lay)
        self.s_one_sess_gr_lay.addLayout(self.s_eye_sess_end_lay)
        self.s_one_sess_gr_lay.addLayout(self.s_eye_rest_lay)

        self.layout.addWidget(self.s_one_sess_gr)

    def _set_limits(self):
        self.s_lim_gr = QGroupBox('Дневной лимит времени')
        self.s_lim_gr.setCheckable(True)

        self.s_lim_end_list = QComboBox()
        self.s_lim_end_list.addItem(phrases['shutdown'])
        self.s_lim_end_list.addItem(phrases['hiber'])
        self.s_lim_end_list.addItem(phrases['restart'])
        self.s_lim_end_list.addItem(phrases['to lock scr'])
        self.s_lim_end_list.addItem(phrases['lock scr'])

        self.s_lim_lab = QLabel('по прошествии')

        self.s_limit = QSpinBox()
        self.s_limit.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        self.s_limit.setRange(1, 1440)
        self.s_limit.setSuffix(' мин.')

        self.s_lim_lay = QHBoxLayout(self.s_lim_gr)
        self.s_lim_lay.setAlignment(Qt.AlignmentFlag.AlignLeft)
        self.s_lim_lay.addWidget(self.s_lim_end_list)
        self.s_lim_lay.addWidget(self.s_lim_lab)
        self.s_lim_lay.addWidget(self.s_limit)
        self.s_lim_lay.setSizeConstraint(QLayout.SizeConstraint.SetFixedSize)

        self.layout.addWidget(self.s_lim_gr)

    def _set_warn_before(self):
        self.s_warn_gr = QGroupBox('Предварительные оповещения')
        self.s_warn_gr.setCheckable(True)

        self.s_warn = QSpinBox()
        self.s_warn.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        self.s_warn.setRange(1, 1440)
        self.s_warn.setSuffix(' мин.')
        self.s_warn.setPrefix('Показывать уведомления за ')

        self.s_warn_gr_lay = QVBoxLayout(self.s_warn_gr)
        self.s_warn_gr_lay.addWidget(self.s_warn)

        self.layout.addWidget(self.s_warn_gr)

    def _set_color(self):
        self.s_theme_gr = QGroupBox('Тема оформления')

        self.s_theme_list = QComboBox()
        self.s_theme_list.addItem(phrases['dark'])
        self.s_theme_list.addItem(phrases['light'])

        self.s_theme_gr_lay = QHBoxLayout(self.s_theme_gr)
        self.s_theme_gr_lay.addWidget(self.s_theme_list)

        self.layout.addWidget(self.s_theme_gr)

    def _set_buttons(self):
        self.butt_lay = QHBoxLayout()
        self.butt_lay.setAlignment(Qt.AlignmentFlag.AlignRight)

        self.butt_ok = QPushButton()
        self.butt_ok.setText(phrases['ok'])
        self.butt_ok.clicked.connect(self.sett_save)
        self.butt_ok.clicked.connect(self.close)
        self.butt_ok.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        self.butt_lay.addWidget(self.butt_ok)

        self.butt_cancel = QPushButton()
        self.butt_cancel.setText(phrases['cancel'])
        self.butt_cancel.clicked.connect(self.close)
        self.butt_cancel.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        self.butt_lay.addWidget(self.butt_cancel)

        self.butt_apply = QPushButton()
        self.butt_apply.setText(phrases['apply'])
        self.butt_apply.clicked.connect(self.sett_save)
        self.butt_apply.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        self.butt_lay.addWidget(self.butt_apply)

        self.layout.addLayout(self.butt_lay)

    def sett_save(self):
        global one_sess, eye_save_type, eye_save_time, eye_save_time_end, eye_save_enabled, limited, lim_off_type, \
            limit, theme, warn_before
        one_sess = self.s_eye.value()
        eye_save_enabled = self.s_one_sess_gr.isChecked()  # Длительность сеанса
        # eye_save_time_end = datetime.datetime.now().replace(microsecond=0) + \
        #     datetime.timedelta(minutes=eye_save_time)
        if self.s_eye_sess_end_list.currentText() == phrases['shutdown']:  # Определение типа выкла
            eye_save_type = 0
        elif self.s_eye_sess_end_list.currentText() == phrases['hiber']:
            eye_save_type = 1
        elif self.s_eye_sess_end_list.currentText() == phrases['restart']:
            eye_save_type = 2
        elif self.s_eye_sess_end_list.currentText() == phrases['to lock scr']:
            eye_save_type = 3
        elif self.s_eye_sess_end_list.currentText() == phrases['lock scr']:
            eye_save_type = 4
        eye_save_time = self.s_eye_rest_spin.value()

        limited = self.s_lim_gr.isChecked()  # Лимит
        if self.s_lim_end_list.currentText() == phrases['shutdown']:  # Определение типа выкла
            lim_off_type = 0
        elif self.s_lim_end_list.currentText() == phrases['hiber']:
            lim_off_type = 1
        elif self.s_lim_end_list.currentText() == phrases['restart']:
            lim_off_type = 2
        elif self.s_lim_end_list.currentText() == phrases['to lock scr']:
            lim_off_type = 3
        elif self.s_lim_end_list.currentText() == phrases['lock scr']:
            lim_off_type = 4
        limit = self.s_limit.value()
        print(f'{sett["limited"] = }, {self.s_lim_end_list.currentText() = } - {sett["lim_off_type"] = }, '
              f'{sett["limit"] = }')
        print(f'{sett["eye_save_enabled"] = }')

        if self.s_theme_list.currentText() == phrases['dark']:
            theme = 'Dark'
        else:
            theme = 'Light'
        if self.s_warn_gr.isChecked():
            warn_before = self.s_warn.value()
        else:
            warn_before = 0
        datasave()

    def update_interface(self):
        self.s_one_sess_gr.setChecked(eye_save_enabled)
        self.s_eye.setValue(one_sess)
        if eye_save_type == 0:  # Определение типа выкла
            self.s_eye_sess_end_list.setCurrentText(phrases['shutdown'])
        elif eye_save_type == 1:
            self.s_eye_sess_end_list.setCurrentText(phrases['hiber'])
        elif eye_save_type == 2:
            self.s_eye_sess_end_list.setCurrentText(phrases['restart'])
        elif eye_save_type == 3:
            self.s_eye_sess_end_list.setCurrentText(phrases['to lock scr'])
        elif eye_save_type == 4:
            self.s_eye_sess_end_list.setCurrentText(phrases['lock scr'])
        self.s_eye_rest_spin.setValue(eye_save_time)

        self.s_lim_gr.setChecked(limited)
        if lim_off_type == 0:  # Определение типа выкла
            self.s_lim_end_list.setCurrentText(phrases['shutdown'])
        elif lim_off_type == 1:
            self.s_lim_end_list.setCurrentText(phrases['hiber'])
        elif lim_off_type == 2:
            self.s_lim_end_list.setCurrentText(phrases['restart'])
        elif lim_off_type == 3:
            self.s_lim_end_list.setCurrentText(phrases['to lock scr'])
        elif lim_off_type == 4:
            self.s_lim_end_list.setCurrentText(phrases['lock scr'])
        self.s_limit.setValue(limit)

        if theme == 'Dark':
            self.s_theme_list.setCurrentText(phrases['dark'])
        else:
            self.s_theme_list.setCurrentText(phrases['light'])

        if warn_before > 0:
            self.s_warn_gr.setChecked(True)
            self.s_warn.setValue(warn_before)
        else:
            self.s_warn_gr.setChecked(False)
            self.s_warn.setValue(1)

    def showEvent(self, event):
        self.update_interface()

    def closeEvent(self, event):  # Если удалить - при закрытии будет завершаться приложение
        event.ignore()
        self.hide()


class Block(QWidget):
    def __init__(self):
        super().__init__()
        log('Block __init__')
        self.setWindowFlags(Qt.WindowType.WindowStaysOnTopHint)
        self.setStyleSheet("background: black;")
        self.setWindowTitle(phrases['block title'])
        self.setWindowIcon(QIcon('icon.ico'))
        self.setWindowOpacity(0.8)
        if (blocked or lim_activated) and (eye_save_type == 3 or lim_off_type == 3):
            self.showFullScreen()
            self.activateWindow()
        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignCenter)
        self.setLayout(layout)
        self.label = QLabel()
        self.label.setStyleSheet("color: red;")
        if not lim_activated:
            self.label.setText("Отдых от монитора")
        else:
            self.label.setText('Ваше время истекло 👎')
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.label.setFont(QFont("Arial", 40))
        layout.addWidget(self.label)
        self.b_timer = QLabel()
        self.b_timer.setStyleSheet("color: blue;")
        if not lim_activated:
            self.b_timer.setText(f'До конца Х минут')
        else:
            self.b_timer.setText('')
        self.b_timer.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.b_timer.setFont(QFont("Arial", 40))
        layout.addWidget(self.b_timer)
        self.noclo()

        self.blocksec_timer = QTimer()
        self.blocksec_timer.timeout.connect(self.blocksec)
        self.blocksec_timer.start(1000)

    def noclo(self):
        global blocked, lim_activated
        if (not self.isActiveWindow()) and \
                ((blocked and eye_save_type == 3) or (lim_activated and lim_off_type == 3)):
            self.up()
        if (blocked and eye_save_type == 3) or (lim_activated and lim_off_type == 3):
            if (eye_save_time_end - datetime.datetime.now()).total_seconds() < 1:
                blocked = False
            if sid < limit * 60:
                lim_activated = False
            QTimer.singleShot(100, self.noclo)
        elif not blocked and not lim_activated:
            QTimer.singleShot(1000, self.noclo)

    def up(self):
        print('up')
        print(f'1 {self.isHidden() = }, {self.isActiveWindow() = }')
        # if not self.isActiveWindow() and wintitle != phrases['block title']:
        #     self.hide()
        self.showNormal()
        self.showFullScreen()
        print(f'2 {self.isHidden() = }, {self.isActiveWindow() = }')

    def closeEvent(self, event):
        if blocked or lim_activated:
            event.ignore()
        else:
            self.hide()

    def blocksec(self):
        global blocked, lim_activated
        if (blocked and eye_save_type == 3) or (lim_activated and lim_off_type == 3):
            self.show()
        if not lim_activated:
            self.b_timer.setText(str(
                datetime.timedelta(seconds=int((eye_save_time_end - datetime.datetime.now()).total_seconds()))))
        else:
            self.label.setText('Ваше время истекло 👎')
            self.b_timer.setText('')
        # self.b_timer.update()
        if (eye_save_time_end - datetime.datetime.now()).total_seconds() < 1 or \
                not eye_save_enabled:  # Если время отдыха закончилось,
            blocked = False  # то закрывать
        if limited and sid < limit * 60 or not limited:
            lim_activated = False
        if not blocked and not lim_activated:
            self.hide()


class Statistic(QWidget):
    def __init__(self):
        super().__init__()
        log('Statistic __init__')
        self.setWindowTitle(phrases['stat title'])
        self.setWindowIcon(QIcon('icon.ico'))
        self.setWindowFlags(Qt.WindowType.CustomizeWindowHint | Qt.WindowType.WindowCloseButtonHint)

        self.adder = TimeAdder(self)

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
        self.add_time.clicked.connect(self.adder.show)

        self.layout.addWidget(self.stat_l)
        self.layout.addWidget(self.add_time)
        self.mainlay.addLayout(self.layout)
        self.setLayout(self.mainlay)
        self.stat_make()
        self.updater = QTimer()
        self.updater.timeout.connect(self.stat_upd)
        self.updater.setInterval(1000)

    def stat_make(self):
        print(f'{self.tabs.count() = }')
        while self.tabs.count() > 0:
            self.tabs.removeTab(0)
        # for tab in range(self.tabs.count()):
        #     self.tabs.removeTab(tab)
        for i in reversed(full_stat):
            # for key in full_stat[i]:
            #     text = QLabel()
            #     # print('eeeeeeee',key, full_stat[i][key])
            #     if full_stat[i][key] != 0 and key not in ['LockApp.exe', 'LockScr']:
            #         text.setText(self.stat_l.text() +
            #                         f'{key.replace(".exe", "")} - {datetime.timedelta(seconds=full_stat[i][key])}\n')
            self.make_tab(sort(full_stat[i]), i)
        self.mainlay.addWidget(self.tabs)
        print(f'{self.tabs.count() = }')

    def make_tab(self, d, name):
        text = QLabel('')
        text.setAlignment(Qt.AlignmentFlag.AlignLeft)
        summ = 0
        for key in d:
            if d[key] != 0 and key not in ['LockApp.exe', 'LockScr']:
                text.setText(text.text() +
                             f'{key.replace(".exe", "")} - {datetime.timedelta(seconds=d[key])}\n')
                summ += d[key]
        if text.text().replace(' ', '') != '':
            text.setText(text.text() + f'\nВсего: {datetime.timedelta(seconds=summ)}')
            self.tabs.addTab(text, name)

    def stat_upd(self):
        try:
            self.stat_l.setText('Сегодня:\n')
            for key in sort(stat):
                if stat[key] != 0 and key not in ['LockApp.exe', 'LockScr']:
                    self.stat_l.setText(self.stat_l.text() +
                                        f'{key.replace(".exe", "")} - {datetime.timedelta(seconds=stat[key])}\n')
            self.stat_l.setText(self.stat_l.text() + f'\nВсего: {datetime.timedelta(seconds=sid)}')
        except Exception as exc:
            print('failed to update stat:', exc)

    def closeEvent(self, event):  # Если удалить - при закрытии будет завершаться приложение
        event.ignore()
        self.hide()


class TimeAdder(QDialog):
    def __init__(self, parent):
        super(TimeAdder, self).__init__(parent)
        log('TimeAdder __init__')

        self.setWindowTitle(phrases['time adder title'])

        self.layout = QVBoxLayout()
        self.app_name = QLineEdit()
        self.app_name.setPlaceholderText(phrases['application'])

        self.time = QSpinBox()
        self.time.setRange(1, 1440)
        self.time.setSuffix(' мин.')

        self.dates = QComboBox()
        self.dates.setWhatsThis(phrases['whats datas?'])
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
        self.ok_b.clicked.connect(self.ok)
        self.cancel_b = QPushButton(phrases['cancel'])
        self.cancel_b.clicked.connect(self.reject)
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


def sort(dict_):
    sorted_dict = {}
    # sorted_keys = list(sorted(dict, key=dict.get))[::-1]
    sorted_keys = list(reversed(sorted(dict_, key=dict_.get)))

    for w in sorted_keys:
        sorted_dict[w] = dict_[w]
    return sorted_dict


def add_to_stat():
    global stat
    if thisapp in stat:
        stat[thisapp] += 1
    else:
        stat[thisapp] = 1


def sett_upd():
    global sett
    sett = {'one_sess': one_sess,
            'eye_save_type': eye_save_type,
            'eye_save_time': eye_save_time,
            'eye_save_time_end': str(eye_save_time_end),
            'eye_save_enabled': eye_save_enabled,
            'limited': limited,
            'limit': limit,
            'lim_off_type': lim_off_type,
            'theme': theme,
            'warn_before': warn_before}


def dataload():
    log('dataload')
    global sid, stat, start, delta_t, today, one_sess, eye_save_type, eye_save_time, sett, full_stat, stat_sids, \
        warn_before, eye_save_time_end, eye_save_enabled, limited, limit, lim_off_type, theme

    def readsett():
        global one_sess, eye_save_type, eye_save_time, eye_save_time_end, sett, sid, eye_save_enabled, limited, limit, \
            lim_off_type, theme, warn_before
        # sid = 0
        try:
            with open('sett.slset', 'r') as file:  # Настройки
                sett = dict(json.load(file))
                one_sess = sett['one_sess']
                eye_save_type = sett['eye_save_type']
                eye_save_time = sett['eye_save_time']
                eye_save_time_end = datetime.datetime.strptime(sett['eye_save_time_end'], '%Y-%m-%d %H:%M:%S')
                eye_save_enabled = sett['eye_save_enabled']
                limited = sett['limited']
                limit = sett['limit']
                lim_off_type = sett['lim_off_type']
                theme = sett['theme']
                warn_before = sett['warn_before']
                print('sett:', sett)
        except Exception as exc:
            print('Failed to read settings because', exc, ' trying to read as old settings')
            with open('sett.slset', 'r') as file:
                sett_l = list(csv.reader(file, delimiter=','))[0]
                one_sess = int(sett_l[0])
                eye_save_type = int(sett_l[1])
                eye_save_time = int(sett_l[2])
                eye_save_time_end = datetime.datetime.strptime(sett_l[3], '%Y-%m-%d %H:%M:%S')
                eye_save_enabled = to_bool(sett_l[4])
                limited = to_bool(sett_l[5])
                limit = int(sett_l[6])
                lim_off_type = int(sett_l[7])
                print(f'{sett = }')
                print('удалось загрузить старые настройки ')
            make_file('sett')

    def readallstat():
        global start, dirs, stat_sids
        try:
            chdir('Statistic')
        except FileNotFoundError:
            mkdir('Statistic')
            chdir('Statistic')
        dirs = [e for e in listdir() if path.isdir(e)]
        print(f'{dirs = }')
        if len(dirs) > 1:
            for d in dirs:
                full_stat[d] = {}
                stat_sids[d] = 0
                chdir(d)
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
                    chdir('..')
                except FileNotFoundError:
                    make_file('stat')
                    full_stat[d]['Sledilka.exe'] = 0
                    chdir('..')
        chdir('..')
        # for i in range(len(dirs)):
        #     dirs[i] =
    log('sett')
    try:
        readsett()
    except FileNotFoundError:
        log('except FileNotFoundError:')
        make_file('sett')
    except ValueError:
        log('ValueError')
        make_file('sett')
    except IndexError:
        log('IndexError')
        make_file('sett')
    finally:
        readsett()
    log('stat')
    try:
        readstat()
    except FileNotFoundError:
        log('except FileNotFoundError:')
        make_file('stat')
    except ValueError:
        log('ValueError')
        make_file('stat')
    except IndexError:
        log('IndexError')
        make_file('stat')
    finally:
        readstat()
        # try:
        readallstat()
    if limited:
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
    log(f'full_stat: {json.dumps(full_stat, indent=4)}')
    log(f'stat_sids: {json.dumps(stat_sids, indent=4)}')
    log('dataload.end\n')


def readstat():
    global sid, start
    sid = 0
    stat_exists = True
    try:
        chdir('Statistic')
    except FileNotFoundError:
        mkdir('Statistic')
        chdir('Statistic')
        stat_exists = False
    try:
        chdir(str(datetime.date.today()))
    except FileNotFoundError:
        mkdir(str(datetime.date.today()))
        chdir(str(datetime.date.today()))
        if stat_exists:
            start = datetime.date.today() - datetime.timedelta(days=1)
            print('noooooooooooot toaaaaaay')
    try:
        with open('stat.csv', 'r', newline='') as file:
            reader = csv.reader(file, delimiter=':')
            for row in reader:
                stat[row[0]] = int(row[1])
                sid += int(row[1])
    except FileNotFoundError:
        make_file('stat')
        print('mkfl')
    for _ in range(2):
        chdir('..')


def set_all_sids():
    global num_days
    log('set_all_sids')
    s = datetime.datetime.now()
    days = []
    for day in full_stat:   # добавляем даты
        days.append(datetime.datetime.strptime(day, '%Y-%m-%d').date())
    days.append(datetime.date.today())  # добавляем сегодня
    num_sid = {}
    num_days = {}
    min_day = min(days)
    for day in days:
        num_sid[(day - min_day).days] = stat_sids[str(day)]
        num_days[day] = (day - min_day).days
        print('to num_sid added',  (day - min_day).days, day)
    print(f'{num_sid = }')
    print(f'{num_days = }')
    print(f'{days = }')
    for day_ in num_sid:
        add_time(day_, num_sid[day_] // 60)
    skok_vozm()
    for e in range(len(pros)):
        print(f'{e} {pros[e]} {vozm[e]}')
    print(f'vozm: {json.dumps(dict(enumerate(vozm)), indent=4)}')
    # print(f'{pros = }\n{vozm = }')
    # print(get_key(num_sid, str(datetime.date.today())), '\n\n\n')
    # print(vozm[get_key(num_sid, str(datetime.date.today()))], '\n\n\n')
    print('setted all sids in', (datetime.datetime.now() - s).total_seconds(), 'sec\n')


def make_file(type_f='stat'):
    log('makefile')
    if type_f == 'stat':
        # last_stat_upd()
        with open('stat.csv', 'w') as file:
            writer = csv.writer(file, delimiter=':', lineterminator='\n')
            writer.writerow(['Sledilka.exe', 0])
    elif type_f == 'sett':
        sett_upd()
        with open('sett.slset', 'w') as file:
            json.dump(sett, file, ensure_ascii=False)


def make_shortcut(name, target, path_to_save, w_dir='default', icon='default'):
    log('make_shortcut')
    if path_to_save == 'desktop':
        '''Saving on desktop'''
        # Соединяем пути, с учётом разных операционок.
        path_to_save = path.join(winshell.desktop(), str(name) + '.lnk')
    elif path_to_save == 'startup':
        '''Adding to startup (windows)'''
        user = path.expanduser('~')
        path_to_save = path.join(r"%s/AppData/Roaming/Microsoft/Windows/Start Menu/Programs/Startup/" % user,
                                 str(name) + '.lnk')
    else:
        path_to_save = path.join(path_to_save, str(name) + '.lnk')
    if path.exists(path_to_save):
        do = False
    else:
        do = True
    if do:
        if icon == 'default':
            icon = target
        if w_dir == 'default':
            w_dir = path.dirname(target)
        # # С помощью метода Dispatch, обьявляем работу с Wscript
        # # (работа с ярлыками, реестром и прочей системной информацией в windows)
        shell = Dispatch('WScript.Shell')
        # Создаём ярлык.
        shortcut = shell.CreateShortCut(path_to_save)
        # Путь к файлу, к которому делаем ярлык.
        shortcut.Targetpath = target
        # Путь к рабочей папке.
        shortcut.WorkingDirectory = w_dir
        # Тырим иконку.
        shortcut.IconLocation = icon
        # Обязательное действо, сохраняем ярлык.
        shortcut.save()


def add_to_startup():
    try:
        if platform == 'win32':
            make_shortcut('Sledilka', path.abspath('Sledilka.exe'), 'startup')
        elif platform == 'linux':
            user = path.expanduser('~')
            with open(f'{user}/.config/autostart/Sledilka.desktop', 'w') as file:
                file.write('[Desktop Entry]\n'
                           'Type=Application\n'
                           f'Exec={getcwd()}/Sledilka\n'
                           f'Path={getcwd()}\n'
                           'Hidden=false\n'
                           'NoDisplay=false\n'
                           'X-GNOME-Autostart-enabled=true\n'
                           'Name[en_IN]=Sledilka\n'
                           'Name[ru_RU]=Следилка\n'
                           f'Name={phrases["app name"]}\n'
                           'Comment[en_IN]=\n'
                           'Comment=')
            print('Home path (user):', path.expanduser('~'))
    except Exception as exc:
        print('Adding to sturtup failed because', exc)


def datasave():
    log('datasave')
    global sid, start
    # last_stat_upd()
    sett_upd()
    print('sett1')
    with open('sett.slset', 'w') as file:  # Настройки
        print('opened')
        json.dump(sett, file, ensure_ascii=False)
        # writer = csv.writer(file, delimiter=',', lineterminator='\n')
        # writer.writerow(sett)
    print('sett2')
    statsave()


def statsave():
    try:
        chdir('Statistic')
    except FileNotFoundError:
        mkdir('Statistic')
        chdir('Statistic')
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
    for _ in range(2):
        chdir('..')


def daysave(day):
    day = str(day)
    try:
        chdir('Statistic')
    except FileNotFoundError:
        mkdir('Statistic')
        chdir('Statistic')
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
    for _ in range(2):
        chdir('..')


def startwin():
    global thisapp, wintitle
    with SharedMemoryManager() as smm:
        shared = smm.ShareableList(['a' * 70])
        p = Process(target=thiswin, args=(shared,), daemon=True)   # , name='anyyyyyyyy', daemon=True
        p.start()
        # freeze_support()
        while True:
            try:
                if shared != smm.ShareableList(['a' * 70]) and shared[0] != 'a' * 70:
                    try:
                        thisapp = shared[0]
                        # wintitle = shared[1]
                    except ValueError:
                        pass
            except ValueError:
                print('value Err from thread in startwin')
            sleep(0.5)


def thiswin(shared):
    from activewindow import getAppName  # , getTitle
    global thisapp, wintitle
    while True:
        thisapp = getAppName()['App2']
        if len(thisapp) > 50:
            thisapp = thisapp[0:49]
        # wintitle = getTitle()
        shared[0] = thisapp
        # shared[1] = wintitle


def pre_start():
    global today, delta_t, start, eye_save_time_end
    log('pre_start')
    print(f'до конца отдыха от мон: {(eye_save_time_end - datetime.datetime.now()).total_seconds()}')
    print(f'{sett["eye_save_time"] = }\n'
          f'{str(sett["eye_save_time_end"]) = }\n'
          f'{sett["one_sess"] = }\n'
          f'{blocked = }')
    if eye_save_time * 60 > (eye_save_time_end - datetime.datetime.now()).total_seconds() > 0 \
            and eye_save_enabled:
        print('prestart-eyesavesssssssssssssssssssssssssssssssssssssss')
        eye_save()
    elif eye_save_enabled and \
            eye_save_time * 60 < (eye_save_time_end - datetime.datetime.now()).total_seconds():
        print('prestart_seeeeeeeecondif')
        eye_save_time_end = datetime.datetime.now().replace(microsecond=0) \
            + datetime.timedelta(minutes=eye_save_time)
    print(f'eye_save_time_end after upd: {sett["eye_save_time_end"]}\n'
          f'{blocked = }')
    if limited and sid >= limit * 60:
        limit_out()

    Thread(target=startwin, daemon=True).start()
    try:
        add_to_startup()
    except Exception as exc:
        print('failed to sturtup:', exc)


def limit_out():
    log('limit_out')
    global eye_save_time, eye_save_time_end, lim_activated
    print(eye_save_time_end, eye_save_time)
    print(f'{sid = }, возможно: {vozm[num_days[datetime.date.today()]]}')

    def locker():
        global lim_activated
        log('locker')
        if lim_activated and limited and (sid > limit * 60 or sid >= vozm[num_days[datetime.date.today()]]):
            lock_comp()
            QTimer.singleShot(1000, locker)
        else:
            print('locker lim_activated - false')
            lim_activated = False

    lim_activated = True
    if lim_off_type == 0:
        log('sutdown')
        popen(f'shutdown -t 100 -s -c "{phrases["needs monitor rest"]}"')
    elif lim_off_type == 1:
        log('hiber')
        QTimer.singleShot(5000, hiber)
        notif(phrases['hiber'], phrases["needs monitor rest"])
    elif lim_off_type == 2:
        log('restart')
        popen(f'shutdown -t 10 -r -c "{phrases["needs monitor rest"]}"')
    elif lim_off_type == 3:
        log('block')
        QTimer.singleShot(1, block_s)
    elif lim_off_type == 4:
        log('lock_scr')
        locker()
    else:
        lim_activated = False


def eye_save():
    global eye_save_time, eye_save_time_end, blocked
    log('eye_save')
    print(blocked)
    print(eye_save_time_end, eye_save_time, eye_save_type)

    def locker():
        global blocked
        log('locker')
        if blocked and (eye_save_time_end - datetime.datetime.now()).total_seconds() > 0:
            lock_comp()
            QTimer.singleShot(100, locker)
        else:
            print('locker blocked - false')
            blocked = False

    blocked = True
    if eye_save_type == 0:
        log('sutdown')
        popen(f'shutdown -t 10 -s -c {phrases["needs monitor rest"]}')
    elif eye_save_type == 1:
        log('hiber')
        QTimer.singleShot(5000, hiber)
        notif(phrases['hiber'], phrases["needs monitor rest"])
    elif eye_save_type == 2:
        log('restart')
        popen(f'shutdown -t 10 -r -c {phrases["needs monitor rest"]}')
    elif eye_save_type == 3:
        log('block')
        QTimer.singleShot(1, block_s)
    elif eye_save_type == 4:
        log('lock_scr')
        locker()
    else:
        blocked = False


def hiber():
    if platform == 'win32':
        print(popen('shutdown -h').read())
    elif platform == 'linux':
        pass


def block_s():
    print('block_s')
    window.show_block()


def lock_comp():
    if platform == 'win32':
        user = windll.LoadLibrary('user32.dll')
        user.LockWorkStation()
    elif platform == 'linux':
        popen('loginctl lock-session')


def log(text):
    print(text)
    log_wr = open('logs.txt', 'a')
    log_wr.write(f'{text}\n')


def add_clip():
    global app
    if app.clipboard() is not None:
        app.clipboard().setText(str(datetime.timedelta(seconds=sid)))


def to_bool(_str):
    if _str == 'True':
        return True
    else:
        return False


def notif(title, msg, sec=2):
    window.tray_icon.showMessage(str(title), str(msg), app_icon, sec*1000)


def notifications():
    global today, delta_t, start
    today = datetime.date.today()
    delta_t = today - start
    if delta_t.days > 0:
        log(f'if delta_t.days ({delta_t.days}) > 0: ')
        for i in dirs:
            print(f'from dirs {i = }')
            if i == str(datetime.date.today()):
                dirs.remove(i)
                print(f'from dirs deleted {i}')
        past_sid = 0
        past_day = max(dirs)
        print(f'{past_day = }')
        for key in full_stat[past_day]:
            past_sid += full_stat[past_day][key]
            print(f'added: {full_stat[past_day][key]}')
        print(f'{past_sid = }\n{too_little_time = }')
        if past_sid < too_little_time:
            print('too low')
            notif("Информация", "В прошлый раз вы подозрительно мало сидели за компьютером", 3)
        else:
            notif("Информация", f"Время проведённое за компьютером в прошлый раз: "
                                f"{datetime.timedelta(seconds=past_sid)}", 3)
        datasave()
        start = datetime.date.today()
        delta_t = today - start


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


def skok_vozm():
    global vozm
    vozm = []
    for a in range(len(pros)+1):
        vozm.append(limit)
    for i in range(len(pros)):
        if pros[i] > vozm[i]:   # Если просижено больше, чем можно, то
            vozm[i+1] -= pros[i] - vozm[i]  # На следующий день отнимается перебор
    # i = 0
    # while vozm[-1] >= 0:
    #     if vozm[i] < 0:
    #         vozm[i+1] += vozm[i]
    #         vozm[i] = 0
    #     i += 1
    for i in range(len(vozm)):
        if vozm[i] < 0 and vozm.index(vozm[-1]) == vozm.index(vozm[i]):  # Если текущий элемент отр и он последний то:
            while not vozm[-1] >= 0:     # Пока последний элемент меньше нуля:
                vozm.append(limit)
                vozm[-1] += vozm[-2]
                vozm[-2] = 0
        elif vozm[i] < 0 and vozm.index(vozm[-1]) != vozm.index(vozm[i]):
            vozm[i+1] += vozm[i]
            vozm[i] = 0
    # for e in vozm:
    #     if e < 0:
    #         print('in skok_vozm() element < 0')
    #         skok_vozm()
    #         break


if __name__ == '__main__':
    dataload()
    app = QApplication(argv)
    app_icon = QIcon('icon.ico')
    app.setWindowIcon(app_icon)
    pre_start()
    window = Timer()
    notifications()
    app.exec()
