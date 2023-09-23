import sys
import os
from PyQt5 import QtWidgets, uic, QtCore, QtGui
from PyQt5.QtGui import QStandardItemModel, QStandardItem
from concurrent.futures import ThreadPoolExecutor
from subprocess import Popen, PIPE
from pathlib import Path
import qdarkstyle
import appdirs

class ArchiveWorker(QtCore.QThread):
    data = QtCore.pyqtSignal(list)

    def __init__(self, channels, foldpath, quality, parent=None):
        super(ArchiveWorker, self).__init__(parent)
        self.channels = channels
        self.foldpath = foldpath
        self.quality = quality
        self.queue = []  # Initialize the download queue

    def run(self):
        for currentindex, channel in enumerate(self.channels):
            if currentindex > 0:
                self.data.emit(['', '', True])

            # Instead of calling backup directly, add to the download queue
            self.queue.append((channel, currentindex))

        # Start processing the queue
        while self.queue:
            channel, currentindex = self.queue.pop(0)  # Get the first item from the queue
            self.backup(channel, currentindex)

    def backup(self, channel, currentindex):
        global finished
        global window

        window._worker.data.emit([f"Job {str(currentindex)} -> Started archiving: {channel}\n"])
        for path in self.run_command(f"cd {self.foldpath} && yt-dlp -f 'bv*[height<={self.quality[:-1]}]+ba' {channel} -o '%(channel)s/%(title)s.%(ext)s'"):
            resp = path.decode() + "\n"
            if resp[:5] == "ERROR":
                show_error(f"Error in archiving Job {currentindex}", resp)
            else:
                window._worker.data.emit(["", [currentindex, resp]])
        finished += 1
        window._worker.data.emit([f"Job {str(currentindex)} -> Finished archiving: {channel}\n{finished}/{len(self.channels)} archived\n"])

    def run_command(self, command):
        process = Popen(command, stdout=PIPE, shell=True)
        while True:
            line = process.stdout.readline().rstrip()
            if not line:
                break
            yield line

class UI(QtWidgets.QMainWindow):
    def __init__(self):
        super(UI, self).__init__()

        self.fontDB = QtGui.QFontDatabase()
        self.fontDB.addApplicationFont("Assets/font.ttf")
        uic.loadUi('Assets/main.ui', self)
        self.qualityBox.addItems(["1080p","720p","480p","360p","240p","144p"])
        self.get_path()
        self.get_data()

        self.show()

        self._worker = ArchiveWorker([], "", "", self)
        self._worker.started.connect(self.worker_started_callback)
        self._worker.finished.connect(self.worker_finished_callback)
        self._worker.data.connect(self.worker_data_callback)
        
        self.startButton.clicked.connect(self.start_transfer)
        self.folderButton.clicked.connect(self.choose_folder)
        self.folderBox.textChanged.connect(self.get_data)

    def worker_data_callback(self, data):
        self.transferw.console.setPlainText(self.transferw.console.toPlainText() + data[0])

        try:
            tabname = "tab" + str(data[1][0])
            textname = "t" + str(data[1][0])
            textobject = getattr(self.transferw, textname)
            textobject.setPlainText(textobject.toPlainText() + data[1][1])
            if self.transferw.autoBox.isChecked():
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
            name = "tab" + str(tabnum)
            text = "t" + str(tabnum)
            tabobject = TabInit()
            setattr(self.transferw, name, tabobject)
            tabobject = getattr(self.transferw, name)
            self.transferw.jobs.addTab(tabobject, name)
            self.transferw.jobs.setTabText(tabnum, "Job " + str(tabnum))
            tabnum += 1

        try:
            data[3]
            error = True
        except Exception as e:
            error = False
            pass
        
        if error == True:
            self.transferw.errorsbox.setPlainText(self.transferw.errorsbox.toPlainText() + f"Job -> {tabnum}" + data[3])

        if self.transferw.autoBox.isChecked():
            self.transferw.console.moveCursor(QtGui.QTextCursor.End)

    def worker_started_callback(self):
        self.startButton.setEnabled(False)
        self.urlBox.setEnabled(False)
        self.folderBox.setEnabled(False)
        self.qualityBox.setEnabled(False)
        self.folderButton.setEnabled(False)
        self.startButton.setText("Running...")

    def worker_finished_callback(self):
        self.startButton.setEnabled(True)
        self.urlBox.setEnabled(True)
        self.folderBox.setEnabled(True)
        self.qualityBox.setEnabled(True)
        self.folderButton.setEnabled(True)
        self.startButton.setText("Update archive!")
        self.transferw.label.setText("Done")
        self.transferw.setWindowTitle("Completed archival")
       
    def start_transfer(self):
        if self.urlBox.toPlainText() and self.folderBox.text():
            dirpath = appdirs.user_config_dir("DownTube", "Bigweld")
            Path(dirpath).mkdir(parents=True, exist_ok=True)
            path = dirpath + "/path.txt"
            with open(path, 'w+') as f:
                f.write(self.folderBox.text())
            
            # Instead of starting immediately, add to the download queue
            self._worker.channels = self.urlBox.toPlainText().split("\n")
            self._worker.foldpath = self.folderBox.text()
            self._worker.quality = str(self.qualityBox.currentText())
            self.queue.extend([(channel, idx) for idx, channel in enumerate(self._worker.channels)])  # Queue all channels
            self._worker.start()
            self.transferw = ArchiveWindow(self)
            self.transferw.show()
        else:
            show_error("Insufficient Information", "Please choose an archive folder and at least one channel")

    def get_data(self):
        global foldpath
        try: 
            foldpath = self.folderBox.text()
            text_file = open(foldpath + "/archive.txt", "r")
            self.urlBox.setPlainText(text_file.read())
            text_file.close()
        except:
            pass

    def get_path(self):
        try: 
            dirpath = appdirs.user_config_dir("DownTube", "Bigweld")
            Path(dirpath).mkdir(parents=True, exist_ok=True)
            text_file = open(dirpath + "/path.txt", "r")
            self.folderBox.setText(text_file.read())
            text_file.close()
        except:
            pass

    def choose_folder(self):
        name = QtWidgets.QFileDialog.getExistingDirectory(None, 'Select a folder:')
        self.folderBox.setText(name)

def show_error(title, message):
    import tkinter as tk
    from tkinter import messagebox

    root = tk.Tk()
    root.withdraw()
    messagebox.showerror(title, message)

if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    window = UI()
    app.setStyleSheet(qdarkstyle.load_stylesheet())
    app.exec_()
