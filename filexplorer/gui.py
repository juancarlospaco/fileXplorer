# -*- coding: utf-8 -*-
# PEP8:OK, LINT:OK, PY3:??


#############################################################################
## This file may be used under the terms of the GNU General Public
## License version 2.0 or 3.0 as published by the Free Software Foundation
## and appearing in the file LICENSE.GPL included in the packaging of
## this file.  Please review the following information to ensure GNU
## General Public Licensing requirements will be met:
## http:#www.fsf.org/licensing/licenses/info/GPLv2.html and
## http:#www.gnu.org/copyleft/gpl.html.
##
## This file is provided AS IS with NO WARRANTY OF ANY KIND, INCLUDING THE
## WARRANTY OF DESIGN, MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE.
#############################################################################


# metadata
' fileXplorer for Ninja-IDE '
__version__ = ' 0.2 '
__license__ = ' GPL '
__author__ = ' juancarlospaco '
__email__ = ' juancarlospaco@ubuntu.com '
__url__ = ''
__date__ = ' 25/01/2013 '
__prj__ = ' filexplorer '
__docformat__ = 'html'
__source__ = ''
__full_licence__ = ''


# imports
import os
import sys
import time
import datetime
import logging
import itertools
from random import randint
from subprocess import call
from string import punctuation
from re import sub
try:
    from urllib.request import urlopen  # py3
except ImportError:
    from urllib2 import urlopen  # lint:ok
if sys.platform != "win32":
    try:
        from subprocess import getoutput  # py3 on nix
    except ImportError:
        from commands import getoutput  # lint:ok

from PyQt4.QtCore import Qt
from PyQt4.QtCore import QProcess
from PyQt4.QtCore import QTimer
from PyQt4.QtCore import QDir
from PyQt4.QtCore import QPoint

from PyQt4.QtGui import QPushButton
from PyQt4.QtGui import QDialog
from PyQt4.QtGui import QMessageBox
from PyQt4.QtGui import QDockWidget
from PyQt4.QtGui import QLabel
from PyQt4.QtGui import QIcon
from PyQt4.QtGui import QLineEdit
from PyQt4.QtGui import QListWidget
from PyQt4.QtGui import QShortcut
from PyQt4.QtGui import QTextBrowser
from PyQt4.QtGui import QPrintPreviewDialog
from PyQt4.QtGui import QAction
from PyQt4.QtGui import QPixmap
from PyQt4.QtGui import QApplication
from PyQt4.QtGui import QFileDialog
from PyQt4.QtGui import QProgressBar
from PyQt4.QtGui import QToolBar
from PyQt4.QtGui import QLCDNumber
from PyQt4.QtGui import QListWidgetItem
from PyQt4.QtGui import QFont
from PyQt4.QtGui import QColor
from PyQt4.QtGui import QPainter
from PyQt4.QtGui import QHBoxLayout
from PyQt4.QtGui import QWidget

from ninja_ide.gui.explorer.explorer_container import ExplorerContainer
from ninja_ide.core import plugin


# globals
CONFIG_DIR = ''  # '' to choose on start, else '/home/user/path_to_py_files'
HOME = os.path.expanduser("~")  # crossplatform shortcut to home sweet home
WEATHER = 'http://m.wund.com/global/stations/87582.html'  # http:m.wund.com
N = os.linesep  # crossplatform standard new line character string
E = ' ERROR '  # trick for A if B else C, where C is E
CHK = 'pylint --output-format=html '  # PyLint command and arguments
# SCH = 'locate --ignore-case --existing --nofollow --quiet --basename -l 35 '


try:
    logger = logging.getLogger(
                        'ninja-virtualenvgui-plugin.virtualenvgui_plugin.gui')
    logging.basicConfig()
    logger.setLevel(logging.DEBUG)
except:
    print(' ERROR: Failed to start Ninja-IDE DEBUG Loggers...')


###############################################################################


class CustomProgressBar(QProgressBar):
    ' kitty kitty kitty kitty kitty '
    def __init__(self, parent=None):
        ' init '
        QProgressBar.__init__(self, parent)
        self.nyan = QLabel(parent)
        self.nyan.setPixmap(QPixmap(
        os.path.join(os.path.abspath(os.path.dirname(__file__)), "nyan.png")))
        self.rainbow = [QColor(255, 0, 0), QColor(255, 147, 28),
                        QColor(238, 245, 12), QColor(75, 245, 12),
                        QColor(115, 115, 255), QColor(238, 193, 210)]
        self.value_label = QLabel('0', parent)

    def paintEvent(self, event):
        ' uh uh booga ugah '
        qp = QPainter()
        qp.begin(self)
        self.drawBar(qp)
        qp.end()
        self.nyan.move(QPoint(self.value() - self.nyan.width() / 5 +
                              randint(0, 2), randint(-1, 1)))
        self.value_label.move(QPoint((self.value() + self.nyan.width() / 6),
            0))
        if self.value() % 2 == 0:
            self.value_label.setText(
            '<font color="white"><b>{0}</b> Nyan!</font>'.format(self.value()))
        else:
            self.value_label.setText(
            '<font color="white"><b>{0}</b></font>'.format(self.value()))
        if self.value() >= 100:
            self.value_label.setText(
                '<font color="black"><h3>{0}</h3></font>'.format(self.value()))
            #self.value_label.move(QPoint((self.value() - self.nyan.width() / 3
                #), 0))
            self.nyan.hide()

    def drawBar(self, qp):
        ' do you nyan bro ? '
        size = self.size()
        color_height = size.height() / len(self.rainbow)
        qp.setPen(QColor(0, 0, 0))
        qp.setBrush(QColor(5, 40, 96))
        qp.drawRect(0, 0, size.width(), size.height())
        qp.setPen(QColor(255, 255, 255))
        for i in range(9):
            x = randint(1, size.width() - 1)
            y = randint(1, size.height() - 1)
            qp.drawPoint(x, y)
        qp.setPen(QColor(0, 0, 0))
        for i in range(len(self.rainbow)):
            qp.setBrush(self.rainbow[i])
            qp.drawRect(0, color_height * i, self.value(), color_height)


###############################################################################


class filexplorerPluginMain(plugin.Plugin):
    ' main class for plugin '
    def initialize(self, *args, **kwargs):
        ' class init '
        ec = ExplorerContainer()
        super(filexplorerPluginMain, self).initialize(*args, **kwargs)

        self.dock1 = QDockWidget()
        self.dock1.setAllowedAreas(Qt.LeftDockWidgetArea |
                                   Qt.RightDockWidgetArea)
        self.dock1.setFeatures(QDockWidget.DockWidgetFloatable |
                                           QDockWidget.DockWidgetMovable)
        # self.dock1.setToolTip("fileXplorer > dock 1")
        self.dock1.setMaximumWidth(200)
        self.dock2 = QDockWidget()
        self.dock2.setAllowedAreas(Qt.LeftDockWidgetArea |
                                   Qt.RightDockWidgetArea)
        self.dock2.setFeatures(QDockWidget.DockWidgetFloatable |
                                           QDockWidget.DockWidgetMovable)
        # self.dock2.setToolTip("fileXplorer > dock 2")

        class TransientWidget(QWidget):
            ' persistant widget thingy '
            def __init__(self, widget_list):
                ' init sub class '
                super(TransientWidget, self).__init__()
                vbox = QHBoxLayout(self)
                for each_widget in widget_list:
                    vbox.addWidget(each_widget)

        tw = TransientWidget((self.dock1, self.dock2))
        ec.addTab(tw, "fileXplorer")

        ####

        self.process = QProcess()
        self.process.finished.connect(self.processFinished)

        # GUI stuff
        # self.setToolTip(__doc__)
        self.dock1.setFont(QFont(self.dock1.font().setBold(True)))

        # reload and target
        self.reload = QPushButton(QIcon.fromTheme("view-refresh"), '',
                                  self.dock1)
        self.reload.clicked.connect(self.initFolder)
        self.reload.setFlat(True)
        # self.reload.setCursor(QCursor(Qt.PointingHandCursor))

        # directory lists
        self.contentsWidget = QListWidget()
        self.contentsWidget.setAlternatingRowColors(True)
        # self.contentsWidget.setMaximumWidth(200)
        # self.contentsWidget.setSortingEnabled(True)
        # self.contentsWidget.setSpacing(1)
        # self.contentsWidget.setIconSize(QSize(32, 32))
        # self.contentsWidget.setCurrentRow(0)
        self.contentsWidget.currentItemChanged.connect(self.changePage)
        self.contentsWidget.itemDoubleClicked.connect(lambda:
            self.openfolder(str(os.path.join(CONFIG_DIR,
            str(self.contentsWidget.currentItem().data(Qt.UserRole))))))
        # Zoom +
        QShortcut("Ctrl++", self.contentsWidget, activated=lambda:
           self.contentsWidget.setIconSize(self.contentsWidget.iconSize() * 2))
        # Zoom -
        QShortcut("Ctrl+-", self.contentsWidget, activated=lambda:
           self.contentsWidget.setIconSize(self.contentsWidget.iconSize() / 2))
        # Delete Items from Folder Tree
        QShortcut("Delete", self.contentsWidget, activated=lambda:
            self.contentsWidget.currentItem().setHidden(True))

        # file manager for py files
        self.textBrowser = QTextBrowser()
        self.textBrowser.setOpenLinks(False)
        self.textBrowser.setHtml(('<br><hr>Beta !<h1><i><center>' + __doc__ +
        '<img src="/usr/share/ninja-ide/img/icon.png"></i></h1><hr></center>'))
        self.textBrowser.anchorClicked.connect(self.launchProgram)

        self.dock1.setWidget(self.contentsWidget)
        self.dock2.setWidget(self.textBrowser)

        # help about
        self.abt = QAction(QIcon.fromTheme("help-about"), 'About', self)
        self.abt.triggered.connect(lambda: QMessageBox.about(self.dock2,
        __doc__, __doc__ + N + __license__ + ', by' + __author__ + ',' +
        __email__ + N * 2 + '-Simple is better than Complex.' +
        'Thats why fileXplorer is that simple' + N +
        '-Flat is better than Nested.Thats why the folder tree is plain Flat' +
        N + '-The implementation is easy to explain.  It has < 500 lines! '))

        # print file view
        self.prt = QAction(QIcon.fromTheme("document-print"), 'Print', self)
        self.prt.triggered.connect(lambda:
           QPrintPreviewDialog(paintRequested=self.textBrowser.print_).exec_())

        # take a shot
        self.pic = QAction(QIcon.fromTheme("camera-photo"), 'Screenshot', self)
        self.pic.triggered.connect(lambda: QPixmap.grabWindow(
            QApplication.desktop().winId()).save(QFileDialog.getSaveFileName(
            self.dock2, " Save Screenshot As ... ", HOME, '(*.png)')))

        # LCD Date and Time
        self.clock = QLCDNumber(self.textBrowser)
        self.clock.setNumDigits(22) if not self.clock.hide() else E
        # self.clock.setAutoFillBackground(True)
        self.clock.setStyleSheet('''*{background-color:QLinearGradient(spread:
        pad,x1:0,y1:0,x2:1,y2:1,stop:0 rgb(99,128,128),stop:1 rgb(9,9,9));}''')
        tmr = QTimer(self)
        tmr.timeout.connect(lambda: self.clock.display(
            datetime.datetime.now().strftime("%d-%m-%Y %H:%M:%S %p")))
        self.clock.setGeometry(0, 30, 200, 50) if not tmr.start(1000) else E
        self.clk = QAction(QIcon.fromTheme("appointment-soon"), 'Time', self)
        self.clk.triggered.connect(lambda:
        self.clock.show() if not self.clock.isVisible() else self.clock.hide())

        # Disk Usage Bar
        self.hdbar = QProgressBar(self.textBrowser)
        self.hdbar.setGeometry(9, 30, 25, 400) if not self.hdbar.hide() else E
        self.hdbar.setMaximum(os.statvfs(HOME).f_blocks *
            os.statvfs(HOME).f_frsize / 1024 / 1024 / 1024)
        self.hdbar.setValue(os.statvfs(HOME).f_bfree *
            os.statvfs(HOME).f_frsize / 1024 / 1024 / 1024)
        # self.hdbar.setToolTip(str(self.hdbar.value()))
        self.hdbar.setOrientation(Qt.Vertical)
        self.hdbar.setStyleSheet('''QProgressBar{background-color:
        QLinearGradient(spread:pad,x1:0,y1:0,x2:1,y2:1,stop:0 rgba(255,0,0,99),
        stop:1 rgba(0,255,0,200));color:#fff;border:none;border-radius:9px;}
        QProgressBar::chunk{background-color:QLinearGradient(spread:pad,x1:0,
        y1:0,x2:1,y2:0.27,stop:0 rgb(0,0,0),stop:1 rgb(150,255,255));padding:0;
        border:none;border-radius:9px;height:19px;margin:1px;}''')
        self.hdd = QAction(QIcon.fromTheme("drive-harddisk"), 'Disk Use', self)
        self.hdd.triggered.connect(lambda:
        self.hdbar.show() if not self.hdbar.isVisible() else self.hdbar.hide())

        # Weather Conditions
        self.wea = QAction(QIcon.fromTheme("weather-showers"), 'Weather', self)
        # I mailed people of page they say mobile ver never change,safe 2 parse
        #
        # this one is a " cosmetic " cut-off    (PyWAPI is dead)
        self.wea.triggered.connect(lambda: self.textBrowser.setHtml(
            '<h3><br>Weather</h3>' + ''.join(a for a in urlopen(WEATHER).read()
            .strip().splitlines()[9:90] if a not in set(punctuation))))
        # this one is raw, with footer and header
        # self.wea.triggered.connect(lambda:
            # self.textBrowser.setHtml(urlopen(WEATHER).read())

        # search for the truth
        self.sch = QAction(QIcon.fromTheme("edit-find"), 'Search file', self)
        self.sch.triggered.connect(lambda:
        self.srch.show() if not self.srch.isVisible() else self.srch.hide())
        self.srch = QLineEdit(self.textBrowser)
        self.srch.move(99, 30) if not self.srch.hide() else E
        self.srch.setPlaceholderText('Search Python files')
        self.srch.returnPressed.connect(lambda: self.textBrowser.setHtml(
        ' <br> <h3> Search Results </h3> <hr> ' +
        # getoutput(SCH + str(self.srch.text()).lower() + '.py')))
        # Jedi list comprehension
        str(["{}/{}".format(root, f) for root, f in list(itertools.chain(*
            [list(itertools.product([root], files))
            for root, dirs, files in os.walk(CONFIG_DIR)]))
            if f.endswith(('.py', '.pyw', '.pth')) and not f.startswith('.')
            and str(self.srch.text()).lower().strip() in f]
        ).replace(',', '<br>')))

        # self.sc = QAction(QIcon.fromTheme("applications-development"),
        #    'View, study, edit fileXplorer Libre Source Code', self)
        # self.sc.triggered.connect(lambda: os.system('ninja-ide ' + __file__))

        # open a Terminal
        # self.trm = QAction(QIcon.fromTheme("utilities-terminal"), '', self)
        # self.trm.triggered.connect(lambda: call('xterm', shell=True ))

        # about Qt
        # self.qta = QAction(QIcon.fromTheme("help-about"), 'About Qt', self)
        # self.qta.triggered.connect(lambda: QMessageBox.aboutQt(self))

        # tool bar with actions
        QToolBar(self.textBrowser).addActions((self.abt, self.prt, self.pic,
        self.clk, self.hdd, self.wea, self.sch))  # self.trm, self.sc, self.qta

        # check for hardcoded directory
        if CONFIG_DIR != '':
            self.initContentsWidget()

    def launchProgram(self, _pyf):
        ' call ninja-ide with file as argument,or text preview,or lint report '
        # process file, I hope Ninja-IDE opens file on a New Tab ?
        if str(_pyf.toString()).startswith('PREVIEW:'):
            # Quick Preview Python files on self-closing Widget Overlay
            f = file(_pyf.toString().replace('PREVIEW:', ''), 'r')
            prv = QDialog(self.dock2)
            prv.setWindowFlags(Qt.FramelessWindowHint)
            prv.setAutoFillBackground(True)
            prv.setGeometry(self.textBrowser.geometry())
            tex = QLabel(f.read(), prv)
            tex.setTextFormat(0)
            tex.setStyleSheet('*{font-size:9px;}')
            progre = CustomProgressBar(prv)
            progre.setValue(0)
            tmNyan = QTimer(prv)
            tmNyan.timeout.connect(lambda: progre.setValue(progre.value() + 1))
            tmNyan.start(50)
            tmr = QTimer(prv)
            tmr.timeout.connect(prv.close)
            tmr.start(5000)
            tex.resize(prv.size())
            prv.exec_()
        elif str(_pyf.toString()).startswith('CHECK:'):
            # Quick Lint Report files on self-closing Widget Overlay
            a = getoutput(CHK +
                             str(_pyf.toString()).replace('CHECK:', ''))
            prv = QDialog(self.dock2)
            prv.setWindowFlags(Qt.FramelessWindowHint)
            prv.setAutoFillBackground(True)
            prv.setGeometry(self.textBrowser.geometry())
            tex = QLabel('<center>10 Seconds Auto-Close!</center>' + a, prv)
            progre = CustomProgressBar(prv)
            progre.setValue(0)
            tmNyan = QTimer(prv)
            tmNyan.timeout.connect(lambda: progre.setValue(progre.value() + 1))
            tmNyan.start(100)
            tmr = QTimer(prv)
            tmr.timeout.connect(prv.close)
            tmr.start(10000)
            tex.resize(prv.size())
            prv.exec_()
        else:
            self.process.start('ninja-ide ' + _pyf.toString())
            if not self.process.waitForStarted():
                # print((" ERROR: %s failed!" % (str(_pyf.toString()))))
                return
        # print(" INFO: OK: %s launched . . ." % (str(_pyf.toString())))
        # QApplication.setOverrideCursor(Qt.BusyCursor)
        # self.setDisabled(True)
        # self.contentsWidget.setDisabled(True)
        # self.textBrowser.setDisabled(True)

    def processFinished(self):
        ' print info of finished processes '
        print(" INFO: OK: QProcess finished . . . ")
        # QApplication.restoreOverrideCursor()
        # self.setDisabled(False)
        # self.contentsWidget.setDisabled(False)
        # self.textBrowser.setDisabled(False)

    def changePage(self):
        ' init values and change pages '
        # self.contentsWidget.currentItem().setSelected(True)
        g = self.contentsWidget.currentItem().data(Qt.UserRole)
        _dir = os.path.join(CONFIG_DIR, str(g))
        current_column = 1
        # retrieve information from '.py' files
        folder = QDir(_dir)
        folder.setFilter(QDir.Files)
        html = ""
        for fileName in folder.entryInfoList():
            try:
                if str(fileName.fileName()).lower().encode('utf-8').endswith(
                    (".py", ".pyw", ".pth")):  # py file, py mswindows, py path
                    _flnm = os.path.join(_dir, str(fileName.fileName()))
                    _cmnt = self.commentBuilder(_flnm)
                    _pyf = str(fileName.fileName())
                    # icon filename full path string
                    _icn = str(os.path.join(os.path.abspath(
                           os.path.dirname(__file__)), "text-x-python.svg"))
                    # build cells in html page
                    if current_column == 1:
                        html += ("<tr>" + self.cellB(_icn, _pyf, _cmnt, _flnm))
                    if current_column == 1:
                        current_column += 1
                    elif current_column == 2:
                        current_column -= 1
            except UnicodeEncodeError:
                pass  # should never end here, it still works, but item ignored
        if html == "":
            self.textBrowser.setHtml(('<br><h4>No Python on Folder! ಠ_ಠ</h4>'))
            return  # should never end here,it still works,but displays nothing
        # display html page in text browser
        self.textBrowser.setHtml('''<style>*{text-decoration:none;padding:0;
        margin:0;border:0;width:100%;font-family:'ubuntu light';}</style>''' +
        '<center><h3><br>' + self.getSectionTitle(_dir) +
        "</h3> <table>" + html + '</table></center>')

    def cellB(self, _icn, _pyf, _cmnt, _flnm):
        ' function to build HTML table cells '
        # mix HTML and string variables to build a table cell, return the cell
        cell = ("<hr><td title=' 1 click Quick Preview Python file: " +
                str(_flnm) + "' ><a href='PREVIEW:" + str(_flnm) +
                "'><img width='32' height='48' src='" + str(_icn) +
                "'></a></td><td><a href='" + str(_flnm) + "'><b>" + str(_pyf)
                + "</b></a><br><small><small><small><small><small>" +
                "<a title=' 1 click Lint Check Python file: " + str(_flnm) +
                "' href='CHECK:" + str(_flnm) + "'>" + str(_cmnt) +
                "</a></small></small></small></small></small></a></td>")
        # print(cell)
        return cell

    def initContentsWidget(self):
        ' function to initialize the folders lists widget and fill contents '
        QListWidgetItem(self.contentsWidget)  # empty item as separator
        folder = QDir(CONFIG_DIR)
        folder.setFilter(QDir.Dirs)
        for folderName in folder.entryInfoList():
            # if folder filename is > 2 to avoid '.' and '..'
            if len(folderName.fileName()) > 2:
                _dir = os.path.join(CONFIG_DIR, str(folderName.fileName()))
                # if folder has python files inside
                if len([f for f in os.listdir(_dir) if not f.startswith('.')
                and f.endswith(('.py', '.pyw', '.pth'))]) != 0:
                    configButton = QListWidgetItem(self.contentsWidget)
                    configButton.setIcon(QIcon.fromTheme("folder"))
                    configButton.setText(self.getSectionTitle(_dir))
                    configButton.setToolTip(folderName.fileName() + N +
                        '1 click view,2 clicks open' + N +
                        'CTRL++ Zoom+, CTRL+- Zoom-' + N +
                        'Delete to hide selected item')
                    # configButton.setTextAlignment(Qt.AlignLeft)
                    configButton.setData(Qt.UserRole, folderName.fileName())
                    # configButton.setFlags(Qt.ItemIsSelectable |
                    #                      Qt.ItemIsEnabled)
                    # configButton.setFlags(Qt.ItemIsEnabled)
                    # configButton.setFont(QFont(
                    #    configButton.font().setBold(True)))

    def commentBuilder(self, _flnm):
        ' build comments with human readable info for the user '
        # TODO  ...always add more info
        f = file(_flnm, 'r').read()
        # ctime is NOT crossplatform,metadata change on *nix,creation on Window
        # http://docs.python.org/library/os.path.html#os.path.getctime
        #
        # Python built-in mimetype uses file extension,if no extension it fails
        # Python Magic http://github.com/ahupp/python-magic
        return (str(os.path.getsize(_flnm) / 1024) + ' Kilobytes, ' +
               str(len(file(_flnm, 'r').readlines())) + ' Lines, ' +
               str(len(f.replace(N, ''))) + ' Characters, ' +
               str(len([a for a in sub('[^a-zA-Z0-9 ]', '', f).split(' ')
               if a != ''])) + ' Words, ' +
               str(len([a for a in f if a in punctuation])) + ' Punctuation,' +
               oct(os.stat(_flnm).st_mode)[-3:] + ' Permissions, ' +
               time.ctime(os.path.getatime(_flnm)) + ' Accessed, ' +
               time.ctime(os.path.getmtime(_flnm)) + ' Modified. '
               # magic.Magic(mime=True).from_file(_flnm) + ' Mimetype '
               )

    def getSectionTitle(self, dir_name):
        ' parse title for file view titles '
        # return the string of the directory sliced by the last / of itself  ;D
        return str(dir_name).split("/")[len(str(dir_name).split("/")) - 1]

    def initFolder(self):
        ' function to ask the user for new folders to add into lists '
        # make CONFIG_DIR global, ask for CONFIG_DIR, call initContentsWidget()
        global CONFIG_DIR
        CONFIG_DIR = str(QFileDialog.getExistingDirectory(self.dock2,
                     ' Please, open a Folder to use as root folder...', HOME))
        self.initContentsWidget()

    def openfolder(self, filename=HOME):
        ' crossplatform workaround to open folders passed as arg, else home '
        try:
            os.startfile(filename)
        except:
            call('xdg-open "' + filename + '"', shell=True)
