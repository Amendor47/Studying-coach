import platform
import PyInstaller.__main__

def build():
    sep = ';' if platform.system() == 'Windows' else ':'
    opts = [
        'app.py',
        '--name=coach',
        '--onefile',
        f'--add-data=templates{sep}templates',
        f'--add-data=static{sep}static',
    ]
    PyInstaller.__main__.run(opts)

if __name__ == '__main__':
    build()
