#!/usr/bin/env python3
"""
Security Levels – controls privacy & anti‑fingerprinting intensity
"""
import random

class SecurityLevel:
    NO_SAFETY = 0
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    HARD = 4
    EXTREME = 5

    NAMES = {
        0: "No Safety",
        1: "Low",
        2: "Medium",
        3: "High",
        4: "Hard",
        5: "Extreme"
    }

class SecurityManager:
    def __init__(self, level=SecurityLevel.MEDIUM):
        self.level = level

    def set_level(self, level):
        self.level = level

    def get_js(self):
        """Returns the JavaScript injection for the current security level."""
        base = """
        (function() {
            delete window.RTCPeerConnection;
            delete window.webkitRTCPeerConnection;
            delete window.mozRTCPeerConnection;
            if(navigator.getBattery) delete navigator.getBattery;
            Object.defineProperty(navigator,'platform',{get:()=>'""" + random.choice(['Win32','Linux x86_64','MacIntel']) + """'});
            Object.defineProperty(navigator,'hardwareConcurrency',{get:()=>""" + str(random.randint(2,16)) + """});
            Object.defineProperty(navigator,'deviceMemory',{get:()=>""" + str(random.randint(2,8)) + """});
            Date.prototype.getTimezoneOffset=function(){return 0;};
            const origToDataURL=HTMLCanvasElement.prototype.toDataURL;
            HTMLCanvasElement.prototype.toDataURL=function(t){
                const ctx=this.getContext('2d');
                if(ctx){
                    const img=ctx.getImageData(0,0,this.width,this.height);
                    for(let i=0;i<img.data.length;i+=4){img.data[i]^=1;}
                    ctx.putImageData(img,0,0);
                }
                return origToDataURL.apply(this,arguments);
            };
            const gp=WebGLRenderingContext.prototype.getParameter;
            WebGLRenderingContext.prototype.getParameter=function(p){
                if(p===37445)return'Google Inc.';
                if(p===37446)return'ANGLE (Intel)';
                return gp.call(this,p);
            };
        """

        # localStorage / sessionStorage polyfill (from Low onwards)
        if self.level >= SecurityLevel.LOW:
            base += """
            (function() {
                function createStorage() {
                    var data = {};
                    return {
                        getItem: function(key) { return key in data ? data[key] : null; },
                        setItem: function(key, value) { data[key] = String(value); },
                        removeItem: function(key) { delete data[key]; },
                        clear: function() { data = {}; },
                        key: function(index) { var keys = Object.keys(data); return keys[index] || null; },
                        get length() { return Object.keys(data).length; }
                    };
                }
                try {
                    var test = localStorage.length;
                } catch(e) {
                    window.localStorage = createStorage();
                }
                try {
                    var test2 = sessionStorage.length;
                } catch(e) {
                    window.sessionStorage = createStorage();
                }
            })();
            """

        # High: stronger canvas noise, block more APIs
        if self.level >= SecurityLevel.HIGH:
            base += """
            const origToBlob = HTMLCanvasElement.prototype.toBlob;
            HTMLCanvasElement.prototype.toBlob = function(callback, type, quality) {
                const ctx = this.getContext('2d');
                if (ctx) {
                    const img = ctx.getImageData(0,0,this.width,this.height);
                    for(let i=0;i<img.data.length;i+=4){
                        img.data[i] = Math.min(255, Math.max(0, img.data[i] + Math.floor(Math.random()*5-2)));
                    }
                    ctx.putImageData(img,0,0);
                }
                origToBlob.call(this, callback, type, quality);
            };
            if(window.speechSynthesis) delete window.speechSynthesis;
            if(window.SpeechRecognition) delete window.SpeechRecognition;
            if(window.webkitSpeechRecognition) delete window.webkitSpeechRecognition;
            if(navigator.getGamepads) delete navigator.getGamepads;
            """

        # Hard: remove USB, Bluetooth, Serial, HID
        if self.level >= SecurityLevel.HARD:
            base += """
            if(navigator.usb) delete navigator.usb;
            if(navigator.bluetooth) delete navigator.bluetooth;
            if(navigator.serial) delete navigator.serial;
            if(navigator.hid) delete navigator.hid;
            """

        # Extreme: timing obfuscation
        if self.level >= SecurityLevel.EXTREME:
            base += """
            const origNow = performance.now;
            performance.now = function() { return origNow() + Math.random()*0.5; };
            """

        base += "\n})();"
        return base

    def get_block_list(self):
        if self.level <= SecurityLevel.LOW:
            return []
        medium = [
            "doubleclick.net", "googleadservices.com", "googlesyndication.com",
            "facebook.com/tr", "analytics.google.com", "googletagmanager.com"
        ]
        if self.level >= SecurityLevel.MEDIUM:
            block = medium.copy()
            if self.level >= SecurityLevel.HIGH:
                block += ["scorecardresearch.com", "outbrain.com", "taboola.com",
                          "quantserve.com", "addthis.com", "bluekai.com"]
            if self.level >= SecurityLevel.EXTREME:
                block += ["exelator.com", "nexac.com", "rfihub.com", "adsrvr.org",
                          "adnxs.com", "demdex.net"]
            return block
        return []
