#!/usr/bin/python2
import sys
import os.path
import wave
import struct
import array
import pygame
import urllib
import socket
from cStringIO import StringIO


def get_server_addr():
    try:
        addr = socket.gethostbyname(socket.gethostname())
    except socket.error:
        return None
    addr = addr.split('.')
    if addr[0] == '127':
        return None
    addr[-1] = '1'
    return '.'.join(addr)


##  WaveReader
##
class WaveReader(object):

    def __init__(self, fp):
        self._fp = wave.open(fp)
        self.nchannels = self._fp.getnchannels()
        self.sampwidth = self._fp.getsampwidth()
        self.framerate = self._fp.getframerate()
        self.nframes = self._fp.getnframes()
        self._nframesleft = self.nframes
        if self.sampwidth == 1:
            self.ratio = 1.0/256.0
            self.arraytype = 'b'
        else:
            self.ratio = 1.0/32768.0
            self.arraytype = 'h'
        return

    def __len__(self):
        return self.nframes

    def close(self):
        self._fp.close()
        return

    def eof(self):
        return (self._nframesleft == 0)
    
    def tell(self):
        return self._fp.tell()

    def seek(self, i):
        self._fp.setpos(i)
        self._nframesleft = self.nframes-i
        return

    def readraw(self, nframes=0):
        assert self.nchannels == 1
        if nframes == 0 or self._nframesleft < nframes:
            nframes = self._nframesleft
        self._nframesleft -= nframes
        return (nframes, self._fp.readframes(nframes))
    
    def read(self, nframes=0):
        (_,data) = self.readraw(nframes)
        a = array.array(self.arraytype)
        a.fromstring(data)
        return [ x*self.ratio for x in a ]


# map7
# 65536:8 = [ -20480, -12288, -4096, +4096, +12288, +20480 ]
# sine wave = [ 4, 6, 7, 7, 6, 4, 2, 1, 1, 2, ]
# rect wave = [ 7,7,7,7,7,1,1,1,1,1 ]
def map7(x):
    if x < -20480:
        return 1
    elif x < -12288:
        return 2
    elif x < -4096:
        return 3
    elif x < +4096:
        return 4
    elif x < +12288:
        return 5
    elif x < +20480:
        return 6
    else:
        return 7


class App(object):

    def __init__(self, baseurl=None,
                 fontpath='./fonts/Vera.ttf',
                 voicepath='./sounds/'):
        self.log('baseurl: %r' % baseurl)
        self.baseurl = baseurl
        self.display = pygame.display.get_surface()
        (self.width, self.height) = self.display.get_size()
        self.font = pygame.font.Font(fontpath, 64)
        self.voices = []
        self.sound_open = pygame.mixer.Sound(os.path.join(voicepath, 'sound_open.wav'))
        self.sound_close = pygame.mixer.Sound(os.path.join(voicepath, 'sound_close.wav'))
        for i in (1,2,3,4,5,6,7):
            name = 'voice%d.wav' % i
            sound = pygame.mixer.Sound(os.path.join(voicepath, name))
            self.voices.append(sound)
        self._text = ''
        return

    def log(self, *args):
        print(' '.join(args))
        return

    def repaint(self):
        self.display.fill((0,0,128))
        b = self.font.render(self._text, 1, (255,255,0), (0,0,128))
        (w,h) = b.get_size()
        self.display.blit(b, ((self.width-w)/2, (self.height-h)/2))
        pygame.display.flip()
        return

    def load_menu(self):
        self.log('load_menu')
        self._files = []
        if self.baseurl.startswith('http://'):
            url = urllib.basejoin(self.baseurl, 'index.txt')
            self.log(' opening: %r...' % url)
            try:
                index = urllib.urlopen(url)
                if index.getcode() in (None, 200): 
                    files = index.read()
                    for name in files.splitlines():
                        (name,_,_) = name.strip().partition('#')
                        if not name: continue
                        url = urllib.basejoin(self.baseurl, name)
                        self.log('  loading: %r...' % url)
                        fp = urllib.urlopen(url)
                        if fp.getcode() in (None, 200):
                            data = fp.read()
                            self._files.append((name, data))
                        fp.close()
                index.close()
            except IOError as e:
                self.log('  error: %s' % e)
        else:
            # fallback to local files.
            path = os.path.join(self.baseurl, 'index.txt')
            self.log(' opening: %r...' % path)
            try:
                index = open(path)
                for name in index:
                    (name,_,_) = name.strip().partition('#')
                    if not name: continue
                    path = os.path.join(self.baseurl, name)
                    self.log('  loading: %r...' % path)
                    fp = open(path, 'rb')
                    data = fp.read()
                    self._files.append((name, data))
                    fp.close()
            except IOError as e:
                self.log('  error: %s' % e)
        self._current = -1
        self._keydown = self.keydown_menu
        self._text = 'INDEX'
        self.repaint()
        self.sound_close.play()
        return
        
    def load_file(self):
        self.log('load_file: %r' % self._current)
        self._pos = -1
        self._keydown = self.keydown_file
        self._text = 'FILE'
        self.repaint()
        self.sound_open.play()
        return
        
    def keydown_menu(self, key):
        pygame.mixer.stop()
        if key in (pygame.K_ESCAPE, pygame.K_TAB):
            self.load_menu()
            return
        if key in (pygame.K_RETURN, pygame.K_SPACE, pygame.K_KP5):
            if 0 <= self._current:
                self.load_file()
            return
        if key in (pygame.K_LEFT, pygame.K_KP4):
            if self._current < 0:
                self._current = 0
            elif 0 < self._current:
                self._current -= 1
        elif key in (pygame.K_RIGHT, pygame.K_KP6):
            if self._current < 0:
                self._current = 0
            elif self._current < len(self._files)-1:
                self._current += 1
        elif key in (pygame.K_UP, pygame.K_KP8):
            self._current = 0
        elif key in (pygame.K_DOWN, pygame.K_KP2):
            self._current = len(self._files)-1
        if 0 <= self._current and self._current < len(self._files):
            (name, data) = self._files[self._current]
            self._text = name
            self._sound = pygame.mixer.Sound(buffer(data))
            self._sound.set_volume(0.5)
            self._sound.play()
            reader = WaveReader(StringIO(data))
            self._samples = reader.read()
            self.repaint()
        return

    def keydown_file(self, key):
        pygame.mixer.stop()
        if key in (pygame.K_ESCAPE, pygame.K_TAB):
            self.load_menu()
            return
        if key in (pygame.K_RETURN, pygame.K_SPACE, pygame.K_KP5):
            self._sound.play()
            return
        if key in (pygame.K_LEFT, pygame.K_KP4):
            if self._pos < 0:
                self._pos = 0
            elif 0 < self._pos:
                self._pos -= 1
        elif key in (pygame.K_RIGHT, pygame.K_KP6):
            if self._pos < 0:
                self._pos = 0
            elif self._pos < len(self._samples)-1:
                self._pos += 1
        elif key in (pygame.K_UP, pygame.K_KP8):
            self._pos = 0
        elif key in (pygame.K_DOWN, pygame.K_KP2):
            self._pos = len(self._samples)-1
        p = self._pos*5
        if 0 <= p and p < len(self._samples):
            v = self._samples[p]*32767
            v = map7(v)
            self.log('  pos %r: %r' % (self._pos, v))
            self.voices[v-1].play()
            self._text = str(v)
            self.repaint()
        return

    def run(self):
        self.repaint()
        while 1:
            e = pygame.event.wait()
            if e.type == pygame.QUIT: break
            elif e.type == pygame.KEYDOWN:
                if (e.key == pygame.K_q and e.mod & pygame.KMOD_CTRL): break
                self._keydown(e.key)
        return


def main(argv):
    import getopt
    def usage():
        print('usage: %s [-d] [-f] [url]' % argv[0])
        return 100
    try:
        (opts, args) = getopt.getopt(argv[1:], 'df')
    except getopt.GetoptError:
        return usage()
    debug = 0
    mode = (640,480)
    flags = 0
    for (k, v) in opts:
        if k == '-d': debug += 1
        elif k == '-f': flags = pygame.FULLSCREEN
    baseurl = './wavs/'
    if args:
        baseurl = args.pop(0)
    else:
        addr = get_server_addr()
        if addr is not None:
            baseurl = 'http://%s/wavtouch/' % addr
    #
    pygame.mixer.pre_init(24000, -16, 1)
    pygame.init()
    modes = pygame.display.list_modes()
    if mode not in modes:
        mode = modes[0]
    pygame.display.set_mode(mode, flags)
    pygame.mouse.set_visible(0)
    pygame.key.set_repeat()
    app = App(baseurl)
    app.load_menu()
    return app.run()

if __name__ == '__main__': sys.exit(main(sys.argv))
