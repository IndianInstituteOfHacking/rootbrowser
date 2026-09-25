#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════╗
║           ROOT BROWSER v5.0 — FULL FEATURED                  ║
║           Tor (auto) · Privacy · Security Tools · Legal      ║
╚══════════════════════════════════════════════════════════════╝
"""
import sys, os, re, json, time, random, socket, hashlib, sqlite3
import logging, base64, shutil, webbrowser, subprocess, threading
from datetime import datetime
from pathlib import Path
from urllib.parse import quote, urlparse, parse_qs, urlencode, urlunparse
from typing import Optional, Dict, List

from PyQt5.QtCore import Qt, QUrl, QTimer, QThread, QObject, QPoint, pyqtSignal, pyqtSlot
from PyQt5.QtGui import QKeySequence, QFont, QColor, QPalette
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QDialog, QTabWidget,
    QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QToolBar, QStatusBar, QMessageBox, QTextEdit, QProgressBar,
    QShortcut, QMenu, QListWidget, QListWidgetItem, QComboBox,
    QFileDialog, QInputDialog, QDialogButtonBox, QGroupBox,
    QCheckBox, QSplitter, QTreeWidget, QTreeWidgetItem, QSpinBox,
    QSizePolicy, QTableWidget, QTableWidgetItem, QHeaderView
)
from PyQt5.QtWebEngineWidgets import (
    QWebEngineView, QWebEngineProfile, QWebEngineSettings,
    QWebEngineDownloadItem, QWebEnginePage
)
from PyQt5.QtWebEngineCore import QWebEngineUrlRequestInterceptor


# ============================================================
#  LICENSE IMPORT (graceful fallback)
# ============================================================
try:
    from licence import LicenseDialog, show_license, request_acceptance
    LICENSE_AVAILABLE = True
except ImportError:
    LICENSE_AVAILABLE = False
    def show_license(parent=None):
        QMessageBox.information(parent, "License",
            "licence.py not found in the same folder.\n"
            "See LICENSE file for details.")
    def request_acceptance(parent=None):
        return True


# ============================================================
#  CONFIG
# ============================================================
class Config:
    TOR_SOCKS_PORT = 9050
    TOR_CONTROL_PORT = 9051
    MAX_TABS = 15

    # "auto" = Tor mile toh use karo, warna direct
    # True   = sirf Tor (Tor na ho toh error)
    # False  = sirf direct connection
    USE_TOR = "auto"

    TOR_AUTO_START = False
    TOR_EXE_PATH = r"C:\tor\tor.exe"
    _TOR_AVAILABLE = False

    SEARCH_ENGINES = {
        "DuckDuckGo": "https://duckduckgo.com/?q={}",
        "Google": "https://www.google.com/search?q={}",
        "Startpage": "https://www.startpage.com/do/dsearch?query={}",
        "Brave": "https://search.brave.com/search?q={}",
        "SearXNG": "https://searx.be/search?q={}",
        "Yahoo": "https://search.yahoo.com/search?p={}",
        "Bing": "https://www.bing.com/search?q={}",
    }

    ADBLOCK = [
        r"doubleclick\.net", r"googlesyndication\.com",
        r"googleadservices\.com", r"facebook\.com/tr",
        r"analytics\.google\.com", r"googletagmanager\.com",
        r"scorecardresearch\.com", r"outbrain\.com", r"taboola\.com",
        r"quantserve\.com", r"addthis\.com"
    ]

    USER_AGENTS = {
        "Firefox (Win)": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:120.0) Gecko/20100101 Firefox/120.0",
        "Chrome (Win)": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36",
        "Chrome (Linux)": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36",
        "Safari (Mac)": "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_0) AppleWebKit/605.1.15 Safari/605.1.15",
        "Tor Browser": "Mozilla/5.0 (Windows NT 10.0; rv:102.0) Gecko/20100101 Firefox/102.0",
        "Edge (Win)": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0"
    }


# ============================================================
#  SECURITY LEVELS
# ============================================================
class SecurityLevel:
    NO_SAFETY, LOW, MEDIUM, HIGH, HARD, EXTREME = range(6)
    NAMES = {0: "No Safety", 1: "Low", 2: "Medium",
             3: "High", 4: "Hard", 5: "Extreme"}


class SecurityManager:
    def __init__(self, level=SecurityLevel.MEDIUM):
        self.level = level

    def set_level(self, level):
        self.level = level

    def get_js(self):
        p = random.choice(['Win32', 'Linux x86_64', 'MacIntel'])
        c = str(random.randint(2, 16))
        m = str(random.randint(2, 8))
        js = """
(function(){
try{
delete window.RTCPeerConnection;
delete window.webkitRTCPeerConnection;
delete window.mozRTCPeerConnection;
if(navigator.getBattery) delete navigator.getBattery;
if(navigator.getGamepads) delete navigator.getGamepads;
if(navigator.usb) delete navigator.usb;
if(navigator.bluetooth) delete navigator.bluetooth;
if(navigator.serial) delete navigator.serial;
if(navigator.hid) delete navigator.hid;
Object.defineProperty(navigator,'platform',{get:()=>'%s'});
Object.defineProperty(navigator,'hardwareConcurrency',{get:()=>%s});
Object.defineProperty(navigator,'deviceMemory',{get:()=>%s});
Date.prototype.getTimezoneOffset=function(){return 0;};
try{
Object.defineProperty(screen,'width',{get:()=>1920});
Object.defineProperty(screen,'height',{get:()=>1080});
Object.defineProperty(screen,'availWidth',{get:()=>1920});
Object.defineProperty(screen,'availHeight',{get:()=>1040});
}catch(e){}
try{
const gp=WebGLRenderingContext.prototype.getParameter;
WebGLRenderingContext.prototype.getParameter=function(p){
if(p===37445)return'Google Inc.';
if(p===37446)return'ANGLE (Intel)';
return gp.call(this,p);};
}catch(e){}
try{
const o=HTMLCanvasElement.prototype.toDataURL;
HTMLCanvasElement.prototype.toDataURL=function(t){
try{const c=this.getContext('2d');
if(c){const i=c.getImageData(0,0,this.width,this.height);
for(let k=0;k<i.data.length;k+=4)i.data[k]=(i.data[k]+1)%%256;
c.putImageData(i,0,0);}}catch(e){}
return o.apply(this,arguments);};
}catch(e){}
try{
if(window.AudioContext){
const oa=AudioContext.prototype.createAnalyser;
AudioContext.prototype.createAnalyser=function(){
const a=oa.call(this);
const o=a.getFloatFrequencyData.bind(a);
a.getFloatFrequencyData=function(arr){
o(arr);
for(let i=0;i<arr.length;i++)arr[i]+=Math.random()*0.0001;};
return a;};}
}catch(e){}
try{
if(navigator.mediaDevices&&navigator.mediaDevices.enumerateDevices){
navigator.mediaDevices.enumerateDevices=function(){
return Promise.resolve([]);};}
}catch(e){}
}catch(e){}
""" % (p, c, m)

        if self.level >= SecurityLevel.LOW:
            js += """
try{
function cs(){var d={};return{
getItem:function(k){return k in d?d[k]:null;},
setItem:function(k,v){d[k]=String(v);},
removeItem:function(k){delete d[k];},
clear:function(){d={};},
key:function(i){var ks=Object.keys(d);return ks[i]||null;},
get length(){return Object.keys(d).length;}};}
try{var t=localStorage.length;}catch(e){try{window.localStorage=cs();}catch(x){}}
try{var t=sessionStorage.length;}catch(e){try{window.sessionStorage=cs();}catch(x){}}
}catch(e){}
"""

        if self.level >= SecurityLevel.HIGH:
            js += """
try{
if(window.speechSynthesis) delete window.speechSynthesis;
}catch(e){}
"""

        if self.level >= SecurityLevel.EXTREME:
            js += """
try{
const on=performance.now.bind(performance);
performance.now=function(){return on()+Math.random()*0.5;};
}catch(e){}
"""

        js += "})();"
        return js

    def get_block_list(self):
        if self.level <= SecurityLevel.LOW:
            return []
        b = ["doubleclick.net", "googleadservices.com", "googlesyndication.com",
             "facebook.com/tr", "analytics.google.com", "googletagmanager.com"]
        if self.level >= SecurityLevel.HIGH:
            b += ["scorecardresearch.com", "outbrain.com", "taboola.com",
                  "quantserve.com", "addthis.com"]
        if self.level >= SecurityLevel.EXTREME:
            b += ["exelator.com", "nexac.com", "adsrvr.org", "adnxs.com"]
        return b


# ============================================================
#  REQUEST INTERCEPTOR
# ============================================================
class RequestInterceptor(QWebEngineUrlRequestInterceptor):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.blocked_hosts = []

    def interceptRequest(self, info):
        try:
            url = info.requestUrl().toString()
            for h in self.blocked_hosts:
                if h and h in url:
                    info.block(True)
                    return
        except Exception:
            pass


# ============================================================
#  TOR MANAGER (auto-detect)
# ============================================================
class TorManager:
    def __init__(self):
        self.socks_port = Config.TOR_SOCKS_PORT
        self.control_port = Config.TOR_CONTROL_PORT
        self._tor_process = None

    def is_running(self):
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(2)
            r = s.connect_ex(('127.0.0.1', self.socks_port))
            s.close()
            return r == 0
        except Exception:
            return False

    def start_tor(self):
        if self.is_running():
            return True
        exe = getattr(Config, 'TOR_EXE_PATH', '')
        if not exe or not os.path.exists(exe):
            return False
        try:
            creation = 0
            if sys.platform == 'win32':
                creation = subprocess.CREATE_NO_WINDOW
            self._tor_process = subprocess.Popen(
                [exe, '--SocksPort', str(self.socks_port),
                 '--ControlPort', str(self.control_port),
                 '--CookieAuthentication', '1'],
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                creationflags=creation
            )
            for _ in range(30):
                time.sleep(1)
                if self.is_running():
                    return True
            return False
        except Exception:
            return False

    def wait_for_tor(self, timeout=30):
        for _ in range(timeout):
            if self.is_running():
                return True
            time.sleep(1)
        return False

    def renew_circuit(self):
        try:
            from stem import Signal
            from stem.control import Controller
            with Controller.from_port(port=self.control_port) as c:
                c.authenticate()
                c.signal(Signal.NEWNYM)
            return True
        except Exception:
            return False

    def get_circuits(self):
        try:
            from stem.control import Controller
            with Controller.from_port(port=self.control_port) as c:
                c.authenticate()
                return c.get_circuits()
        except Exception:
            return []

    def get_exit_ip(self, timeout=10):
        try:
            import requests
            r = requests.get(
                "https://check.torproject.org/api/ip",
                proxies={'http': f'socks5h://127.0.0.1:{self.socks_port}',
                         'https': f'socks5h://127.0.0.1:{self.socks_port}'},
                timeout=timeout)
            data = r.json()
            return data.get('IP'), data.get('IsTor', False)
        except Exception:
            return None, False

    def stop_tor(self):
        if self._tor_process:
            try:
                self._tor_process.terminate()
            except Exception:
                pass
# ============================================================
#  HASH CRACKER
# ============================================================
class CrackWorker(QThread):
    progress = pyqtSignal(int, int)
    finished = pyqtSignal(str)
    error = pyqtSignal(str)

    def __init__(self, h, t, w):
        super().__init__()
        self.h = h.strip()
        self.t = t
        self.w = w
        self.running = True

    def run(self):
        if not os.path.exists(self.w):
            self.error.emit("Wordlist not found!")
            return
        try:
            with open(self.w, 'r', encoding='latin-1', errors='ignore') as f:
                lines = f.readlines()
            total = len(lines)
            for i, line in enumerate(lines):
                if not self.running:
                    self.finished.emit("Aborted.")
                    return
                word = line.strip()
                if not word:
                    continue
                if i % 100 == 0:
                    self.progress.emit(i, total)
                if self._hash(word) == self.h.lower():
                    self.finished.emit(f"[+] CRACKED!\nHash: {self.h}\nPlain: {word}")
                    self.progress.emit(total, total)
                    return
            self.finished.emit("[-] Not found.")
            self.progress.emit(total, total)
        except Exception as e:
            self.error.emit(str(e))

    def _hash(self, w):
        h = self.t.lower()
        try:
            if h == "md5": return hashlib.md5(w.encode()).hexdigest()
            if h == "sha1": return hashlib.sha1(w.encode()).hexdigest()
            if h == "sha256": return hashlib.sha256(w.encode()).hexdigest()
            if h == "sha512": return hashlib.sha512(w.encode()).hexdigest()
            if h == "ntlm":
                try:
                    from Crypto.Hash import MD4
                    return MD4.new(w.encode('utf-16-le')).hexdigest()
                except ImportError:
                    return None
        except Exception:
            return None
        return None

    def stop(self):
        self.running = False


class HashCrackerDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Hash Cracker")
        self.setMinimumSize(600, 500)
        l = QVBoxLayout()
        l.addWidget(QLabel("Hash:"))
        self.h = QLineEdit()
        l.addWidget(self.h)
        r = QHBoxLayout()
        r.addWidget(QLabel("Type:"))
        self.t = QComboBox()
        self.t.addItems(["MD5", "SHA1", "SHA256", "SHA512", "NTLM"])
        r.addWidget(self.t)
        l.addLayout(r)
        l.addWidget(QLabel("Wordlist:"))
        w = QHBoxLayout()
        self.w = QLineEdit()
        self.w.setReadOnly(True)
        w.addWidget(self.w)
        b = QPushButton("Browse")
        b.clicked.connect(self.browse)
        w.addWidget(b)
        d = QPushButton("Demo")
        d.clicked.connect(self.demo)
        w.addWidget(d)
        l.addLayout(w)
        bl = QHBoxLayout()
        self.s = QPushButton("Start")
        self.s.clicked.connect(self.start)
        bl.addWidget(self.s)
        self.st = QPushButton("Stop")
        self.st.setEnabled(False)
        self.st.clicked.connect(self.stop)
        bl.addWidget(self.st)
        l.addLayout(bl)
        self.p = QProgressBar()
        self.p.setVisible(False)
        l.addWidget(self.p)
        self.o = QTextEdit()
        self.o.setReadOnly(True)
        l.addWidget(self.o)
        cb = QDialogButtonBox(QDialogButtonBox.Close)
        cb.rejected.connect(self.reject)
        l.addWidget(cb)
        self.setLayout(l)
        self.worker = None

    def browse(self):
        p, _ = QFileDialog.getOpenFileName(self, "Wordlist", "", "*.txt")
        if p: self.w.setText(p)

    def demo(self):
        p = os.path.join(os.getcwd(), "demo_wl.txt")
        with open(p, "w") as f:
            f.write("\n".join(["password", "123456", "admin", "test", "hello"]))
        self.w.setText(p)

    def start(self):
        if not self.h.text().strip() or not self.w.text().strip():
            QMessageBox.warning(self, "Error", "Hash aur wordlist do.")
            return
        self.p.setVisible(True)
        self.p.setValue(0)
        self.o.clear()
        self.s.setEnabled(False)
        self.st.setEnabled(True)
        self.worker = CrackWorker(self.h.text(), self.t.currentText(), self.w.text())
        self.worker.progress.connect(self.upd)
        self.worker.finished.connect(self.done)
        self.worker.error.connect(self.err)
        self.worker.start()

    def stop(self):
        if self.worker: self.worker.stop()

    def upd(self, c, t):
        self.p.setMaximum(max(1, t))
        self.p.setValue(c)

    def done(self, m):
        self.o.append(m)
        self.s.setEnabled(True)
        self.st.setEnabled(False)
        self.p.setVisible(False)

    def err(self, e):
        QMessageBox.critical(self, "Error", e)
        self.s.setEnabled(True)
        self.st.setEnabled(False)


# ============================================================
#  SQL SCANNER
# ============================================================
class SqlWorker(QThread):
    progress = pyqtSignal(int, int)
    found = pyqtSignal(str, str, str, str)
    finished = pyqtSignal()
    error = pyqtSignal(str)

    PAYLOADS = ["'", "\"", "')", " OR '1'='1", "' OR 1=1 --",
                "admin' --", "' UNION SELECT NULL--",
                "' AND SLEEP(3)--", "1' OR '1'='1"]

    def __init__(self, u, p, m):
        super().__init__()
        self.u = u
        self.p = p
        self.m = m
        self.running = True

    def run(self):
        try:
            import requests
            total = len(self.p) * len(self.PAYLOADS)
            c = 0
            px = None
            if Config.USE_TOR:
                px = {'http': 'socks5h://127.0.0.1:9050',
                      'https': 'socks5h://127.0.0.1:9050'}
            s = requests.Session()
            if px: s.proxies = px
            for p in self.p:
                for pl in self.PAYLOADS:
                    if not self.running:
                        self.finished.emit()
                        return
                    c += 1
                    self.progress.emit(c, total)
                    try:
                        if self.m == 'GET':
                            parsed = urlparse(self.u)
                            q = parse_qs(parsed.query)
                            if p not in q: continue
                            base = s.get(self.u, timeout=10)
                            nq = q.copy()
                            nq[p] = [pl]
                            inj = urlunparse(parsed._replace(query=urlencode(nq, doseq=True)))
                            r = s.get(inj, timeout=10)
                        else:
                            base = s.post(self.u, data={x: '1' for x in self.p}, timeout=10)
                            d = {x: '1' for x in self.p}
                            d[p] = pl
                            r = s.post(self.u, data=d, timeout=10)
                        sigs = ["sql syntax", "mysql", "postgresql", "syntax error",
                                "unclosed", "sqlexception", "database error"]
                        if any(sig in r.text.lower() for sig in sigs):
                            self.found.emit(p, pl, self.m, "Error-based")
                        elif abs(len(r.content) - len(base.content)) > 200:
                            self.found.emit(p, pl, self.m, "Length diff")
                    except Exception:
                        pass
            self.finished.emit()
        except ImportError:
            self.error.emit("pip install requests")
            self.finished.emit()

    def stop(self):
        self.running = False


class SqlScannerDialog(QDialog):
    def __init__(self, url='', parent=None):
        super().__init__(parent)
        self.setWindowTitle("SQL Scanner")
        self.setMinimumSize(700, 600)
        l = QVBoxLayout()
        l.addWidget(QLabel("Target URL:"))
        self.u = QLineEdit(url)
        l.addWidget(self.u)
        l.addWidget(QLabel("Parameters (comma-separated):"))
        self.p = QLineEdit()
        l.addWidget(self.p)
        t = QHBoxLayout()
        e = QPushButton("Extract")
        e.clicked.connect(self.extract)
        t.addWidget(e)
        t.addWidget(QLabel("Method:"))
        self.m = QComboBox()
        self.m.addItems(["GET", "POST"])
        t.addWidget(self.m)
        l.addLayout(t)
        bl = QHBoxLayout()
        self.s = QPushButton("Start Scan")
        self.s.clicked.connect(self.start)
        bl.addWidget(self.s)
        self.st = QPushButton("Stop")
        self.st.setEnabled(False)
        self.st.clicked.connect(self.stop)
        bl.addWidget(self.st)
        l.addLayout(bl)
        self.pb = QProgressBar()
        self.pb.setVisible(False)
        l.addWidget(self.pb)
        self.o = QTextEdit()
        self.o.setReadOnly(True)
        l.addWidget(self.o)
        cb = QDialogButtonBox(QDialogButtonBox.Close)
        cb.rejected.connect(self.reject)
        l.addWidget(cb)
        self.setLayout(l)
        self.worker = None
        if url: self.extract()

    def extract(self):
        p = urlparse(self.u.text())
        self.p.setText(', '.join(parse_qs(p.query).keys()))

    def start(self):
        u = self.u.text().strip()
        ps = [x.strip() for x in self.p.text().split(',') if x.strip()]
        if not u or not ps:
            QMessageBox.warning(self, "Error", "URL aur params do.")
            return
        self.o.clear()
        self.pb.setVisible(True)
        self.pb.setValue(0)
        self.s.setEnabled(False)
        self.st.setEnabled(True)
        self.worker = SqlWorker(u, ps, self.m.currentText())
        self.worker.progress.connect(self.upd)
        self.worker.found.connect(self.fnd)
        self.worker.finished.connect(self.done)
        self.worker.error.connect(self.err)
        self.worker.start()

    def stop(self):
        if self.worker: self.worker.stop()

    def upd(self, c, t):
        self.pb.setMaximum(max(1, t))
        self.pb.setValue(c)

    def fnd(self, p, pl, m, e):
        self.o.append(f"[VULN] {m} param={p} payload={pl!r} → {e}")

    def done(self):
        self.s.setEnabled(True)
        self.st.setEnabled(False)
        self.pb.setVisible(False)

    def err(self, e):
        QMessageBox.critical(self, "Error", e)
        self.s.setEnabled(True)
        self.st.setEnabled(False)


# ============================================================
#  REQUEST REPEATER
# ============================================================
class ReqWorker(QThread):
    done = pyqtSignal(dict)
    error = pyqtSignal(str)

    def __init__(self, m, u, h, b, f, v):
        super().__init__()
        self.m, self.u, self.h, self.b, self.f, self.v = m, u, h, b, f, v

    def run(self):
        try:
            import requests
            px = None
            if Config.USE_TOR:
                px = {'http': 'socks5h://127.0.0.1:9050',
                      'https': 'socks5h://127.0.0.1:9050'}
            t0 = time.time()
            r = requests.request(self.m, self.u, headers=self.h,
                                 data=self.b or None, proxies=px,
                                 timeout=30, allow_redirects=self.f,
                                 verify=self.v)
            self.done.emit({'code': r.status_code, 'reason': r.reason,
                            'headers': dict(r.headers), 'body': r.text,
                            'time': time.time() - t0, 'size': len(r.content)})
        except Exception as e:
            self.error.emit(str(e))


class RequestRepeaterDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Request Repeater")
        self.setMinimumSize(800, 600)
        l = QVBoxLayout()
        t = QHBoxLayout()
        self.m = QComboBox()
        self.m.addItems(["GET", "POST", "PUT", "DELETE", "PATCH"])
        t.addWidget(self.m)
        self.u = QLineEdit()
        self.u.setPlaceholderText("https://...")
        t.addWidget(self.u)
        s = QPushButton("Send")
        s.clicked.connect(self.send)
        t.addWidget(s)
        l.addLayout(t)
        l.addWidget(QLabel("Headers (key: value per line):"))
        self.h = QTextEdit()
        self.h.setMaximumHeight(80)
        l.addWidget(self.h)
        l.addWidget(QLabel("Body:"))
        self.b = QTextEdit()
        self.b.setMaximumHeight(100)
        l.addWidget(self.b)
        o = QHBoxLayout()
        self.f = QCheckBox("Follow redirects")
        self.f.setChecked(True)
        o.addWidget(self.f)
        self.v = QCheckBox("Verify SSL")
        o.addWidget(self.v)
        l.addLayout(o)
        l.addWidget(QLabel("Response:"))
        self.o = QTextEdit()
        self.o.setReadOnly(True)
        l.addWidget(self.o)
        cb = QDialogButtonBox(QDialogButtonBox.Close)
        cb.rejected.connect(self.reject)
        l.addWidget(cb)
        self.setLayout(l)

    def send(self):
        u = self.u.text().strip()
        if not u: return
        h = {}
        for line in self.h.toPlainText().splitlines():
            if ':' in line:
                k, v = line.split(':', 1)
                h[k.strip()] = v.strip()
        self.o.setPlainText("Sending...")
        self.w = ReqWorker(self.m.currentText(), u, h,
                           self.b.toPlainText(),
                           self.f.isChecked(), self.v.isChecked())
        self.w.done.connect(self.show)
        self.w.error.connect(lambda e: self.o.setPlainText(f"Error: {e}"))
        self.w.start()

    def show(self, r):
        h = "\n".join(f"{k}: {v}" for k, v in r['headers'].items())
        self.o.setPlainText(
            f"Status: {r['code']} {r['reason']}\n"
            f"Time: {r['time']:.2f}s\nSize: {r['size']} bytes\n\n"
            f"--- Headers ---\n{h}\n\n--- Body ---\n{r['body']}")


# ============================================================
#  DOM MANIPULATOR
# ============================================================
class DomDialog(QDialog):
    def __init__(self, page, parent=None):
        super().__init__(parent)
        self.page = page
        self.setWindowTitle("DOM Manipulator")
        self.setMinimumSize(800, 600)
        l = QVBoxLayout()
        l.addWidget(QLabel("Edit HTML and click Apply:"))
        self.e = QTextEdit()
        self.e.setAcceptRichText(False)
        l.addWidget(self.e)
        bl = QHBoxLayout()
        a = QPushButton("Apply")
        a.clicked.connect(self.apply)
        bl.addWidget(a)
        r = QPushButton("Reload")
        r.clicked.connect(self.load)
        bl.addWidget(r)
        bl.addStretch()
        c = QPushButton("Close")
        c.clicked.connect(self.reject)
        bl.addWidget(c)
        l.addLayout(bl)
        self.setLayout(l)
        self.load()

    def load(self):
        self.page.toHtml(self.e.setPlainText)

    def apply(self):
        html = self.e.toPlainText()
        js = f"document.open();document.write({json.dumps(html)});document.close();"
        self.page.runJavaScript(js)
        QMessageBox.information(self, "Success", "Applied.")


# ============================================================
#  DARK SEARCH
# ============================================================
class DarkSearchDialog(QDialog):
    def __init__(self, browser=None, parent=None):
        super().__init__(parent)
        self.browser = browser
        self.setWindowTitle("Dark Web Search")
        self.setMinimumSize(800, 600)
        l = QVBoxLayout()
        t = QHBoxLayout()
        t.addWidget(QLabel("Query:"))
        self.q = QLineEdit()
        t.addWidget(self.q)
        s = QPushButton("Search")
        s.clicked.connect(self.start)
        t.addWidget(s)
        l.addLayout(t)
        self.o = QTextEdit()
        self.o.setReadOnly(True)
        l.addWidget(self.o)
        cb = QDialogButtonBox(QDialogButtonBox.Close)
        cb.rejected.connect(self.reject)
        l.addWidget(cb)
        self.setLayout(l)

    def start(self):
        q = self.q.text().strip()
        if not q: return
        self.o.clear()
        self.o.append(f"Searching '{q}'...")
        def run():
            try:
                import requests
                px = None
                if Config.USE_TOR:
                    px = {'http': 'socks5h://127.0.0.1:9050',
                          'https': 'socks5h://127.0.0.1:9050'}
                r = requests.get(f"https://ahmia.fi/search/?q={quote(q)}",
                                 proxies=px, timeout=20)
                self.o.append(f"Status: {r.status_code}")
                try:
                    from bs4 import BeautifulSoup
                    soup = BeautifulSoup(r.text, 'html.parser')
                    for res in soup.select('li.result')[:20]:
                        a = res.select_one('h4 a')
                        if a:
                            self.o.append(f"• {a.get_text(strip=True)}\n  {a.get('href')}")
                except ImportError:
                    self.o.append(f"HTML: {len(r.text)} chars")
            except Exception as e:
                self.o.append(f"Error: {e}")
        threading.Thread(target=run, daemon=True).start()


# ============================================================
#  CERT VIEWER
# ============================================================
class CertDialog(QDialog):
    def __init__(self, hostname=None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Certificate Viewer")
        self.setMinimumSize(700, 500)
        l = QVBoxLayout()
        t = QHBoxLayout()
        t.addWidget(QLabel("Hostname:"))
        self.h = QLineEdit(hostname or "")
        t.addWidget(self.h)
        f = QPushButton("Fetch")
        f.clicked.connect(self.fetch)
        t.addWidget(f)
        l.addLayout(t)
        self.tree = QTreeWidget()
        self.tree.setHeaderLabels(["Field", "Value"])
        self.tree.setColumnWidth(0, 200)
        l.addWidget(self.tree)
        cb = QDialogButtonBox(QDialogButtonBox.Close)
        cb.rejected.connect(self.reject)
        l.addWidget(cb)
        self.setLayout(l)

    def fetch(self):
        h = self.h.text().strip()
        if not h: return
        self.tree.clear()
        try:
            import ssl
            ctx = ssl.create_default_context()
            with socket.create_connection((h, 443), timeout=8) as s:
                with ctx.wrap_socket(s, server_hostname=h) as ss:
                    c = ss.getpeercert()
                    if c:
                        for k, v in c.items():
                            i = QTreeWidgetItem(self.tree)
                            i.setText(0, str(k))
                            i.setText(1, str(v))
        except Exception as e:
            i = QTreeWidgetItem(self.tree)
            i.setText(0, "Error")
            i.setText(1, str(e))


# ============================================================
#  JS CONSOLE
# ============================================================
class JsConsole(QDialog):
    def __init__(self, browser, parent=None):
        super().__init__(parent)
        self.browser = browser
        self.setWindowTitle("JS Console")
        self.setMinimumSize(700, 500)
        l = QVBoxLayout()
        self.o = QTextEdit()
        self.o.setReadOnly(True)
        l.addWidget(self.o)
        t = QHBoxLayout()
        t.addWidget(QLabel(">"))
        self.i = QLineEdit()
        self.i.returnPressed.connect(self.run)
        t.addWidget(self.i)
        l.addLayout(t)
        self.setLayout(l)
        self.o.append("JS Console Ready")

    def run(self):
        c = self.i.text().strip()
        if not c: return
        self.i.clear()
        self.o.append(f"\n> {c}")
        w = self.browser.tabs.currentWidget()
        if isinstance(w, QWebEngineView):
            w.page().runJavaScript(c, self.show)
        else:
            self.show("No page")

    def show(self, r):
        if r is not None:
            self.o.append(f"← {repr(r)}")


# ============================================================
#  PYTHON CONSOLE
# ============================================================
class PyConsole(QDialog):
    def __init__(self, browser, parent=None):
        super().__init__(parent)
        self.browser = browser
        self.setWindowTitle("Python Console")
        self.resize(700, 500)
        l = QVBoxLayout()
        self.o = QTextEdit()
        self.o.setReadOnly(True)
        self.i = QLineEdit()
        self.i.returnPressed.connect(self.run)
        l.addWidget(self.o)
        l.addWidget(self.i)
        self.setLayout(l)
        self.o.append("Python Console Ready\n")

    def run(self):
        c = self.i.text()
        self.i.clear()
        self.o.append(f">>> {c}")
        try:
            ns = {"browser": self.browser, "app": QApplication.instance()}
            try:
                r = eval(c, {}, ns)
                if r is not None: self.o.append(str(r))
            except SyntaxError:
                exec(c, {}, ns)
        except Exception as e:
            self.o.append(f"Error: {e}")


# ============================================================
#  COOKIE EDITOR
# ============================================================
class CookieEditor(QDialog):
    def __init__(self, profile, parent=None):
        super().__init__(parent)
        self.profile = profile
        self.setWindowTitle("Cookie Editor")
        self.setMinimumSize(600, 400)
        l = QVBoxLayout()
        self.list = QListWidget()
        l.addWidget(self.list)
        bl = QHBoxLayout()
        a = QPushButton("Add")
        a.clicked.connect(self.add)
        bl.addWidget(a)
        d = QPushButton("Delete")
        d.clicked.connect(self.delete)
        bl.addWidget(d)
        c = QPushButton("Clear All")
        c.clicked.connect(self.clear)
        bl.addWidget(c)
        l.addLayout(bl)
        cb = QDialogButtonBox(QDialogButtonBox.Close)
        cb.rejected.connect(self.reject)
        l.addWidget(cb)
        self.setLayout(l)
        self.list.addItem("(Cookies clear on close — NoPersistentCookies)")

    def add(self):
        n, ok = QInputDialog.getText(self, "Cookie", "Name=Value:")
        if ok and n:
            self.list.addItem(n)

    def delete(self):
        i = self.list.currentItem()
        if i: self.list.takeItem(self.list.row(i))

    def clear(self):
        try:
            self.profile.cookieStore().deleteAllCookies()
        except Exception:
            pass
        self.list.clear()


# ============================================================
#  JS INJECTOR
# ============================================================
class JsInjector(QDialog):
    def __init__(self, browser, parent=None):
        super().__init__(parent)
        self.browser = browser
        self.setWindowTitle("JS Injector")
        self.resize(600, 400)
        l = QVBoxLayout()
        self.e = QTextEdit()
        l.addWidget(self.e)
        r = QPushButton("Execute")
        r.clicked.connect(self.inject)
        l.addWidget(r)
        self.setLayout(l)

    def inject(self):
        js = self.e.toPlainText()
        w = self.browser.tabs.currentWidget()
        if isinstance(w, QWebEngineView):
            w.page().runJavaScript(js, lambda r: QMessageBox.information(
                self, "Result", f"Returned: {r}" if r else "Done."))


# ============================================================
#  DEVTOOLS
# ============================================================
class DevToolsWindow(QDialog):
    def __init__(self, page, parent=None):
        super().__init__(parent)
        self.setWindowTitle("DevTools")
        self.resize(900, 700)
        l = QVBoxLayout()
        self.v = QWebEngineView()
        self.p = QWebEnginePage(self.v)
        self.v.setPage(self.p)
        try:
            page.setDevToolsPage(self.p)
        except Exception:
            pass
        l.addWidget(self.v)
        self.setLayout(l)


# ============================================================
#  SECURITY SETTINGS
# ============================================================
class SecuritySettingsDialog(QDialog):
    def __init__(self, browser, parent=None):
        super().__init__(parent)
        self.browser = browser
        self.setWindowTitle("Security Settings")
        self.setMinimumSize(500, 400)
        l = QVBoxLayout()

        g1 = QGroupBox("SSL/TLS")
        v1 = QVBoxLayout()
        self.ssl = QCheckBox("Verify SSL Certificates")
        self.ssl.setChecked(True)
        v1.addWidget(self.ssl)
        g1.setLayout(v1)
        l.addWidget(g1)

        g2 = QGroupBox("JavaScript")
        v2 = QVBoxLayout()
        self.js = QCheckBox("Enable JavaScript")
        self.js.setChecked(True)
        v2.addWidget(self.js)
        g2.setLayout(v2)
        l.addWidget(g2)

        g3 = QGroupBox("Content")
        v3 = QVBoxLayout()
        self.imgs = QCheckBox("Load Images")
        self.imgs.setChecked(True)
        v3.addWidget(self.imgs)
        self.plug = QCheckBox("Enable Plugins")
        self.plug.setChecked(False)
        v3.addWidget(self.plug)
        g3.setLayout(v3)
        l.addWidget(g3)

        g4 = QGroupBox("Tor")
        v4 = QVBoxLayout()
        self.tor = QCheckBox("Use Tor Proxy (auto-detect on startup)")
        self.tor.setChecked(Config.USE_TOR is True)
        v4.addWidget(self.tor)
        g4.setLayout(v4)
        l.addWidget(g4)

        s = QPushButton("Save")
        s.clicked.connect(self.save)
        l.addWidget(s)
        self.setLayout(l)

    def save(self):
        Config.USE_TOR = self.tor.isChecked()
        QMessageBox.information(self, "Saved",
                                "Settings saved. Restart for Tor change.")
        self.accept()


# ============================================================
#  BOOKMARKS / HISTORY DIALOGS
# ============================================================
class BookmarksDialog(QDialog):
    def __init__(self, bookmarks, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Bookmarks")
        self.setMinimumSize(400, 300)
        l = QVBoxLayout()
        lw = QListWidget()
        for b in bookmarks:
            lw.addItem(f"{b['title']}  -  {b['url']}")
        l.addWidget(lw)
        cb = QDialogButtonBox(QDialogButtonBox.Close)
        cb.rejected.connect(self.reject)
        l.addWidget(cb)
        self.setLayout(l)


class HistoryDialog(QDialog):
    def __init__(self, history, parent=None):
        super().__init__(parent)
        self.setWindowTitle("History")
        self.setMinimumSize(500, 300)
        l = QVBoxLayout()
        lw = QListWidget()
        for h in history:
            lw.addItem(f"[{h['time']}] {h['title']}  -  {h['url']}")
        l.addWidget(lw)
        cb = QDialogButtonBox(QDialogButtonBox.Close)
        cb.rejected.connect(self.reject)
        l.addWidget(cb)
        self.setLayout(l)
# ============================================================
#  MAIN BROWSER WINDOW
# ============================================================
class Browser(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Root Browser v5.0 — Full Featured")
        self.setGeometry(100, 100, 1400, 900)

        self.tor_available = Config._TOR_AVAILABLE
        self.current_search_engine = "DuckDuckGo"
        self.current_ua = "Firefox (Win)"
        self.adblock_enabled = True
        self.security_manager = SecurityManager()
        self.tor = TorManager()
        self.bookmarks = []
        self.history = []

        self._apply_theme()

        self.interceptor = RequestInterceptor()
        self.profile = QWebEngineProfile(self)
        self.profile.setHttpCacheType(QWebEngineProfile.NoCache)
        self.profile.setPersistentCookiesPolicy(QWebEngineProfile.NoPersistentCookies)
        self.profile.setHttpUserAgent(Config.USER_AGENTS[self.current_ua])
        self.profile.setUrlRequestInterceptor(self.interceptor)
        self.profile.downloadRequested.connect(self.on_download)
        self.profile.setSpellCheckEnabled(False)

        self._apply_block_list()

        self.tabs = QTabWidget()
        self.tabs.setTabsClosable(True)
        self.tabs.tabCloseRequested.connect(self.close_tab)
        self.tabs.setContextMenuPolicy(Qt.CustomContextMenu)
        self.tabs.customContextMenuRequested.connect(self.tab_menu)
        self.tabs.currentChanged.connect(self.on_tab_changed)

        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Ready")

        # Tor mode indicator
        self.mode_label = QLabel()
        if Config.USE_TOR:
            self.mode_label.setText(" 🟢 Tor ")
            self.mode_label.setStyleSheet(
                "color:#4ade80; background:#1e1e32; padding:3px 8px; "
                "border-radius:6px; font-weight:bold;")
        else:
            self.mode_label.setText(" 🟡 Direct ")
            self.mode_label.setStyleSheet(
                "color:#fbbf24; background:#1e1e32; padding:3px 8px; "
                "border-radius:6px; font-weight:bold;")
        self.status_bar.addPermanentWidget(self.mode_label)

        self.progress_bar = QProgressBar()
        self.progress_bar.setMaximumWidth(200)
        self.progress_bar.setVisible(False)
        self.progress_bar.setRange(0, 100)
        self.status_bar.addPermanentWidget(self.progress_bar)

        self._setup_shortcuts()
        self._setup_ui()

        self.new_tab()

        self.tor_timer = QTimer()
        self.tor_timer.timeout.connect(self.renew_tor)
        self.tor_timer.start(600000)

    def _apply_theme(self):
        p = QPalette()
        p.setColor(QPalette.Window, QColor(15, 15, 26))
        p.setColor(QPalette.WindowText, QColor(226, 232, 240))
        p.setColor(QPalette.Base, QColor(30, 30, 50))
        p.setColor(QPalette.Text, QColor(226, 232, 240))
        p.setColor(QPalette.Button, QColor(45, 45, 75))
        p.setColor(QPalette.ButtonText, QColor(226, 232, 240))
        p.setColor(QPalette.Highlight, QColor(99, 102, 241))
        p.setColor(QPalette.HighlightedText, Qt.white)
        QApplication.setPalette(p)

        self.setStyleSheet("""
            QMainWindow { background-color: #0f0f1a; }
            QToolBar { background-color: #1e1e32;
                border-bottom: 1px solid #3f3f5e; spacing: 6px; padding: 6px; }
            QStatusBar { background-color: #16162a; color: #94a3b8;
                border-top: 1px solid #3f3f5e; }
            QLineEdit { background-color: #2d2d4a; color: #f1f5f9;
                border: 1px solid #4b4b6e; border-radius: 14px;
                padding: 7px 14px; font: 13px 'Segoe UI'; }
            QLineEdit:focus { border-color: #6366f1; }
            QPushButton { background-color: #3a3a5e; color: #f1f5f9;
                border: 1px solid #4b4b6e; border-radius: 8px;
                padding: 6px 14px; font: 12px 'Segoe UI'; }
            QPushButton:hover { background-color: #4b4b6e; }
            QPushButton:pressed { background-color: #6366f1; }
            QTabWidget::pane { border: 1px solid #3f3f5e; }
            QTabBar::tab { background-color: #1e1e32; color: #94a3b8;
                padding: 7px 18px; margin-right: 2px;
                border-radius: 8px 8px 0 0; }
            QTabBar::tab:selected { background-color: #0f0f1a;
                color: white; border-bottom: 2px solid #6366f1; }
            QComboBox { background-color: #2d2d4a; color: #f1f5f9;
                border: 1px solid #4b4b6e; border-radius: 6px;
                padding: 5px 10px; }
            QComboBox QAbstractItemView { background-color: #2d2d4a;
                color: #f1f5f9; selection-background-color: #6366f1; }
            QMenu { background-color: #1e1e32; color: #e2e8f0;
                border: 1px solid #4b4b6e; border-radius: 6px; padding: 4px; }
            QMenu::item { padding: 6px 20px; border-radius: 4px; }
            QMenu::item:selected { background-color: #6366f1; }
            QProgressBar { border: none; border-radius: 6px;
                background-color: #2d2d4a; height: 6px; }
            QProgressBar::chunk { background: qlineargradient(x1:0, y1:0,
                x2:1, y2:0, stop:0 #6366f1, stop:1 #3b82f6);
                border-radius: 6px; }
            QListWidget, QTextEdit, QTreeWidget {
                background-color: #1e1e32; color: #e2e8f0;
                border: 1px solid #3f3f5e; border-radius: 6px; }
            QListWidget::item:selected, QTreeWidget::item:selected {
                background-color: #6366f1; }
            QLabel { color: #e2e8f0; }
            QGroupBox { color: #6366f1; border: 1px solid #3f3f5e;
                margin-top: 10px; padding-top: 10px; border-radius: 8px; }
            QGroupBox::title { subcontrol-origin: margin; left: 10px;
                padding: 0 5px; }
            QCheckBox { color: #e2e8f0; spacing: 8px; }
        """)

    def _setup_shortcuts(self):
        QShortcut(QKeySequence("Ctrl+T"), self, lambda: self.new_tab())
        QShortcut(QKeySequence("Ctrl+W"), self, lambda: self.close_tab(self.tabs.currentIndex()))
        QShortcut(QKeySequence("Ctrl+L"), self, lambda: self.url_bar.setFocus())
        QShortcut(QKeySequence("Ctrl+R"), self, self.reload)
        QShortcut(QKeySequence("F5"), self, self.reload)
        QShortcut(QKeySequence("F11"), self, self.fullscreen)
        QShortcut(QKeySequence("Ctrl+Shift+Q"), self, self.panic)
        QShortcut(QKeySequence("Ctrl+Shift+X"), self, self.panic)
        QShortcut(QKeySequence("Ctrl+H"), self, self.show_history)
        QShortcut(QKeySequence("Ctrl+B"), self, self.show_bookmarks)
        QShortcut(QKeySequence("Ctrl+P"), self, self.open_py_console)
        QShortcut(QKeySequence("Ctrl+J"), self, self.open_js_injector)
        QShortcut(QKeySequence("Ctrl+I"), self, self.open_inspector)
        QShortcut(QKeySequence("Ctrl+U"), self, self.view_source)

    def _setup_ui(self):
        tb = QToolBar()
        tb.setMovable(False)
        self.addToolBar(tb)

        back = QPushButton("◀")
        back.setToolTip("Back")
        back.clicked.connect(self.back)
        tb.addWidget(back)

        fwd = QPushButton("▶")
        fwd.setToolTip("Forward")
        fwd.clicked.connect(self.forward)
        tb.addWidget(fwd)

        rel = QPushButton("↻")
        rel.setToolTip("Reload")
        rel.clicked.connect(self.reload)
        tb.addWidget(rel)

        home = QPushButton("🏠")
        home.setToolTip("Home")
        home.clicked.connect(self.home)
        tb.addWidget(home)

        nt = QPushButton("+")
        nt.setToolTip("New Tab (Ctrl+T)")
        nt.clicked.connect(lambda: self.new_tab())
        tb.addWidget(nt)

        sp = QWidget()
        sp.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        tb.addWidget(sp)

        self.url_bar = QLineEdit()
        self.url_bar.setPlaceholderText("Search or type URL...")
        self.url_bar.returnPressed.connect(self.navigate)
        tb.addWidget(self.url_bar)

        sp2 = QWidget()
        sp2.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        tb.addWidget(sp2)

        tb.addSeparator()
        tb.addWidget(QLabel("🔍"))
        self.engine_combo = QComboBox()
        self.engine_combo.addItems(Config.SEARCH_ENGINES.keys())
        self.engine_combo.setCurrentText(self.current_search_engine)
        self.engine_combo.currentTextChanged.connect(self.change_engine)
        tb.addWidget(self.engine_combo)

        tb.addWidget(QLabel("🔒"))
        self.sec_combo = QComboBox()
        self.sec_combo.addItems(SecurityLevel.NAMES.values())
        self.sec_combo.setCurrentText(SecurityLevel.NAMES[self.security_manager.level])
        self.sec_combo.currentTextChanged.connect(self.change_security)
        tb.addWidget(self.sec_combo)

        self.ua_combo = QComboBox()
        self.ua_combo.addItems(Config.USER_AGENTS.keys())
        self.ua_combo.setCurrentText(self.current_ua)
        self.ua_combo.currentTextChanged.connect(self.change_ua)
        tb.addWidget(self.ua_combo)

        ad = QPushButton("AdBlock")
        ad.setCheckable(True)
        ad.setChecked(True)
        ad.toggled.connect(self.toggle_adblock)
        tb.addWidget(ad)

        notes = QPushButton("Notes")
        notes.clicked.connect(self.open_notes)
        tb.addWidget(notes)

        panic = QPushButton("PANIC")
        panic.setStyleSheet("background-color:#e11d48; color:white; "
                            "font-weight:bold; border-radius:8px; padding:6px 16px;")
        panic.clicked.connect(self.panic)
        tb.addWidget(panic)

        mb = self.menuBar()
        mb.setStyleSheet("""
            QMenuBar { background-color: #1e1e32; color: #e2e8f0;
                border-bottom: 1px solid #3f3f5e; }
            QMenuBar::item { padding: 6px 12px; }
            QMenuBar::item:selected { background-color: #6366f1; }
        """)

        fm = mb.addMenu("File")
        fm.addAction("New Tab", lambda: self.new_tab(), "Ctrl+T")
        fm.addSeparator()
        fm.addAction("Exit", self.close, "Ctrl+Q")

        em = mb.addMenu("Edit")
        em.addAction("Copy URL", lambda: QApplication.clipboard().setText(self.url_bar.text()))
        em.addAction("Bookmarks", self.show_bookmarks, "Ctrl+B")
        em.addAction("History", self.show_history, "Ctrl+H")

        vm = mb.addMenu("View")
        vm.addAction("View Source", self.view_source, "Ctrl+U")
        vm.addAction("DevTools", self.open_inspector, "Ctrl+I")
        vm.addAction("JS Console", self.open_js_console)
        vm.addAction("Fullscreen", self.fullscreen, "F11")

        sm = mb.addMenu("Security")
        sm.addAction("Certificate Viewer", self.open_cert)
        sm.addAction("Security Settings", self.open_sec_settings)
        sm.addAction("Cookie Editor", self.open_cookies)
        sm.addAction("Tor Circuits", self.show_circuits)
        sm.addAction("Renew Tor Circuit", self.renew_tor)

        tm = mb.addMenu("Tools")
        tm.addAction("Hash Cracker", self.open_hash)
        tm.addAction("SQLi Scanner", self.open_sql)
        tm.addAction("Request Repeater", self.open_repeater)
        tm.addAction("DOM Manipulator", self.open_dom)
        tm.addAction("Dark Web Search", self.open_dark)
        tm.addSeparator()
        tm.addAction("JS Injector", self.open_js_injector)
        tm.addAction("Python Console", self.open_py_console, "Ctrl+P")

        hm = mb.addMenu("Help")
        hm.addAction("⚖️ License & Legal Disclaimer", self.show_license_dialog)
        hm.addAction("About", lambda: QMessageBox.about(
            self, "Root Browser v5.0",
            "Root Browser v5.0 - Full Featured\n\n"
            "Tor (auto) · Anti-Fingerprint · Hash Cracker · SQL Scanner\n"
            "Request Repeater · DOM Manipulator · Dark Search\n"
            "Cert Viewer · JS/Python Console · Cookie Editor · etc.\n\n"
            "⚠️ For legal security research only."))

        central = QWidget()
        cl = QVBoxLayout(central)
        cl.setContentsMargins(0, 0, 0, 0)
        cl.setSpacing(0)
        cl.addWidget(self.tabs)
        self.setCentralWidget(central)

    def _apply_block_list(self):
        base = Config.ADBLOCK if self.adblock_enabled else []
        extra = self.security_manager.get_block_list()
        self.interceptor.blocked_hosts = list(set(base + extra))

    # ---------- Tabs ----------
    def new_tab(self, url=None):
        if self.tabs.count() >= Config.MAX_TABS:
            QMessageBox.warning(self, "Limit", f"Max {Config.MAX_TABS} tabs.")
            return
        v = QWebEngineView()
        p = QWebEnginePage(self.profile, v)
        v.setPage(p)
        s = v.settings()
        s.setAttribute(QWebEngineSettings.JavascriptEnabled, True)
        s.setAttribute(QWebEngineSettings.LocalStorageEnabled, True)
        s.setAttribute(QWebEngineSettings.JavascriptCanOpenWindows, True)
        s.setAttribute(QWebEngineSettings.FullScreenSupportEnabled, True)
        s.setAttribute(QWebEngineSettings.ScrollAnimatorEnabled, True)
        s.setAttribute(QWebEngineSettings.PluginsEnabled, False)
        s.setAttribute(QWebEngineSettings.ErrorPageEnabled, True)
        s.setAttribute(QWebEngineSettings.WebRTCPublicInterfacesOnly, True)
        s.setAttribute(QWebEngineSettings.DnsPrefetchEnabled, False)
        s.setAttribute(QWebEngineSettings.HyperlinkAuditingEnabled, False)
        s.setAttribute(QWebEngineSettings.LocalContentCanAccessRemoteUrls, False)
        s.setAttribute(QWebEngineSettings.LocalContentCanAccessFileUrls, False)

        v.setContextMenuPolicy(Qt.CustomContextMenu)
        v.customContextMenuRequested.connect(lambda pos, vv=v: self.page_menu(vv, pos))
        v.urlChanged.connect(lambda u, vv=v: self.on_url(vv, u))
        v.titleChanged.connect(lambda t, vv=v: self.on_title(vv, t))
        v.loadProgress.connect(lambda pr, vv=v: self.on_progress(vv, pr))

        idx = self.tabs.addTab(v, "New Tab")
        self.tabs.setCurrentIndex(idx)
        if url:
            v.setUrl(QUrl(url))
        else:
            v.setHtml(self._home_html())
        return v

    def close_tab(self, idx):
        if self.tabs.count() > 1:
            w = self.tabs.widget(idx)
            self.tabs.removeTab(idx)
            if w: w.deleteLater()

    def on_tab_changed(self, i):
        w = self.tabs.widget(i)
        if isinstance(w, QWebEngineView):
            self.url_bar.setText(w.url().toString())

    def on_title(self, v, t):
        i = self.tabs.indexOf(v)
        if i >= 0 and t:
            self.tabs.setTabText(i, t[:25])

    def on_url(self, v, u):
        if self.tabs.currentWidget() == v:
            self.url_bar.setText(u.toString())
            self.status_bar.showMessage(f"Loaded: {u.toString()}", 3000)
        try:
            if v.title():
                self.history.append({"title": v.title(), "url": u.toString(),
                                     "time": datetime.now().strftime("%H:%M:%S")})
        except Exception:
            pass

    def on_progress(self, v, p):
        if v == self.tabs.currentWidget():
            if p < 100:
                self.progress_bar.setVisible(True)
                self.progress_bar.setValue(p)
            else:
                self.progress_bar.setVisible(False)

    # ---------- Navigation ----------
    def _cur(self):
        w = self.tabs.currentWidget()
        return w if isinstance(w, QWebEngineView) else None

    def navigate(self):
        t = self.url_bar.text().strip()
        if not t: return
        w = self._cur()
        if not w: return
        is_url = (' ' not in t) and (
            t.startswith(('http://', 'https://', 'about:', 'file://')) or
            ('.' in t and not t.startswith(('?', '#'))))
        if is_url:
            if not t.startswith(('http://', 'https://', 'about:', 'file://')):
                t = 'https://' + t
            w.setUrl(QUrl(t))
        else:
            e = Config.SEARCH_ENGINES.get(self.current_search_engine,
                                          Config.SEARCH_ENGINES["DuckDuckGo"])
            w.setUrl(QUrl(e.format(quote(t))))

    def back(self):
        w = self._cur()
        if w: w.back()

    def forward(self):
        w = self._cur()
        if w: w.forward()

    def reload(self):
        w = self._cur()
        if w: w.reload()

    def home(self):
        w = self._cur()
        if w: w.setHtml(self._home_html())

    def change_engine(self, n):
        self.current_search_engine = n
        self.status_bar.showMessage(f"Engine: {n}", 2000)

    def change_ua(self, n):
        self.current_ua = n
        self.profile.setHttpUserAgent(Config.USER_AGENTS.get(n))

    def change_security(self, name):
        try:
            lvl = [k for k, v in SecurityLevel.NAMES.items() if v == name][0]
        except IndexError:
            return
        self.security_manager.set_level(lvl)
        self._apply_block_list()
        js = self.security_manager.get_js()
        for i in range(self.tabs.count()):
            w = self.tabs.widget(i)
            if isinstance(w, QWebEngineView):
                try: w.page().runJavaScript(js)
                except Exception: pass
        self.status_bar.showMessage(f"Security: {name}", 3000)

    def toggle_adblock(self, c):
        self.adblock_enabled = c
        self._apply_block_list()

    def fullscreen(self):
        if self.isFullScreen(): self.showNormal()
        else: self.showFullScreen()

    def panic(self):
        if QMessageBox.question(self, "PANIC", "Exit browser?",
                                QMessageBox.Yes | QMessageBox.No) == QMessageBox.Yes:
            QApplication.quit()

    def renew_tor(self):
        if Config.USE_TOR:
            self.tor.renew_circuit()

    def show_circuits(self):
        cs = self.tor.get_circuits()
        if not cs:
            QMessageBox.information(self, "Circuits", "No info. Need stem + Tor.")
            return
        QMessageBox.information(self, "Circuits",
                                "\n".join(f"{c.id} {c.status}" for c in cs))

    def show_license_dialog(self):
        show_license(self)

    # ---------- Home HTML ----------
    def _home_html(self):
        e = Config.SEARCH_ENGINES.get(self.current_search_engine,
                                      Config.SEARCH_ENGINES["DuckDuckGo"])
        mode = "🟢 Tor Mode" if Config.USE_TOR else "🟡 Direct Mode"
        return f"""<!DOCTYPE html>
<html><head><meta charset="utf-8"><title>New Tab</title>
<style>
body{{background:linear-gradient(180deg,#0f0f1a,#1a1a2e);color:#e2e8f0;
font-family:'Segoe UI',sans-serif;display:flex;justify-content:center;
align-items:center;height:100vh;margin:0;}}
.c{{text-align:center;max-width:600px;background:#1e1e32;
border:1px solid #3f3f5e;border-radius:16px;padding:40px;}}
h2{{color:#6366f1;margin-bottom:20px;}}
p{{color:#94a3b8;font-size:14px;}}
.badge{{display:inline-block;padding:4px 12px;background:#0f0f1a;
border-radius:12px;font-size:13px;margin-bottom:14px;color:#cbd5e1;}}
.s{{display:flex;gap:10px;margin-top:20px;}}
.i{{flex:1;padding:14px 22px;background:#2d2d4a;border:1px solid #4b4b6e;
border-radius:30px;color:#f1f5f9;font-size:16px;outline:none;}}
.i:focus{{border-color:#6366f1;}}
.b{{padding:14px 28px;background:linear-gradient(90deg,#6366f1,#3b82f6);
color:white;border:none;border-radius:30px;font-size:16px;cursor:pointer;
font-weight:bold;}}
</style></head><body>
<div class="c">
<h2>Root Browser v5.0</h2>
<div class="badge">{mode}</div>
<p>Search or type a URL</p>
<div class="s">
<input id="q" class="i" placeholder="Search or URL..." autofocus>
<button class="b" onclick="go()">Search</button>
</div></div>
<script>
const E="{e}";
function go(){{var q=document.getElementById('q').value.trim();if(!q)return;
var u=q.indexOf(' ')===-1&&(q.startsWith('http')||(q.indexOf('.')!==-1&&!q.startsWith('?')));
if(u){{if(!q.startsWith('http://')&&!q.startsWith('https://'))q='https://'+q;
window.location.href=q;}}else{{window.location.href=E+encodeURIComponent(q);}}}}
document.getElementById('q').addEventListener('keypress',function(e){{
if(e.key==='Enter')go();}});
</script></body></html>"""

    # ---------- Right-click page menu ----------
    def page_menu(self, v, pos):
        m = QMenu(v)
        m.addAction("◀ Back", v.back)
        m.addAction("▶ Forward", v.forward)
        m.addAction("↻ Reload", v.reload)
        m.addSeparator()
        m.addAction("Copy", lambda: v.page().triggerAction(QWebEnginePage.Copy))
        m.addAction("Paste", lambda: v.page().triggerAction(QWebEnginePage.Paste))
        m.addAction("Select All", lambda: v.page().triggerAction(QWebEnginePage.SelectAll))
        m.addSeparator()
        m.addAction("🔍 Copy as cURL", lambda: self.copy_curl(v))
        m.addAction("🔐 Hash Cracker", self.open_hash)
        m.addAction("💉 SQLi Scanner", self.open_sql)
        m.addAction("🔁 Request Repeater", self.open_repeater)
        m.addAction("🧩 DOM Manipulator", lambda: self.open_dom(v))
        m.addAction("🌐 Dark Web Search", self.open_dark)
        m.addSeparator()
        m.addAction("🍪 View Cookies", lambda: self.show_cookies(v))
        m.addAction("📷 Screenshot", lambda: self.screenshot(v))
        m.addAction("💾 Save Page As HTML", lambda: self.save_page(v))
        m.addSeparator()
        m.addAction("🔗 Extract All Links", lambda: self.extract_links(v))
        m.addAction("🖼 Extract All Images", lambda: self.extract_images(v))
        m.addAction("💬 View HTML Comments", lambda: self.view_comments(v))
        m.addSeparator()
        host = v.url().host()
        if host and host in self.interceptor.blocked_hosts:
            m.addAction("🔓 Unblock This Domain", lambda: self.unblock_host(host))
        else:
            m.addAction("🚫 Block This Domain", lambda: self.block_host(host))
        m.addAction("🤖 Check robots.txt", lambda: self.open_robots(v))
        m.addAction("🌍 Open in System Browser",
                    lambda: webbrowser.open(v.url().toString()))
        m.addAction("🧅 Open in Tor Browser", lambda: self.open_tor_browser(v))
        m.addSeparator()
        m.addAction("📝 Generate Wordlist", lambda: self.generate_wordlist(v))
        m.addAction("🌓 Toggle Dark Mode", lambda: self.toggle_dark(v))
        m.addSeparator()
        m.addAction("🔧 Inspect Element",
                    lambda: self.open_inspector_for(v.page()))
        m.addAction("➕ Open in New Tab", lambda: self.new_tab(v.url().toString()))
        m.addSeparator()
        m.addAction("⚖️  License & Legal Disclaimer", self.show_license_dialog)
        m.exec_(v.mapToGlobal(pos))

    def tab_menu(self, pos):
        m = QMenu()
        m.addAction("New Tab", lambda: self.new_tab())
        m.addAction("Reload", self.reload)
        m.addAction("Close Tab", lambda: self.close_tab(self.tabs.currentIndex()))
        m.addSeparator()
        m.addAction("⚖️  License & Legal Disclaimer", self.show_license_dialog)
        m.exec_(self.tabs.mapToGlobal(pos))

    # ---------- Tool implementations ----------
    def copy_curl(self, v):
        u = v.url().toString()
        ua = self.profile.httpUserAgent()
        if Config.USE_TOR:
            c = f'curl -x socks5h://127.0.0.1:{Config.TOR_SOCKS_PORT} -H "User-Agent: {ua}" "{u}"'
        else:
            c = f'curl -H "User-Agent: {ua}" "{u}"'
        QApplication.clipboard().setText(c)
        self.status_bar.showMessage("cURL copied", 3000)

    def show_cookies(self, v):
        v.page().runJavaScript("document.cookie",
                               lambda c: self._text_dialog("Cookies", c or "No cookies"))

    def screenshot(self, v):
        p = v.grab()
        path, _ = QFileDialog.getSaveFileName(self, "Save", "screenshot.png", "PNG (*.png)")
        if path:
            p.save(path)
            self.status_bar.showMessage(f"Saved: {path}", 3000)

    def save_page(self, v):
        v.page().toHtml(self._save_html)

    def _save_html(self, h):
        path, _ = QFileDialog.getSaveFileName(self, "Save", "page.html", "HTML (*.html)")
        if path:
            with open(path, 'w', encoding='utf-8') as f:
                f.write(h)
            self.status_bar.showMessage(f"Saved: {path}", 3000)

    def extract_links(self, v):
        v.page().runJavaScript(
            "Array.from(document.querySelectorAll('a[href]')).map(a=>a.href);",
            lambda links: self._list_dialog("Links", links))

    def extract_images(self, v):
        v.page().runJavaScript(
            "Array.from(document.querySelectorAll('img[src]')).map(i=>i.src);",
            lambda imgs: self._list_dialog("Images", imgs))

    def view_comments(self, v):
        v.page().toHtml(self._extract_comments)

    def _extract_comments(self, h):
        c = re.findall(r'<!--(.*?)-->', h, re.DOTALL)
        self._text_dialog("HTML Comments", "\n\n".join(c) if c else "None")

    def block_host(self, h):
        if h and h not in self.interceptor.blocked_hosts:
            self.interceptor.blocked_hosts.append(h)
            QMessageBox.information(self, "Blocked", f"{h} blocked")
            self.reload()

    def unblock_host(self, h):
        if h and h in self.interceptor.blocked_hosts:
            self.interceptor.blocked_hosts.remove(h)
            QMessageBox.information(self, "Unblocked", f"{h} unblocked")
            self.reload()

    def open_robots(self, v):
        h = v.url().host()
        if h: self.new_tab(f"https://{h}/robots.txt")

    def open_tor_browser(self, v):
        u = v.url().toString()
        if not u.startswith("http"): return
        for c in ["torbrowser-launcher", "tor-browser", "tor-browser-sandbox"]:
            if shutil.which(c):
                subprocess.Popen([c, u])
                return
        QMessageBox.information(self, "Tor Browser", "Not installed")

    def generate_wordlist(self, v):
        v.page().runJavaScript("document.body.innerText", self._save_wordlist)

    def _save_wordlist(self, text):
        if not text: return
        words = sorted(set(re.findall(r'\b\w+\b', text.lower())))
        p, _ = QFileDialog.getSaveFileName(self, "Save Wordlist", "wordlist.txt", "*.txt")
        if p:
            with open(p, 'w', encoding='utf-8') as f:
                f.write('\n'.join(words))
            self.status_bar.showMessage(f"Wordlist saved ({len(words)})", 4000)

    def toggle_dark(self, v):
        css = ("html{filter:invert(1) hue-rotate(180deg)!important;"
               "background:#000!important;}"
               "img,video,canvas,iframe,embed{"
               "filter:invert(1) hue-rotate(180deg)!important;}")
        js = f"var s=document.getElementById('dm');if(s){{s.remove();}}else{{" \
             f"var e=document.createElement('style');e.id='dm';" \
             f"e.textContent=`{css}`;document.head.appendChild(e);}}"
        v.page().runJavaScript(js)

    def view_source(self):
        v = self._cur()
        if v:
            v.page().toHtml(lambda h: self._text_dialog("Source", h))

    def open_inspector(self):
        self.open_inspector_for(None)

    def open_inspector_for(self, page):
        if page is None:
            v = self._cur()
            page = v.page() if v else None
        if page:
            d = DevToolsWindow(page, self)
            d.show()
            if not hasattr(self, 'devtools'):
                self.devtools = []
            self.devtools.append(d)

    def open_hash(self):
        HashCrackerDialog(self).exec_()

    def open_sql(self):
        v = self._cur()
        u = v.url().toString() if v else ""
        SqlScannerDialog(u, self).exec_()

    def open_repeater(self):
        RequestRepeaterDialog(self).exec_()

    def open_dom(self, v=None):
        if v is None:
            v = self._cur()
        if v:
            DomDialog(v.page(), self).exec_()

    def open_dark(self):
        DarkSearchDialog(self, self).exec_()

    def open_cert(self):
        v = self._cur()
        h = v.url().host() if v else ""
        CertDialog(h, self).exec_()

    def open_sec_settings(self):
        SecuritySettingsDialog(self, self).exec_()

    def open_cookies(self):
        CookieEditor(self.profile, self).exec_()

    def open_js_console(self):
        self.jsc = JsConsole(self)
        self.jsc.show()

    def open_js_injector(self):
        JsInjector(self, self).exec_()

    def open_py_console(self):
        self.pyc = PyConsole(self)
        self.pyc.show()

    def show_bookmarks(self):
        BookmarksDialog(self.bookmarks, self).exec_()

    def show_history(self):
        HistoryDialog(self.history, self).exec_()

    def open_notes(self):
        d = QDialog(self)
        d.setWindowTitle("Notes")
        d.resize(500, 400)
        l = QVBoxLayout()
        l.addWidget(QTextEdit())
        cb = QDialogButtonBox(QDialogButtonBox.Close)
        cb.rejected.connect(d.reject)
        l.addWidget(cb)
        d.setLayout(l)
        d.exec_()

    # ---------- Helpers ----------
    def _text_dialog(self, title, text):
        d = QDialog(self)
        d.setWindowTitle(title)
        d.resize(700, 500)
        l = QVBoxLayout()
        t = QTextEdit()
        t.setPlainText(text)
        t.setReadOnly(True)
        l.addWidget(t)
        cb = QDialogButtonBox(QDialogButtonBox.Close)
        cb.rejected.connect(d.reject)
        l.addWidget(cb)
        d.setLayout(l)
        d.exec_()

    def _list_dialog(self, title, items):
        if not items:
            QMessageBox.information(self, title, "None found.")
            return
        d = QDialog(self)
        d.setWindowTitle(f"{title} ({len(items)})")
        d.resize(700, 500)
        l = QVBoxLayout()
        lw = QListWidget()
        for it in items:
            lw.addItem(QListWidgetItem(str(it)))
        lw.itemDoubleClicked.connect(lambda i: self.new_tab(i.text()))
        l.addWidget(lw)
        cb = QDialogButtonBox(QDialogButtonBox.Close)
        cb.rejected.connect(d.reject)
        l.addWidget(cb)
        d.setLayout(l)
        d.exec_()

    def on_download(self, dl: QWebEngineDownloadItem):
        try:
            p, _ = QFileDialog.getSaveFileName(self, "Save", dl.path() or dl.downloadFileName())
            if p:
                dl.setPath(p)
                dl.accept()
            else:
                dl.cancel()
        except Exception:
            pass

    def closeEvent(self, e):
        e.accept()


# ============================================================
#  SMART TOR DETECTION
# ============================================================
def _detect_tor_mode():
    """Return (use_tor: bool, tor_available: bool, message: str)"""
    tor = TorManager()

    if Config.USE_TOR is True:
        if tor.is_running():
            return True, True, "Tor detected (forced mode)"
        if Config.TOR_AUTO_START and tor.start_tor():
            return True, True, "Tor auto-started"
        return True, False, "Tor not found (USE_TOR=True, will error)"

    if Config.USE_TOR is False:
        return False, False, "Tor disabled by user"

    # "auto"
    if tor.is_running():
        return True, True, "Tor detected — using Tor"
    if Config.TOR_AUTO_START and tor.start_tor():
        return True, True, "Tor auto-started"
    return False, False, "Tor not found — using direct connection"


# ============================================================
#  MAIN
# ============================================================
def main():
    print("╔══════════════════════════════════════════════╗")
    print("║   ROOT BROWSER v5.0 — Smart Tor Mode        ║")
    print("╚══════════════════════════════════════════════╝")

    use_tor, tor_available, message = _detect_tor_mode()
    print(f"[*] {message}")

    if use_tor:
        os.environ['QTWEBENGINE_CHROMIUM_FLAGS'] = (
            f'--proxy-server=socks5://127.0.0.1:{Config.TOR_SOCKS_PORT}'
        )
        print(f"[✓] Proxy set to Tor SOCKS5 (127.0.0.1:{Config.TOR_SOCKS_PORT})")
    else:
        os.environ.pop('QTWEBENGINE_CHROMIUM_FLAGS', None)
        print("[✓] No proxy — direct connection")

    Config.USE_TOR = use_tor
    Config._TOR_AVAILABLE = tor_available

    app = QApplication(sys.argv)
    app.setFont(QFont("Segoe UI", 10))

    # License acceptance (first run only)
    if LICENSE_AVAILABLE:
        flag = os.path.join(os.path.expanduser("~"), ".root_browser_agreed")
        if not os.path.exists(flag):
            if not request_acceptance():
                print("[!] License not accepted. Exiting.")
                sys.exit(0)
            try:
                with open(flag, 'w', encoding='utf-8') as f:
                    f.write(datetime.now().isoformat())
            except Exception:
                pass

    # Verify Tor exit IP
    if use_tor and tor_available:
        try:
            tor = TorManager()
            ip, is_tor = tor.get_exit_ip()
            if ip:
                print(f"[✓] Exit IP: {ip}  IsTor: {is_tor}")
            else:
                print("[!] Could not fetch exit IP")
        except Exception as e:
            print(f"[!] Exit IP check failed: {e}")

    w = Browser()
    w.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()