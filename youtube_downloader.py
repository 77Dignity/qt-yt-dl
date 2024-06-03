import sys
from PyQt5.QtWidgets import (QApplication, QWidget, QVBoxLayout, QPushButton, 
                             QLineEdit, QLabel, QProgressBar, QMessageBox, QFileDialog)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
import yt_dlp
import qdarkstyle
import os

class DownloadThread(QThread):
    progress = pyqtSignal(int)
    finished = pyqtSignal(str)
    error = pyqtSignal(str)
    
    def __init__(self, url, download_dir):
        super().__init__()
        self.url = url
        self.download_dir = download_dir
    
    def run(self):
        ydl_opts = {
            'format': 'bestaudio/best',
            'merge_output_format': 'm4a',
            'addheaders': 'User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3',
            'outtmpl': os.path.join(self.download_dir, '%(title)s.%(ext)s'),
            'postprocessors': [
                {
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'm4a',
                    'preferredquality': '320',
                },
                {
                    'key': 'FFmpegMetadata',
                    'add_metadata': True,
                },
                {
                    'key': 'EmbedThumbnail'
                }
            ],
            'keepvideo': False,
            'download_archive': 'archive.txt',
            'nooverwrites': True,
            'ignoreerrors': True,
            'writethumbnail': True,
            'progress_hooks': [self.hook],
        }
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([self.url])
        except Exception as e:
            self.error.emit(str(e))
    
    def hook(self, d):
        if d['status'] == 'downloading':
            total_bytes = d.get('total_bytes') or d.get('total_bytes_estimate')
            downloaded_bytes = d.get('downloaded_bytes', 0)
            if total_bytes:
                percentage = int(downloaded_bytes / total_bytes * 100)
                self.progress.emit(percentage)
        elif d['status'] in ['finished', 'postprocessing']:
            self.progress.emit(100)
            if d['status'] == 'finished':
                self.finished.emit(d['filename'])

class YouTubeDownloader(QWidget):
    def __init__(self):
        super().__init__()
        self.download_dir = os.getcwd()  # Default download directory
        self.initUI()
        
    def initUI(self):
        self.setWindowTitle('YouTube Downloader')
        self.setGeometry(300, 300, 400, 250)
        
        layout = QVBoxLayout()
        
        self.url_label = QLabel('YouTube URL:', self)
        layout.addWidget(self.url_label)
        
        self.url_input = QLineEdit(self)
        layout.addWidget(self.url_input)
        
        self.dir_button = QPushButton('Choose Download Directory', self)
        self.dir_button.clicked.connect(self.choose_directory)
        layout.addWidget(self.dir_button)
        
        self.download_button = QPushButton('Download', self)
        self.download_button.clicked.connect(self.start_download)
        layout.addWidget(self.download_button)
        
        self.progress_bar = QProgressBar(self)
        self.progress_bar.setAlignment(Qt.AlignCenter)
        self.progress_bar.setFixedHeight(10)  # Slim version of the progress bar
        self.progress_bar.setVisible(False)  # Initially hidden
        layout.addWidget(self.progress_bar)
        
        self.status_label = QLabel('', self)
        layout.addWidget(self.status_label)
        
        self.setLayout(layout)
    
    def choose_directory(self):
        directory = QFileDialog.getExistingDirectory(self, 'Select Download Directory', os.getcwd())
        if directory:
            self.download_dir = directory
    
    def start_download(self):
        url = self.url_input.text()
        if not url:
            self.status_label.setText('Please enter a URL.')
            return
        
        self.download_thread = DownloadThread(url, self.download_dir)
        self.download_thread.progress.connect(self.update_progress)
        self.download_thread.finished.connect(self.download_finished)
        self.download_thread.error.connect(self.download_error)
        self.download_thread.start()
        
        self.progress_bar.setVisible(True)  # Show progress bar when download starts
        self.progress_bar.setValue(0)  # Reset progress bar to 0
        self.status_label.setText('Downloading...')
        self.download_button.setEnabled(False)
    
    def update_progress(self, value):
        self.progress_bar.setValue(value)
    
    def download_finished(self, filename):
        self.status_label.setText(f'Download finished: {filename}')
        self.download_button.setEnabled(True)
        self.progress_bar.setVisible(False)  # Hide progress bar after download
    
    def download_error(self, error_message):
        QMessageBox.critical(self, 'Error', f'Error: {error_message}')
        self.status_label.setText('Error occurred during download.')
        self.download_button.setEnabled(True)
        self.progress_bar.setVisible(False)  # Hide progress bar after error

if __name__ == '__main__':
    app = QApplication(sys.argv)
    app.setStyleSheet(qdarkstyle.load_stylesheet_pyqt5())  # Apply the dark theme
    ex = YouTubeDownloader()
    ex.show()
    sys.exit(app.exec_())
