from PyQt5 import QtWidgets, uic, QtCore, QtGui
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
import sys
import qdarkstyle
import os
from concurrent.futures import ThreadPoolExecutor
import time
import appdirs
from subprocess import Popen, PIPE
from pathlib import Path
tabnum = 1

def exists(var):
     return var in globals()

# Allows live logging of shell commands
def run(command):
    process = Popen(command, stdout=PIPE, shell=True)
    while True:
        line = process.stdout.readline().rstrip()
        if not line:
            break
        yield line

finished = 0

# Backup channel with yt-dlp
def backup(channel, currentindex):
    global finished
    global channels
    quality = str(window.qualityBox.currentText())
    window._worker.data.emit([f"Job {str(currentindex)} -> Started archiving: {channel}\n"])
    for path in run(f"cd {foldpath} && yt-dlp -f 'bv*[height<={quality[:-1]}]+ba' {channel} -o '%(channel)s/%(title)s.%(ext)s'"):
        resp = path.decode()+"\n"
        if resp[:5] == "ERROR":
            window._worker.data.emit(["", "", "", resp])
        else:
            window._worker.data.emit(["", [currentindex, resp]])
    finished += 1
    window._worker.data.emit([f"Job {str(currentindex)} -> Finished archiving: {channel}\n{finished}/{len(channels)} archived\n"])
    
class Archive(QtCore.QThread):
    global window
    data = QtCore.pyqtSignal(list)

    def __init__(self, parent=None):
        super(Archive, self).__init__(parent)
        self._stopped = True
        self._mutex = QtCore.QMutex()

    def stop(self):
        self._mutex.lock()
        self._stopped = True
        self._mutex.unlock()

    def run(self):
        global channels
        global finished
        global foldpath

        # Update archive txt
        Path(foldpath).mkdir(parents = True, exist_ok = True)
        with open(foldpath+"/archive.txt", 'w+') as f:
            f.write(window.urlBox.toPlainText())

        channels = window.urlBox.toPlainText().split("\n")
        
        # Archive all channels
        with ThreadPoolExecutor(max_workers=100) as executor:
            for i in range(len(channels)):
                if i > 0:
                    self.data.emit(['', '', True])
                executor.submit(backup, channels[i], i)
    
        while finished < len(channels):
            time.sleep(1)

        finished = 0
        tabnum = 1
        self.data.emit(['Done'])

class ErrorWindow(QDialog):
  def __init__(self, parent):
    super(ErrorWindow, self).__init__(parent)
    uic.loadUi('Assets/error.ui', self)

class ArchiveWindow(QDialog):
  def __init__(self, parent):
    super(ArchiveWindow, self).__init__(parent)
    uic.loadUi('Assets/archive.ui', self)

class TabInit(QtWidgets.QWidget):
    def __init__(self, parent=None):
        global tabnum
        global window

        super(TabInit, self).__init__(parent)
        name = "t"+str(tabnum)
        lay = QtWidgets.QVBoxLayout(self)

        wid = QPlainTextEdit(objectName = name)
        wid.setReadOnly(True)

        setattr(window.transferw, name, wid)
        wid = getattr(window.transferw, name)

        lay.addWidget(wid)


class Ui(QtWidgets.QMainWindow):
    def __init__(self):
        super(Ui, self).__init__()

        # Load UI and Fonts
        self.fontDB = QtGui.QFontDatabase()
        self.fontDB.addApplicationFont("Assets/font.ttf")
        uic.loadUi('Assets/main.ui', self)
        self.qualityBox.addItems(["1080p","720p","480p","360p","240p","144p"])
        self.get_path()
        self.get_data()

        # Reveal window
        self.show()

        # Load threads
        self._worker = Archive()
        self._worker.started.connect(self.worker_started_callback)
        self._worker.finished.connect(self.worker_finished_callback)
        self._worker.data.connect(self.worker_data_callback)
        
        # Load UI
        self.startButton.clicked.connect(self.start_transfer)
        self.folderButton.clicked.connect(self.choose_folder)
        self.folderBox.textChanged.connect(self.get_data)

    def worker_data_callback(self, data):
        global tabnum
        

        # Update console 
        self.transferw.console.setPlainText(self.transferw.console.toPlainText()+data[0])
        
        try:
            tabname = "tab"+str(data[1][0])
            textname = "t"+str(data[1][0])

            textobject = getattr(self.transferw, textname)

            textobject.setPlainText(textobject.toPlainText()+data[1][1])
            if (self.transferw.autoBox.isChecked()):
                textobject.moveCursor(QtGui.QTextCursor.End)
        except Exception as e:
            pass
            
        try:
            data[2]
            makeNewTab = True
        except Exception as e:
            makeNewTab = False
            pass

        if makeNewTab == True:
            name = "tab"+str(tabnum)
            text = "t"+str(tabnum)
            tabobject = TabInit()
            setattr(self.transferw, name, tabobject)
            tabobject = getattr(self.transferw, name)
            self.transferw.jobs.addTab(tabobject, name)
            self.transferw.jobs.setTabText(tabnum, "Job "+str(tabnum))
            tabnum += 1

        try:
            data[3]
            error = True
        except Exception as e:
            error = False
            pass
        
        if error == True:
            self.transferw.errorsbox.setPlainText(self.transferw.errorsbox.toPlainText()+f"Job -> {tabnum}"+data[3])

        # Autoscroll
        if (self.transferw.autoBox.isChecked()):
            self.transferw.console.moveCursor(QtGui.QTextCursor.End)


    def worker_started_callback(self):
        # Disable UI
        self.startButton.setEnabled(False)
        self.urlBox.setEnabled(False)
        self.folderBox.setEnabled(False)
        self.qualityBox.setEnabled(False)
        self.folderButton.setEnabled(False)
        self.startButton.setText("Running...")

    def worker_finished_callback(self):
        # Re Enable UI
        self.startButton.setEnabled(True)
        self.urlBox.setEnabled(True)
        self.folderBox.setEnabled(True)
        self.qualityBox.setEnabled(True)
        self.folderButton.setEnabled(True)
        self.startButton.setText("Update archive!")
        self.transferw.label.setText("Done")
        self.transferw.setWindowTitle("Completed archival")
       
    def start_transfer(self):
        # Save folder to be default next time
        if (self.urlBox.toPlainText() != '' and self.folderBox.text() != ''):
            dirpath = appdirs.user_config_dir("DownTube", "Bigweld")
            Path(dirpath).mkdir(parents = True, exist_ok = True)
            path = dirpath+"/path.txt"
            with open(path, 'w+') as f:
                f.write(self.folderBox.text())
            
            # Start thread
            self._worker.start()
            self.transferw = ArchiveWindow(self)
            self.transferw.show()
        else:
            # Not enough info
            self.errorw = ErrorWindow(self)
            self.errorw.errorText.setText("Please choose an archive folder and at least one channel")
            self.errorw.show()

    def get_data(self):
        global foldpath
        # Attempt to get archive data from previous archive
        try: 
            foldpath = self.folderBox.text()
            text_file = open(foldpath+"/archive.txt", "r")
            self.urlBox.setPlainText(text_file.read())
            text_file.close()
        except:
            pass

    def get_path(self):
        # Attempt to get last path used
        try: 
            dirpath = appdirs.user_config_dir("DownTube", "Bigweld")
            Path(dirpath).mkdir(parents = True, exist_ok = True)
            text_file = open(dirpath+"/path.txt", "r")
            self.folderBox.setText(text_file.read())
            text_file.close()
        except:
            pass

    def choose_folder(self):
        # Pick folder
        name = QtWidgets.QFileDialog.getExistingDirectory(None, 'Select a folder:')
        self.folderBox.setText(name)

    

app = QtWidgets.QApplication(sys.argv)
window = Ui()
app.setStyleSheet(qdarkstyle.load_stylesheet())
app.exec_()
