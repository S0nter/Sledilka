import csv
import json
import ctypes
import datetime
import os
import sys
import threading
from ctypes import windll, wintypes
from tkinter import messagebox as msg
import keyboard
import psutil
import winshell
from PyQt6.QtCore import QSize, Qt, QEvent, QTimer
from PyQt6.QtGui import QPainter, QIcon, QAction, QFont
from PyQt6.QtWidgets import QApplication, QSystemTrayIcon, QWidget, QMenu, QLabel, QVBoxLayout, QSpinBox, QSizePolicy, \
    QLayout, QGroupBox, QComboBox, QHBoxLayout, QTabWidget
from win32com.client import Dispatch

sid = 0  # Время за компом (сек)
sid_sess = 0  # Время текущей сессии (сек)
it = 0  # Итерации
stat = {}   # Сегодняшняя статистика
full_stat = {str(datetime.date.today()): {}}   # Статистика вся, кроме сегодня
one_sess = 0  # Длительность сессии (до выключения, минут)
eye_save_type = 0  # Тип выключения компа
eye_save_time = 1  # Длительность отдыха от монитора
eye_save_time_end = datetime.datetime.strptime(
    datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'), '%Y-%m-%d %H:%M:%S')  # Конец отдыха от монитора
blocked = False
start = datetime.date.today()
today = datetime.date.today()
delta_t = start - today
load_iter = 0
sett = []
thiswin = ''
saved = False
loaded = True


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

        self.timer = QTimer()
        self.timer.timeout.connect(self.runtimesec)

        self.runtime()

    def _actions(self):
        self.copy = QAction('Копировать', self)
        self.copy.triggered.connect(self.sid_add)
        # self.copy.triggered.connect()

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
        self.in_tray = True

    def paintEvent(self, ev):  # Создание окна
        if sid > 36000:
            self.setFixedSize(165, 120)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.renderHints(painter).Antialiasing)  # Убирание некрасивых краёв
        painter.setBrush(Qt.GlobalColor.white)
        painter.drawRoundedRect(self.rect(), 25, 25)  # Закругление краёв

    def eventFilter(self, source, event):  # Перетаскивание окна
        if event.type() == QEvent.Type.MouseButtonPress and event.button() == Qt.MouseButton.LeftButton:
            self.offset = event.pos()
        elif event.type() == QEvent.Type.MouseMove and self.offset is not None:
            self.move(self.pos() - self.offset + event.pos())
            return True
        elif event.type() == QEvent.Type.MouseButtonRelease:
            self.offset = None
        return super().eventFilter(source, event)

    def contextMenuEvent(self, e):  # Контекстное меню
        # print(e)
        self.context.exec(self.mapToGlobal(e.pos()))
        # log('contextMenuEvent')
        # context = QMenu(self)
        # copy_act = context.addAction(self.copy)
        # # copy_act.setShortcut(QKeySequence.StandardKey.Copy)
        # context.addSeparator()
        # stat_act = context.addAction("Статистика")
        # sett_act = context.addAction("Настройки")
        # context.addSeparator()
        # quit_act = context.addAction("Скрыть")
        # action = context.exec(self.mapToGlobal(e.pos()))
        #
        # if action == copy_act:
        #     log('ПКМ -> Копировать')
        #     log(datetime.timedelta(seconds=sid))
        #     add_clip(str(datetime.timedelta(seconds=sid)))
        #     # threading.Thread(target=add_clip, args=(str(sid)))
        # elif action == stat_act:
        #     log('ПКМ -> Статистика')
        #     print(stat)
        #     self.stat.show()
        # elif action == sett_act:
        #     log('ПКМ -> Настройки')
        #     self.sett_w.show()
        # elif action == quit_act:
        #     log('ПКМ -> Quit')
        #     datasave()
        #     self.hide()
        #     self.in_tray = True

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

        self.timer.start(1000)

    def runtimesec(self):
        global sid, sid_sess, it, eye_save_time_end, start, saved, loaded, stat
        if thiswin != 'Win_lock_scr_real' and not blocked:
            if not loaded:
                threading.Thread(target=dataload).start()
                loaded = True
            saved = False
            if self.isHidden() and not self.in_tray:
                self.show()
            self.time_show.setText(str(datetime.timedelta(seconds=sid)))
            self.time_show.update()
            sid += 1
            sid_sess += 1
            it += 1
            threading.Thread(target=add_to_stat).start()
            if sid_sess == one_sess * 60 and one_sess > 0:  # Если время сессии подошло к концу, то:
                log('end os sess')
                print('eeeeeeeeeeeeeeeeeeeendofsess')
                sid_sess = 0
                eye_save_time_end = datetime.datetime.strptime(
                    datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'), '%Y-%m-%d %H:%M:%S') + \
                    datetime.timedelta(minutes=eye_save_time)
                threading.Thread(target=datasave).start()
                eye_save()
            elif sid_sess > one_sess * 60:
                sid_sess = 0
            else:  # Иначе:
                if it == 60:  # Сейвы каждую минуту
                    threading.Thread(target=datasave).start()
                    it = 0
        elif blocked:
            self.hide()
        elif not saved and thiswin == 'Win_lock_scr_real':
            threading.Thread(target=datasave).start()
            saved = True
        if datetime.date.today() != start:
            start = datetime.date.today()
            sid = 0
            full_stat[start] = stat
            stat = {'Sledilka.exe': 0}

    def show_block(self):
        if blocked:
            self.blk.hide()
            self.blk.showNormal()
            self.blk.showFullScreen()


class Settings(QWidget):
    def __init__(self):
        super().__init__()
        global one_sess
        log('Settings __init__')
        self.setWindowTitle("Настройки")
        self.setWindowIcon(QIcon('icon.ico'))
        self.setWindowFlags(Qt.WindowType.CustomizeWindowHint | Qt.WindowType.WindowCloseButtonHint)

        self.s_one_sess_gr = QGroupBox('Отдых от монитора')  # Отдых от монитора:
        self.s_one_sess_gr.setCheckable(True)

        self.s_eye_sess = QLabel('Длительность сеанса')
        self.s_eye = QSpinBox()
        self.s_eye.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        self.s_eye.setRange(1, 1440)

        if one_sess > 0:
            self.s_eye.setValue(one_sess)
        else:
            self.s_one_sess_gr.setChecked(False)
            self.s_eye.setValue(1)
        self.s_eye.setSuffix(' мин.')

        self.s_eye_lay = QHBoxLayout()
        self.s_eye_lay.setAlignment(Qt.AlignmentFlag.AlignLeft)
        self.s_eye_lay.addWidget(self.s_eye_sess)
        self.s_eye_lay.addWidget(self.s_eye)
        self.s_eye_lay.setSizeConstraint(QLayout.SizeConstraint.SetFixedSize)

        self.s_eye_sess_end_label = QLabel('При окончании сеанса:')

        self.s_eye_sess_end_list = QComboBox()
        self.s_eye_sess_end_list.addItem('Выключить компьютер')
        self.s_eye_sess_end_list.addItem('Гибернация')
        self.s_eye_sess_end_list.addItem('Перезагрузка')
        self.s_eye_sess_end_list.addItem('Заблокировать экран')
        self.s_eye_sess_end_list.addItem('Экран блокировки')

        if eye_save_type == 0:  # Определение типа выкла
            self.s_eye_sess_end_list.setCurrentText('Выключить компьютер')
        elif eye_save_type == 1:
            self.s_eye_sess_end_list.setCurrentText('Гибернация')
        elif eye_save_type == 2:
            self.s_eye_sess_end_list.setCurrentText('Перезагрузка')
        elif eye_save_type == 3:
            self.s_eye_sess_end_list.setCurrentText('Заблокировать экран')
        elif eye_save_type == 4:
            self.s_eye_sess_end_list.setCurrentText('Экран блокировки')

        self.s_eye_sess_end_lay = QHBoxLayout()
        self.s_eye_sess_end_lay.addWidget(self.s_eye_sess_end_label)
        self.s_eye_sess_end_lay.addWidget(self.s_eye_sess_end_list)

        self.s_eye_rest_label = QLabel('Требовать отдыха от монитора на')
        self.s_eye_rest_spin = QSpinBox()
        self.s_eye_rest_spin.setRange(1, 1440)
        self.s_eye_rest_spin.setValue(eye_save_time)
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

        # if one_sess > 0:
        #     self.s_one_sess_gr.setChecked(True)
        #     self.s_eye.setValue(one_sess)
        # else:
        #     self.s_eye_sess.setDisabled(True)
        #     self.s_eye.setDisabled(True)
        layout = QVBoxLayout()
        layout.setSizeConstraint(QLayout.SizeConstraint.SetFixedSize)
        layout.addWidget(self.s_one_sess_gr)

        self.setLayout(layout)

    # def set_s_eye_type(self):
    # if self.s_one_sess_ch.isChecked():
    #     self.s_eye_sess.setEnabled(True)
    #     self.s_eye.setEnabled(True)
    # else:
    #     self.s_eye_sess.setEnabled(False)
    #     self.s_eye.setEnabled(False)

    def closeEvent(self, event):
        global one_sess, eye_save_type, eye_save_time
        # log(self.s_eye_sess_end_list.currentText())
        print(f'closesett, sid = {sid}')
        event.ignore()
        if self.s_one_sess_gr.isChecked():  # Длительность сеанса
            one_sess = self.s_eye.value()
            if self.s_eye_sess_end_list.currentText() == 'Выключить компьютер':  # Определение типа выкла
                eye_save_type = 0
            elif self.s_eye_sess_end_list.currentText() == 'Гибернация':
                eye_save_type = 1
            elif self.s_eye_sess_end_list.currentText() == 'Перезагрузка':
                eye_save_type = 2
            elif self.s_eye_sess_end_list.currentText() == 'Заблокировать экран':
                eye_save_type = 3
            elif self.s_eye_sess_end_list.currentText() == 'Экран блокировки':
                eye_save_type = 4
            eye_save_time = self.s_eye_rest_spin.value()
        else:
            self.s_eye.setValue(1)
            one_sess = 0
        datasave()
        self.hide()


class Block(QWidget):
    def __init__(self):
        super().__init__()
        log('Block __init__')
        self.setWindowFlags(Qt.WindowType.WindowStaysOnTopHint)
        self.setStyleSheet("background: black;")
        self.setWindowTitle("Следилка - Блокировщик ТЕБЯ")
        self.setWindowIcon(QIcon('icon.ico'))
        self.setWindowOpacity(0.8)
        if blocked:
            self.showFullScreen()
            self.activateWindow()

        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignCenter)
        self.setLayout(layout)
        label = QLabel()
        label.setStyleSheet("color: red;")
        label.setText("Отдых от монитора")
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        label.setFont(QFont("Arial", 40))
        layout.addWidget(label)
        self.b_timer = QLabel()
        self.b_timer.setStyleSheet("color: blue;")
        self.b_timer.setText(f'До конца Х минут')
        self.b_timer.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.b_timer.setFont(QFont("Arial", 40))
        layout.addWidget(self.b_timer)
        self.noclo()
        self.blocksec()

    def noclo(self):
        if not self.isActiveWindow() and blocked:
            self.up()
        if blocked:
            QTimer.singleShot(1, self.noclo)
        else:
            QTimer.singleShot(369, self.noclo)

    def up(self):
        keyboard.press_and_release('Esc')
        self.hide()
        self.showNormal()
        self.showFullScreen()

    def closeEvent(self, event):
        if blocked:
            event.ignore()

    def blocksec(self):
        global blocked
        if blocked and eye_save_type == 3:
            self.show()
        self.b_timer.setText(str(
            datetime.timedelta(seconds=int((eye_save_time_end - datetime.datetime.now()).total_seconds()))))
        self.b_timer.update()
        QTimer.singleShot(1000, self.blocksec)
        if (eye_save_time_end - datetime.datetime.now()).total_seconds() < 1:  # Если время отдыха закончилось,
            blocked = False  # то закрывать
            self.hide()


class Statistic(QWidget):
    def __init__(self):
        super().__init__()
        log('Statistic __init__')
        self.setWindowTitle("Статистика")
        self.setWindowIcon(QIcon('icon.ico'))
        self.setWindowFlags(Qt.WindowType.CustomizeWindowHint | Qt.WindowType.WindowCloseButtonHint)

        self.mainlay = QVBoxLayout()
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
        self.updater.start(1000)

    def stat_make(self):
        for i in reversed(full_stat):
            # for key in full_stat[i]:
            #     text = QLabel()
            #     # print('eeeeeeee',key, full_stat[i][key])
            #     if full_stat[i][key] != 0 and key != 'Win_lock_scr_real':
            #         text.setText(self.stat_l.text() +
            #                         f'{key.replace(".exe", "")} - {datetime.timedelta(seconds=full_stat[i][key])}\n')
            self.make_tab(sort(full_stat[i]), i)
        self.layout.addWidget(self.tabs)

    def make_tab(self, d, name):
        text = QLabel('')
        text.setAlignment(Qt.AlignmentFlag.AlignLeft)
        summ = 0
        for key in d:
            if d[key] != 0 and key != 'Win_lock_scr_real':
                text.setText(text.text() +
                             f'{key.replace(".exe", "")} - {datetime.timedelta(seconds=d[key])}\n')
                summ += d[key]
        if text.text().replace(' ', '') != '':
            text.setText(text.text() + f'\nВсего: {datetime.timedelta(seconds=summ)}')
            self.tabs.addTab(text, name)

    def stat_upd(self):
        # self.stat_l = QLabel('')
        self.stat_l.setText('Сегодня:\n')
        for key in sort(stat):
            if stat[key] != 0 and key != 'Win_lock_scr_real':
                self.stat_l.setText(self.stat_l.text() +
                                    f'{key.replace(".exe", "")} - {datetime.timedelta(seconds=stat[key])}\n')
        self.stat_l.setText(self.stat_l.text() + f'\nВсего: {datetime.timedelta(seconds=sid)}')


def sort(dict_):
    sorted_dict = {}
    # sorted_keys = list(sorted(dict, key=dict.get))[::-1]
    sorted_keys = list(reversed(sorted(dict_, key=dict_.get)))

    for w in sorted_keys:
        sorted_dict[w] = dict_[w]

    return sorted_dict


def add_to_stat():
    global stat
    if thiswin in stat:
        stat[thiswin] += 1
    else:
        stat[thiswin] = 1


def sett_upd():
    global sett
    sett = [one_sess, eye_save_type, eye_save_time, str(eye_save_time_end)]


def dataload():
    log('dataload')
    global sid, stat, start, delta_t, today, one_sess, eye_save_type, eye_save_time, sett, full_stat

    def readsett():
        global one_sess, eye_save_type, eye_save_time, eye_save_time_end, sett, sid
        # sid = 0
        with open('sett.slset', 'r') as file:  # Настройки
            sett = list(csv.reader(file, delimiter=','))[0]
            one_sess = int(sett[0])
            eye_save_type = int(sett[1])
            eye_save_time = int(sett[2])
            eye_save_time_end = datetime.datetime.strptime(sett[3], '%Y-%m-%d %H:%M:%S')
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

    def readstat():
        global sid
        sid = 0
        try:
            os.chdir('Statistic')
        except FileNotFoundError:
            os.mkdir('Statistic')
            os.chdir('Statistic')
        try:
            os.chdir(str(datetime.date.today()))
        except FileNotFoundError:
            os.mkdir(str(datetime.date.today()))
            os.chdir(str(datetime.date.today()))
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
            os.chdir('..')

    def readallstat():
        try:
            os.chdir('Statistic')
        except FileNotFoundError:
            os.mkdir('Statistic')
            os.chdir('Statistic')
        dirs = [e for e in os.listdir() if os.path.isdir(e)]
        print(dirs)
        if len(dirs) > 0:
            for d in dirs:
                full_stat[d] = {}
                print(d)
                os.chdir(d)
                try:
                    with open('stat.csv', 'r', newline='') as file:
                        reader = csv.reader(file, delimiter=':')
                        for row in reader:
                            print('rrrrrrrrrrrrrrrrrrrrrr', row[0])
                            if row[0] not in ['LockApp.exe']:
                                full_stat[d][row[0]] = int(row[1])
                    if d == str(datetime.date.today()):
                        full_stat[str(datetime.date.today())] = stat
                        del full_stat[str(datetime.date.today())]
                    os.chdir('..')
                except:
                    pass
        os.chdir('..')



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
    log(f'full_stat: {json.dumps(full_stat, indent=4)}')
    log('dataload.end')


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
        path_to_save = os.path.join(winshell.desktop(), str(name) + '.lnk')
    elif path_to_save == 'startup':
        '''Adding to startup (windows)'''
        user = os.path.expanduser('~')
        path_to_save = os.path.join(r"%s/AppData/Roaming/Microsoft/Windows/Start Menu/Programs/Startup/" % user,
                                    str(name) + '.lnk')
    else:
        path_to_save = os.path.join(path_to_save, str(name) + '.lnk')
    if os.path.exists(path_to_save):
        do = False
    else:
        do = True
    if do:
        if icon == 'default':
            icon = target
        if w_dir == 'default':
            w_dir = os.path.dirname(target)
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
    else:
        print('hhhhhhhhhhhhhhhahahaha')


def datasave():
    log('datasave')
    global sid, start, stat
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
    with open('sett.slset', 'w') as file:  # Настройки
        writer = csv.writer(file, delimiter=',', lineterminator='\n')
        writer.writerow(sett)

    try:
        os.chdir('Statistic')
    except FileNotFoundError:
        os.mkdir('Statistic')
        os.chdir('Statistic')
    try:
        # значит не начался новый день
        os.chdir(str(datetime.date.today()))
    except FileNotFoundError:
        # значит начался новый день
        os.mkdir(str(datetime.date.today()))
        os.chdir(str(datetime.date.today()))
    with open('stat.csv', 'w') as file:
        writer = csv.writer(file, delimiter=':', lineterminator='\n')
        for key in stat.keys():
            writer.writerow([key, stat[key]])
    for _ in range(2):
        os.chdir('..')

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


def thiswin_f():
    global thiswin
    pid = wintypes.DWORD()
    # active = ctypes.windll.user32.GetForegroundWindow()
    # active_window = ctypes.windll.user32.GetWindowThreadProcessId(active, ctypes.byref(pid))
    user32 = ctypes.windll.User32
    if user32.GetForegroundWindow() == 0 or user32.GetForegroundWindow() == 67370 or \
            user32.GetForegroundWindow() == 1901390:
        thiswin = 'Win_lock_scr_real'
    # 10553666 - return code for unlocked workstation1
    # 0 - return code for locked workstation1
    #
    # 132782 - return code for unlocked workstation2
    # 67370 -  return code for locked workstation2
    #
    # 3216806 - return code for unlocked workstation3
    # 1901390 - return code for locked workstation3
    #
    # 197944 - return code for unlocked workstation4
    # 0 -  return code for locked workstation4
    else:
        pid = pid.value
        for item in psutil.process_iter():
            if pid == item.pid:
                thiswin = item.name()
    threading.Timer(1, thiswin_f).start()


def pre_start():
    global today, delta_t, start, eye_save_time_end
    log('pre_start')
    print(f'до конца отдыха от мон: {(eye_save_time_end - datetime.datetime.now()).total_seconds()}')
    print(f'eye_save_time: {eye_save_time}\n'
          f'eye_save_time_end: {eye_save_time_end}\n'
          f'one_sess: {one_sess}\n'
          f'blocked: {blocked}')
    if eye_save_time * 60 > (eye_save_time_end - datetime.datetime.now()).total_seconds() > 0 and one_sess > 0:
        print('prestart-eyesavesssssssssssssssssssssssssssssssssssssss')
        eye_save()
    elif one_sess > 0 and eye_save_time * 60 < (eye_save_time_end - datetime.datetime.now()).total_seconds():
        print('prestart_seeeeeeeecondif')
        eye_save_time_end = datetime.datetime.strptime(
            datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'), '%Y-%m-%d %H:%M:%S') + \
            datetime.timedelta(minutes=eye_save_time)
    print(f'eye_save_time_end after upd: {eye_save_time_end}\n'
          f'blocked: {blocked}')
    thiswin_f()
    today = datetime.date.today()
    delta_t = today - start
    if delta_t.days > 0:
        log(f'if delta_t.days ({delta_t.days}) > 0: ')
        threading.Thread(target=msg.showinfo, args=("Информация",
                                                    f"Время проведённое за компьютером в прошлый раз: "
                                                    f"{datetime.timedelta(seconds=sid)}")).start()
        datasave()
        start = datetime.date.today()
        delta_t = today - start
    make_shortcut('Sledilka', os.path.abspath('Sledilka.exe'), 'startup')


def eye_save():
    global eye_save_time, eye_save_time_end, blocked
    log('eye_save')
    print(blocked)
    print(eye_save_time_end, eye_save_time)

    def hiber():
        os.popen('shutdown -h')

    def block_s():
        print('block_s')
        window.show_block()

    def locker():
        global blocked
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
        os.popen('shutdown -t 10 -s -c "Требуется отдых от монитора"')
    elif eye_save_type == 1:
        log('hiber')
        QTimer.singleShot(5000, hiber)
        msg.showinfo('Гибернация', 'Требуется отдых от монитора')
    elif eye_save_type == 2:
        log('restart')
        os.popen('shutdown -t 10 -r -c "Требуется отдых от монитора"')
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

#
# def add_clip(text):
#     global app
#     if app.clipboard() is not None:
#         app.clipboard().setText(str(text))


if __name__ == '__main__':
    log('main')
    app = QApplication(sys.argv)
    app.setWindowIcon(QIcon('icon.ico'))
    dataload()
    window = Timer()
    pre_start()
    window.show()
    app.exec()
