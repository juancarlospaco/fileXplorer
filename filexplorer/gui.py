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
__version__ = ' 1.0 '
__license__ = ' GPL '
__author__ = ' juancarlospaco '
__email__ = ' juancarlospaco@ubuntu.com '
__url__ = ''
__date__ = ' 20/02/2013 '
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
from sip import setapi
from subprocess import call
from string import punctuation
from re import sub
try:
    from urllib.request import urlopen  # py3
    import xmlrpc.client as xmlrpclib  # py3
except ImportError:
    from urllib2 import urlopen  # lint:ok
    import xmlrpclib  # lint:ok

# API 2
(setapi(a, 2) for a in ("QDate", "QDateTime", "QString", "QTime", "QUrl",
                        "QTextStream", "QVariant"))

from PyQt4.QtCore import Qt
from PyQt4.QtCore import QProcess
from PyQt4.QtCore import QTimer
from PyQt4.QtCore import QSize

from PyQt4.QtGui import QDialog
from PyQt4.QtGui import QDockWidget
from PyQt4.QtGui import QLabel
from PyQt4.QtGui import QIcon
from PyQt4.QtGui import QLineEdit
from PyQt4.QtGui import QAction
from PyQt4.QtGui import QPixmap
from PyQt4.QtGui import QApplication
from PyQt4.QtGui import QFileDialog
from PyQt4.QtGui import QProgressBar
from PyQt4.QtGui import QToolBar
from PyQt4.QtGui import QVBoxLayout
from PyQt4.QtGui import QWidget
from PyQt4.QtGui import QColorDialog
from PyQt4.QtGui import QTableWidget
from PyQt4.QtGui import QTableWidgetItem
from PyQt4.QtGui import QDirModel
from PyQt4.QtGui import QColumnView
from PyQt4.QtGui import QTextBrowser
from PyQt4.QtGui import QSlider

from .pypi_proxy_donottrack import ProxyTransport

from ninja_ide.gui.explorer.explorer_container import ExplorerContainer
from ninja_ide.core import plugin


# globals
HOME = os.path.expanduser("~")  # crossplatform shortcut to home sweet home
N = os.linesep  # crossplatform standard new line character string

try:
    logger = logging.getLogger(
                        'ninja-virtualenvgui-plugin.virtualenvgui_plugin.gui')
    logging.basicConfig()
    logger.setLevel(logging.DEBUG)
except:
    print(' ERROR: Failed to start Ninja-IDE DEBUG Loggers...')


###############################################################################


class filexplorerPluginMain(plugin.Plugin):
    ' main class for plugin '
    def initialize(self, *args, **kwargs):
        ' class init '
        global CONFIG_DIR
        ec = ExplorerContainer()
        super(filexplorerPluginMain, self).initialize(*args, **kwargs)

        self.dock = QDockWidget()
        self.dock.setAllowedAreas(Qt.LeftDockWidgetArea |
                                   Qt.RightDockWidgetArea)
        self.dock.setFeatures(QDockWidget.DockWidgetFloatable |
                                           QDockWidget.DockWidgetMovable)
        self.dock.setWindowTitle("fileXplorer")
        self.dock.setStyleSheet('QDockWidget::title { text-align: center; }')

        # search for the truth
        self.srch = QLineEdit()
        #self.srch.resize(self.srch.size().height(), self.dock.size().width())
        self.srch.setPlaceholderText(' Search for Python files Local or PyPI ')
        self.srch.returnPressed.connect(self.search)

        # Disk Usage Bar
        self.hdbar = QProgressBar()
        if sys.platform != 'win32':
            self.hdbar.setMaximum(os.statvfs(HOME).f_blocks *
                os.statvfs(HOME).f_frsize / 1024 / 1024 / 1024)
            self.hdbar.setValue(os.statvfs(HOME).f_bfree *
                os.statvfs(HOME).f_frsize / 1024 / 1024 / 1024)
        self.hdbar.setToolTip(str(self.hdbar.value()) + '% Total Disk Use ')
        #self.hdbar.setStyleSheet('''QProgressBar{background-color:
        #QLinearGradient(spread:pad,x1:0,y1:0,x2:1,y2:1,stop:0 rgba(255,0,0,99),
        #stop:1 rgba(9,255,9,200));color:#fff;border:none;border-radius:9px;}
        #QProgressBar::chunk{background-color:QLinearGradient(spread:pad,y1:0,
        #x1:0,y2:1,x2:0.27,stop:0 rgb(0,0,0),stop:1 rgb(9,99,255));padding:0;
        #border:none;border-radius:9px;height:9px;margin:1px;}''')

        self.model = QDirModel()
        self.fileView = QColumnView(self.dock)
        self.fileView.setAlternatingRowColors(True)
        # self.fileView.setFont(QFont(self.fileView.font().setBold(True)))
        self.fileView.setIconSize(QSize(32, 32))
        self.fileView.setModel(self.model)
        self.fileView.updatePreviewWidget.connect(self.runfile)

        self.sli = QSlider()
        self.sli.setRange(16, 128)
        self.sli.setValue(32)
        self.sli.setToolTip('Icon Size: 32 px. Move Slider to change.')
        self.sli.setOrientation(Qt.Horizontal)
        self.sli.valueChanged.connect(lambda: self.fileView.setIconSize(
            QSize(self.sli.value(), self.sli.value())))
        self.sli.sliderReleased.connect(lambda:
            self.sli.setToolTip('Icon Size: ' + str(self.sli.value()) + ' px'))

        class TransientWidget(QWidget):
            ' persistant widget thingy '
            def __init__(self, widget_list):
                ' init sub class '
                super(TransientWidget, self).__init__()
                vbox = QVBoxLayout(self)
                for each_widget in widget_list:
                    vbox.addWidget(each_widget)

        tw = TransientWidget((self.srch, self.dock, self.sli, self.hdbar))
        ec.addTab(tw, "fileXplorer")

        ####

        self.process = QProcess()
        self.process.finished.connect(self.processFinished)

        self.preview = QLabel(self.fileView)
        self.preview.setTextFormat(0)
        self.preview.setStyleSheet('QLabel{font-size:9px;}')
        self.preview.setAutoFillBackground(True)
        self.fileView.setPreviewWidget(self.preview)
        self.dock.setWidget(self.fileView)

        # take a shot
        self.pic = QAction(QIcon.fromTheme("camera-photo"), 'Screenshot', self)
        self.pic.triggered.connect(lambda: QPixmap.grabWindow(
            QApplication.desktop().winId()).save(QFileDialog.getSaveFileName(
            self.dock, " Save Screenshot As ... ", HOME, '(*.png)')))

        # copy time
        self.tim = QAction(QIcon.fromTheme("user-away"),
                           'Date and Time to Clipboard', self)
        self.tim.triggered.connect(lambda: QApplication.clipboard().setText(
            datetime.datetime.now().strftime(" %A %B %d-%m-%Y %H:%M:%S %p ")))

        # color chooser
        self.cl = QAction(QIcon.fromTheme("applications-graphics"),
                          'Color Chooser to Clipboard', self)
        self.cl.triggered.connect(self.showQColorDialog)

        # icon chooser
        self.icn = QAction(QIcon.fromTheme("insert-image"),
                          'Icon Chooser to Clipboard', self)
        self.icn.triggered.connect(self.iconChooser)

        # tool bar with actions
        QToolBar(self.dock).addActions((self.cl, self.icn, self.tim, self.pic))

        self.textBrowser = QTextBrowser(self.dock)
        self.textBrowser.setAutoFillBackground(True)
        self.textBrowser.setGeometry(self.dock.geometry())
        self.textBrowser.hide()

    def processFinished(self):
        ' print info of finished processes '
        print(" INFO: OK: QProcess finished . . . ")

    def search(self):
        ' function to search python files '
        # get search results of python filenames local or remote
        pypi_url = 'http://pypi.python.org/pypi'
        # pypi query
        pypi = xmlrpclib.ServerProxy(pypi_url, transport=ProxyTransport())
        try:
            pypi_query = pypi.search({'name': str(self.srch.text()).lower()})
            pypi_fls = list(set(['pypi.python.org/pypi/' + a['name'] +
                   ' | pip install ' + a['name'] for a in pypi_query]))
        except:
            pypi_fls = '<b> ERROR: Internet not available! ಠ_ಠ </b>'
        s_out = ('<br> <br> <br> <h3> Search Local Python files: </h3> <hr> ' +
        # Jedi list comprehension for LOCAL search
        str(["{}/{}".format(root, f) for root, f in list(itertools.chain(*
            [list(itertools.product([root], files))
            for root, dirs, files in os.walk(str(
            QFileDialog.getExistingDirectory(self.dock,
            'Open Directory to Search', os.path.expanduser("~"))))]))
            if f.endswith(('.py', '.pyw', '.pth')) and not f.startswith('.')
            and str(self.srch.text()).lower().strip() in f]
        ).replace(',', '<br>') + '<hr><h3> Search PyPI Python files: </h3>' +
        # wraped pypi query REMOTE search
        str(pypi_fls).replace(',', '<br>') + '<hr>Auto-Proxy:ON,DoNotTrack:ON')
        # print(s_out)
        try:
            call('notify-send fileXplorer Searching...', shell=True)
        except:
            pass
        self.srch.clear()
        self.textBrowser.setGeometry(self.dock.geometry())
        self.textBrowser.setHtml(s_out)
        self.textBrowser.show()
        tmr = QTimer(self.fileView)
        tmr.timeout.connect(self.textBrowser.hide)
        tmr.start(20000)

    def showQColorDialog(self):
        ' Choose a Color and copy it to clipboard '
        color = QColorDialog.getColor()
        if color.isValid():
            QApplication.clipboard().setText('"' + color.name() + '"')

    def iconChooser(self):
        ' Choose a Icon and copy it to clipboard '
        #
        from .std_icon_naming import std_icon_naming as a
        #
        prv = QDialog(self.dock)
        prv.setWindowFlags(Qt.FramelessWindowHint)
        prv.setAutoFillBackground(True)
        prv.setGeometry(self.fileView.geometry())
        table = QTableWidget(prv)
        table.setColumnCount(1)
        table.setRowCount(len(a))
        table.verticalHeader().setVisible(True)
        table.horizontalHeader().setVisible(False)
        table.setShowGrid(True)
        table.setIconSize(QSize(128, 128))
        for index, icon in enumerate(a):
            item = QTableWidgetItem(QIcon.fromTheme(icon), '')
            # item.setData(Qt.UserRole, '')
            item.setToolTip(icon)
            table.setItem(index, 0, item)
        table.clicked.connect(lambda: QApplication.clipboard().setText(
            'QtGui.QIcon.fromTheme("' + table.currentItem().toolTip() + '")'))
        table.doubleClicked.connect(prv.close)
        table.resizeColumnsToContents()
        table.resizeRowsToContents()
        QLabel('<h3> <br> 1 Click Copy, 2 Clicks Close </h3>', table)
        table.resize(prv.size())
        prv.exec_()

    def runfile(self, index):
        ' run the choosed file '
        s = str(file(self.model.filePath(index), 'r').read().strip())
        f = str(self.model.filePath(index))
        # ctime is NOT crossplatform,metadata change on *nix,creation on Window
        # http://docs.python.org/library/os.path.html#os.path.getctime
        m = (f + N + str(os.path.getsize(f) / 1024) + ' Kilobytes' + N +
            str(len(file(f, 'r').readlines())) + ' Lines' + N +
            str(len(s.replace(N, ''))) + ' Characters' + N +
            str(len([a for a in sub('[^a-zA-Z0-9 ]', '', s).split(' ')
                if a != ''])) + ' Words' + N +
            str(len([a for a in s if a in punctuation])) + ' Punctuation' + N +
            oct(os.stat(f).st_mode)[-3:] + ' Permissions' + N +
            time.ctime(os.path.getatime(f)) + ' Accessed' + N +
            time.ctime(os.path.getmtime(f)) + ' Modified' + N +
            'Owner: ' + str(self.model.fileInfo(index).owner()) + N +
            'Is Writable:' + str(self.model.fileInfo(index).isWritable()) + N +
            'Is Executable:' + str(self.model.fileInfo(index).isExecutable()) +
            N + 'Is Hidden:' + str(self.model.fileInfo(index).isHidden()) + N +
            'Is SymLink: ' + str(self.model.fileInfo(index).isSymLink()) + N +
            'File Extension: ' + str(self.model.fileInfo(index).suffix())
        )
        #print(m)
        self.preview.setToolTip(m)
        self.preview.setText(s)
        self.preview.resize(self.preview.size().width(),
                            self.dock.size().height())
        self.process.start('xdg-open ' + f)
        if not self.process.waitForStarted():
            print((" ERROR: %s failed!" % (str(f))))
            return


if __name__ == '__main__':
    ' Do NOT add anything here ! '
    print(__doc__)
