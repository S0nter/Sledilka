import csv
import datetime
from os import listdir, chdir, mkdir, path, popen
from sys import argv, platform as pt
from time import sleep
from multiprocessing import Process
from multiprocessing.managers import SharedMemoryManager
from threading import Thread
from tkinter import messagebox as msg
from keyboard import press_and_release
from PyQt6.QtCore import QSize, Qt, QEvent, QTimer
from PyQt6.QtGui import QPainter, QIcon, QAction, QFont
from PyQt6.QtWidgets import QApplication, QSystemTrayIcon, QWidget, QMenu, QLabel, QVBoxLayout, QSpinBox,\
    QSizePolicy, \
    QLayout, QGroupBox, QComboBox, QHBoxLayout, QTabWidget, QPushButton

platform = pt
if platform == 'win32':
    from ctypes import windll
    import winshell
    from win32com.client import Dispatch

limited = False
limit = 0  # Возможное колличество времени за день (мин)
lim_off_type = 0  # Тип выкла (выкл, гибернация, перезагрузка, заблок экран, экран блок)
# lim_end = datetime.datetime.now().replace(microsecond=0)  # Конец лимит (не нужен, т. к. будет определяться через sid)
lim_activated = False
sid = 0  # Время за компом (сек)
sid_sess = 0  # Время текущей сессии (сек)
stat = {}  # Сегодняшняя статистика
full_stat = {str(datetime.date.today()): {}}  # Статистика вся, кроме сегодня

eye_save_enabled = False
one_sess = 0  # Длительность сессии (до выключения, минут) (если ноль - отключено)
eye_save_type = 0  # Тип выключения компа
eye_save_time = 1  # Длительность отдыха от монитора (минут)
eye_save_time_end = datetime.datetime.now().replace(microsecond=0)  # Конец отдыха от монитора
# eye_save_time_end = datetime.datetime.strptime(
#     datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'), '%Y-%m-%d %H:%M:%S')
blocked = False
start = datetime.date.today()
today = datetime.date.today()
delta_t = start - today
sett = []
thisapp = 'Sledilka.exe'
wintitle = ''
saved = False
loaded = True
dirs = []
txt_OK = 'OK'
txt_cancel = 'Отмена'
txt_apply = 'Применить'
too_little_time = 1
phrases = {
    'shutdown': 'Выключить компьютер',
    'restart': 'Перезагрузка',
    'hiber': 'Гибернация',
    'to lock scr': 'Заблокировать экран',
    'lock scr': 'Экран блокировки',
    'block title': 'Следилка - Блокировщик ТЕБЯ'
}


class Timer(QWidget):

    def __init__(self):
        log('Timer __init__')
        super().__init__()
        self.setFixedSize(QSize(145, 110))
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint)
        self.setWindowTitle("Следилка")
        self.setWindowIcon(QIcon('icon.ico'))

        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.offset = None
        self.in_tray = False
        self.installEventFilter(self)
        self.time_show = QLabel(str(datetime.timedelta(seconds=sid)))
        self.time_show.setAlignment(Qt.AlignmentFlag.AlignCenter)

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
        # event.ignore()
        self.hide()

    def paintEvent(self, ev):  # Создание окна
        if sid > 36000:
            self.setFixedSize(165, 120)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.renderHints(painter).Antialiasing)  # Убирание некрасивых краёв PyQt6
        # painter.setRenderHint(QPainter.Antialiasing)                                                   # PySide6
        painter.setBrush(Qt.GlobalColor.white)
        painter.drawRoundedRect(self.rect(), 25, 25)  # Закругление краёв

    def eventFilter(self, source, event):  # Перетаскивание окна
        if event.type() == QEvent.Type.MouseButtonPress and event.button() == Qt.MouseButton.LeftButton:
            # self.offset = event.position()      # PySide6
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
        font = self.time_show.font()
        font.setPointSize(30)
        self.time_show.setFont(font)
        self.time_show.setAlignment(Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignVCenter)
        self.stat.updater.start()
        self.timer.start()
        self.checker_timer.start()

    def checker(self):
        global sid, sid_sess, eye_save_time_end, start, saved, loaded, stat, thisapp, wintitle
        # thisapp = win_info[0]
        # wintitle = win_info[1]
        if thisapp not in ['LockApp.exe', 'LockScr'] and not blocked and not lim_activated:
            if not loaded:
                Thread(target=dataload).start()
                loaded = True
            saved = False
            if self.isHidden() and not self.in_tray:
                self.show()
            # ???
            Thread(target=add_to_stat).start()
            # ???
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
            else:  # Иначе:
                if self.it == 60:  # Сейвы каждую минуту
                    Thread(target=datasave).start()
                    self.it = 0
            if limited and sid >= limit * 60:
                limit_out()
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

    def runtimesec(self):
        global sid, sid_sess
        # print(f'{thisapp = }, {blocked = }')
        if thisapp not in ['LockApp.exe', 'LockScr'] and not blocked and not lim_activated:
            self.time_show.setText(str(datetime.timedelta(seconds=sid + 1)))
            sid += 1
            sid_sess += 1

    def runtimesec_old(self):
        global sid, sid_sess, eye_save_time_end, start, saved, loaded, stat
        if thisapp not in ['LockApp.exe', 'LockScr'] and not blocked:
            if not loaded:
                Thread(target=dataload).start()
                loaded = True
            saved = False
            if self.isHidden() and not self.in_tray:
                self.show()
            self.time_show.setText(str(datetime.timedelta(seconds=sid + 1)))
            sid += 1
            sid_sess += 1
            self.it += 1
            Thread(target=add_to_stat).start()
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
            else:  # Иначе:
                if self.it == 60:  # Сейвы каждую минуту
                    Thread(target=datasave).start()
                    self.it = 0
        elif blocked:
            self.hide()
        elif not saved and thisapp not in ['LockApp.exe', 'LockScr']:
            Thread(target=datasave).start()
            saved = True
        if datetime.date.today() != start:
            start = datetime.date.today()
            sid = 0
            full_stat[start] = stat
            stat = {'Sledilka.exe': 0}

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
        global one_sess
        log('Settings __init__')
        self.setWindowTitle("Настройки")
        self.setWindowIcon(QIcon('icon.ico'))
        self.setWindowFlags(Qt.WindowType.CustomizeWindowHint | Qt.WindowType.WindowCloseButtonHint)

        self.layout = QVBoxLayout()
        self.layout.setSizeConstraint(QLayout.SizeConstraint.SetFixedSize)

        self._set_eye_save()
        self._set_limits()

        self.updateInterface()
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
        global one_sess
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

    def _set_buttons(self):
        self.butt_lay = QHBoxLayout()
        self.butt_lay.setAlignment(Qt.AlignmentFlag.AlignRight)

        self.butt_ok = QPushButton()
        self.butt_ok.setText(txt_OK)
        self.butt_ok.clicked.connect(self.sett_save)
        self.butt_ok.clicked.connect(self.close)
        self.butt_ok.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        self.butt_lay.addWidget(self.butt_ok)

        self.butt_cancel = QPushButton()
        self.butt_cancel.setText(txt_cancel)
        self.butt_cancel.clicked.connect(self.close)
        self.butt_cancel.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        self.butt_lay.addWidget(self.butt_cancel)

        self.butt_apply = QPushButton()
        self.butt_apply.setText(txt_apply)
        self.butt_apply.clicked.connect(self.sett_save)
        self.butt_apply.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        self.butt_lay.addWidget(self.butt_apply)

        self.layout.addLayout(self.butt_lay)

    def sett_save(self):
        global one_sess, eye_save_type, eye_save_time, eye_save_time_end, eye_save_enabled, limited, lim_off_type, limit
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
        print(f'{limited = }, {self.s_lim_end_list.currentText() = } - {lim_off_type = }, {limit = }')
        print(f'{eye_save_enabled = }')
        datasave()

    def updateInterface(self):
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

    def showEvent(self, event):
        self.updateInterface()


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
        press_and_release('Esc')
        print(f'1 {self.isHidden() = }, {self.isActiveWindow() = }')
        # if not self.isActiveWindow() and wintitle != phrases['block title']:
        #     self.hide()
        self.showNormal()
        self.showFullScreen()
        print(f'2 {self.isHidden() = }, {self.isActiveWindow() = }')

    def closeEvent(self, event):
        if blocked or lim_activated:
            event.ignore()

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
        self.setWindowTitle("Статистика")
        self.setWindowIcon(QIcon('icon.ico'))
        self.setWindowFlags(Qt.WindowType.CustomizeWindowHint | Qt.WindowType.WindowCloseButtonHint)

        # self.mainlay = QVBoxLayout()
        self.layout = QHBoxLayout()

        self.tabs = QTabWidget()
        self.tabs.setDocumentMode(True)
        self.tabs.setMovable(True)

        self.stat_l = QLabel()
        self.stat_l.setAlignment(Qt.AlignmentFlag.AlignLeft)
        self.layout.addWidget(self.stat_l)
        self.setLayout(self.layout)
        self.stat_make()
        self.updater = QTimer()
        self.updater.timeout.connect(self.stat_upd)
        self.updater.setInterval(1000)

    def stat_make(self):
        for i in reversed(full_stat):
            # for key in full_stat[i]:
            #     text = QLabel()
            #     # print('eeeeeeee',key, full_stat[i][key])
            #     if full_stat[i][key] != 0 and key not in ['LockApp.exe', 'LockScr']:
            #         text.setText(self.stat_l.text() +
            #                         f'{key.replace(".exe", "")} - {datetime.timedelta(seconds=full_stat[i][key])}\n')
            self.make_tab(sort(full_stat[i]), i)
        self.layout.addWidget(self.tabs)

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
        # if not self.isHidden():
        # readstat()
        self.stat_l.setText('Сегодня:\n')
        for key in sort(stat):
            if stat[key] != 0 and key not in ['LockApp.exe', 'LockScr']:
                self.stat_l.setText(self.stat_l.text() +
                                    f'{key.replace(".exe", "")} - {datetime.timedelta(seconds=stat[key])}\n')
        self.stat_l.setText(self.stat_l.text() + f'\nВсего: {datetime.timedelta(seconds=sid)}')
        # QTimer.singleShot(1000, self.stat_upd)

    # def showEvent(self, event):
    #     readstat()


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
    sett = [one_sess, eye_save_type, eye_save_time, str(eye_save_time_end), eye_save_enabled, limited, limit,
            lim_off_type]


def dataload():
    log('dataload')
    global sid, stat, start, delta_t, today, one_sess, eye_save_type, eye_save_time, sett, full_stat

    def readsett():
        global one_sess, eye_save_type, eye_save_time, eye_save_time_end, sett, sid, eye_save_enabled, limited, limit, \
            lim_off_type
        # sid = 0
        with open('sett.slset', 'r') as file:  # Настройки
            sett = list(csv.reader(file, delimiter=','))[0]
            print(f'{sett = }')
            one_sess = int(sett[0])
            eye_save_type = int(sett[1])
            eye_save_time = int(sett[2])
            eye_save_time_end = datetime.datetime.strptime(sett[3], '%Y-%m-%d %H:%M:%S')
            # try:
            eye_save_enabled = to_bool(sett[4])
            limited = to_bool(sett[5])
            limit = int(sett[6])
            lim_off_type = int(sett[7])
            print('удалось загрузить новые настройки ')
            # except Exception:
            #     print('не удалось новые настройки загрузить')
            print(f'{eye_save_enabled = }')
            # for ind in range(len(reader)):
            #     reader[ind] = int(reader[ind])

    # def readsett_old():
    #     global one_sess, eye_save_type, eye_save_time, eye_save_time_end, sett
    #     sett = []
    #     with open('sett.slset', 'r', newline='') as f_s:  # Загрузка настроек
    #         s_reader = csv.reader(f_s)
    #         for s_row in s_reader:
    #             one_sess = int(s_row[0])
    #             eye_save_type = int(s_row[1])
    #             eye_save_time = int(s_row[2])
    #             eye_save_time_end = datetime.datetime.strptime(s_row[3], '%Y-%m-%d %H:%M:%S')
    #         f_s.close()
    #     sett_upd()

    def readallstat():
        global start, dirs
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
                chdir(d)
                try:
                    with open('stat.csv', 'r', newline='') as file:
                        reader = csv.reader(file, delimiter=':')
                        for row in reader:
                            # print('rrrrrrrrrrrrrrrrrrrrrr', row[0])
                            if row[0] not in ['LockApp.exe']:
                                full_stat[d][row[0]] = int(row[1])
                    if d == str(datetime.date.today()):
                        full_stat[str(datetime.date.today())] = stat
                        del full_stat[str(datetime.date.today())]
                    chdir('..')
                except FileNotFoundError:
                    make_file('stat')
                    full_stat[d]['sledilka.exe'] = 0
                    chdir('..')
        chdir('..')
        # for i in range(len(dirs)):
        #     dirs[i] =

    # def readstat_old():
    #     global stat, start, sid
    #     stat = []
    #     with open('stat.csv', 'r', newline='') as f:  # Загрузка статистики
    #         reader = csv.reader(f)
    #         for row in reader:
    #             start = datetime.datetime.strptime(row[0], '%Y-%m-%d').date()
    #             sid = int(row[1])
    #             stat.append(row)
    #     f.close()
    #     last_stat_upd()

    log('sett')
    try:
        readsett()
    except FileNotFoundError:
        log('except FileNotFoundError:')
        make_file('s')
    except ValueError:
        log('ValueError')
        make_file('s')
    except IndexError:
        log('IndexError')
        make_file('s')
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


def make_file(type_f='stat'):
    log('makefile')
    if type_f == 'stat':
        # last_stat_upd()
        with open('stat.csv', 'w') as file:
            writer = csv.writer(file, delimiter=':', lineterminator='\n')
            writer.writerow(['sledilka.exe', 0])

    else:
        sett_upd()
        with open('sett.slset', 'w', newline='') as file:
            writer = csv.writer(file, delimiter=',', lineterminator='\n')
            writer.writerow(sett)
    file.close()


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


def datasave():
    log('datasave')
    global sid, start
    # save_file = open('statS.csv', 'a')
    # saver = csv.writer(save_file, delimiter=',', lineterminator='\n')
    # saver.writerows(stat)
    # saver.writerow(['\n'])
    # save_file.close()
    # save_file = open('settS.slset', 'a')
    # sett_saver = csv.writer(save_file, delimiter=',', lineterminator='\n')
    # sett_saver.writerow(sett)
    # sett_saver.writerow(['\n'])
    # save_file.close()
    # last_stat_upd()
    sett_upd()
    with open('sett.slset', 'w') as file:  # Настройки
        writer = csv.writer(file, delimiter=',', lineterminator='\n')
        writer.writerow(sett)
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

    # def old():
    #     if len(stat) > 0 and delta_t.days > 0:  # Статистика
    #         ''' Если заход в прогу был не сегодня: '''
    #         print(f'delta_t: {delta_t}\nstart: {start}\ntoday: {today}')
    #         log('if len(stat) > 0 and delta_t.days > 0:')
    #         log(f'{len(stat)} {delta_t.days}')
    #         sid = 0
    #         stat.append(last_stat)
    #     else:
    #         log('else:        stat[-1] = last_stat')
    #         log(f'len(stat) = {len(stat)}, delta_t.days = {delta_t.days}')
    #         stat[-1] = last_stat
    #     with open('stat.csv', 'w') as file:
    #         writer = csv.writer(file, delimiter=',', lineterminator='\n')
    #         if delta_t.days > 0:
    #             if not len(stat) > 1:
    #                 '''Если сегодня старта проги не было и кол-во строк в документе не превышает одну:'''
    #                 log('if delta_t.days > 0 and not len(stat) > 1:')
    #                 writer.writerow(stat[-1])
    #                 writer.writerow(last_stat)
    #                 stat.append(last_stat)
    #             else:
    #                 '''Если сегодня старта проги не было и кол-во строк в документе превышает одну:'''
    #                 log('elif delta_t.days > 0 and len(stat) > 1:')
    #                 writer.writerows(stat[:-1])
    #                 log(f'writer.writerows({stat[:-2]})')
    #                 writer.writerow(last_stat)
    #                 stat[-1] = last_stat
    #         else:
    #             if not len(stat) > 1:
    #                 '''Если сегодня старт проги был и кол-во строк в документе не превышает одну:'''
    #                 log('elif not (delta_t.days > 0) and not len(stat) > 1:')
    #                 writer.writerow(stat[-1])
    #                 stat[-1] = last_stat
    #             else:
    #                 '''Если сегодня старт проги был и кол-во строк в документе превышает одну:'''
    #                 log('elif not (delta_t.days > 0) and len(stat) > 1:')
    #                 writer.writerows(stat[:-1])
    #                 writer.writerow(last_stat)
    #                 stat[-1] = last_stat
    #     file.close()
    #     log(f'stat: {stat}')
    #     sett_upd()
    #     log(f'sett saved: {sett}')
    #     log('datasave.end')


def startwin():
    global thisapp, wintitle
    # def adds():
    #     time.sleep(1)
    #     add_to_stat()
    #     statsave()
    #     # print(stat)
    #     threading.Thread(target=adds).start()
    #
    # readstat()
    # print(f'readstated: {stat}')
    # threading.Thread(target=adds).start()
    with SharedMemoryManager() as smm:
        shared = smm.ShareableList(['a' * 200, 'a' * 200])
        p = Process(target=thiswin, args=(shared,), daemon=True)   # , name='anyyyyyyyy', daemon=True
        p.start()
        # freeze_support()
        while True:
            if shared != smm.ShareableList(['a' * 200, 'a' * 200]) and \
                    shared[0] != 'a' * 200 and shared[1] != 'a' * 200:
                try:
                    thisapp = shared[0]
                    wintitle = shared[1]
                except ValueError:
                    pass
            sleep(0.5)


def thiswin(shared):
    from activewindow import getInfo, getTitle
    global thisapp, wintitle
    while True:
        thisapp = getInfo()['App2']
        wintitle = getTitle()
        shared[0] = thisapp
        shared[1] = wintitle
    # threading.Timer(1, thiswin).start()
    # info = a.getInfo()
    # thisapp = info['App2']
    # wintitle = info['Title']
    # # print(thisapp, wintitle)
    # threading.Timer(1, thiswin).start()

    # lst = SharedMemoryManager().ShareableList([thisapp, wintitle])
    # lst[0] = thisapp
    # lst[1] = wintitle
    # # queue.put({'thisapp': thisapp, 'wintitle': wintitle})
    # # conn.send({'thisapp': thisapp, 'wintitle': wintitle})
    # # Process(target=thiswin, args=(conn,)).start()
    # # return {'thisapp': thisapp, 'wintitle': wintitle}
    # # thiswin()


def pre_start():
    global today, delta_t, start, eye_save_time_end
    log('pre_start')
    print(f'до конца отдыха от мон: {(eye_save_time_end - datetime.datetime.now()).total_seconds()}')
    print(f'{eye_save_time = }\n'
          f'{str(eye_save_time_end) = }\n'
          f'{one_sess = }\n'
          f'{blocked = }')
    if eye_save_time * 60 > (eye_save_time_end - datetime.datetime.now()).total_seconds() > 0 and eye_save_enabled:
        print('prestart-eyesavesssssssssssssssssssssssssssssssssssssss')
        eye_save()
    elif eye_save_enabled and eye_save_time * 60 < (eye_save_time_end - datetime.datetime.now()).total_seconds():
        print('prestart_seeeeeeeecondif')
        eye_save_time_end = datetime.datetime.now().replace(microsecond=0) + datetime.timedelta(minutes=eye_save_time)
    print(f'eye_save_time_end after upd: {eye_save_time_end}\n'
          f'{blocked = }')
    if limited and sid >= limit * 60:
        limit_out()

    Thread(target=startwin, daemon=True).start()

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
        if past_sid < too_little_time:
            Process(target=msg.showinfo, args=("Информация",
                                               "В прошлый раз вы подозрительно мало "
                                               "сидели за компьютером")).start()
        else:
            Process(target=msg.showinfo, args=("Информация",
                                               f"Время проведённое за компьютером в прошлый раз: "
                                               f"{datetime.timedelta(seconds=past_sid)}")).start()
        datasave()
        start = datetime.date.today()
        delta_t = today - start
    make_shortcut('Sledilka', path.abspath('Sledilka.exe'), 'startup')


def limit_out():
    log('limit_out')
    global eye_save_time, eye_save_time_end, lim_activated
    print(eye_save_time_end, eye_save_time)

    def hiber():
        popen('shutdown -h')

    def block_s():
        print('block_s')
        window.show_block()

    def locker():
        global lim_activated
        log('locker')
        if lim_activated and limited and sid > limit:
            user = windll.LoadLibrary('user32.dll')
            user.LockWorkStation()
            QTimer.singleShot(2000, locker)
        else:
            print('locker lim_activated - false')
            lim_activated = False

    lim_activated = True
    if lim_off_type == 0:
        log('sutdown')
        popen('shutdown -t 10 -s -c "Требуется отдых от монитора"')
    elif lim_off_type == 1:
        log('hiber')
        QTimer.singleShot(5000, hiber)
        msg.showinfo(phrases['hiber'], 'Требуется отдых от монитора')
    elif lim_off_type == 2:
        log('restart')
        popen('shutdown -t 10 -r -c "Требуется отдых от монитора"')
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
    print(eye_save_time_end, eye_save_time)

    def hiber():
        popen('shutdown -h')

    def block_s():
        print('block_s')
        window.show_block()

    def locker():
        global blocked
        log('locker')
        if blocked and (eye_save_time_end - datetime.datetime.now()).total_seconds() > 0:
            user = windll.LoadLibrary('user32.dll')
            user.LockWorkStation()
            QTimer.singleShot(100, locker)
        else:
            print('locker blocked - false')
            blocked = False

    blocked = True
    if eye_save_type == 0:
        log('sutdown')
        popen('shutdown -t 10 -s -c "Требуется отдых от монитора"')
    elif eye_save_type == 1:
        log('hiber')
        QTimer.singleShot(5000, hiber)
        msg.showinfo(phrases['hiber'], 'Требуется отдых от монитора')
    elif eye_save_type == 2:
        log('restart')
        popen('shutdown -t 10 -r -c "Требуется отдых от монитора"')
    elif eye_save_type == 3:
        log('block')
        QTimer.singleShot(1, block_s)
    elif eye_save_type == 4:
        log('lock_scr')
        locker()
    else:
        blocked = False


def log(text):
    print(text)
    log_wr = open('logs.txt', 'a')
    log_wr.write(f'{text}\n')


def add_clip():
    global app
    if app.clipboard() is not None:
        app.clipboard().setText(str(sid))


def to_bool(_str):
    if _str == 'True':
        return True
    else:
        return False


if __name__ == '__main__':
    # freeze_support()
    dataload()
    pre_start()
    app = QApplication(argv)
    app.setWindowIcon(QIcon('icon.ico'))
    window = Timer()
    app.exec()
