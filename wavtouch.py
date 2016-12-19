#!/usr/bin/python2
import sys
import os.path
import wave
import array
import pygame
import urllib
import socket
try:
    from urllib import urljoin, urlopen
except ImportError:
    from urllib.parse import urljoin
    from urllib.request import urlopen
try:
    from cStringIO import StringIO
except ImportError:
    from io import BytesIO as StringIO

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


FGCOLOR = (255,255,0)
BGCOLOR = (0,0,255)

SOUNDS = (
    'sound_open',
    'sound_close',
    'voice1',
    'voice2',
    'voice3',
    'voice4',
    'voice5',
    'voice6',
    'voice7',
)


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


    def __init__(self, surface, font, sounds, baseurls):
        (self.width, self.height) = surface.get_size()
        self.surface = surface
        self.font = font
        self.sounds = sounds
        self.baseurls = baseurls
        self.log('App(%d,%d, baseurls=%r)' % (self.width, self.height, self.baseurls))
        self._text = None
        return

    def log(self, *args):
        print(' '.join(args))
        return

    def playSound(self, name=None):
        if name is not None:
            self.sounds[name].play()
        else:
            pygame.mixer.stop()
        return

    def refresh(self):
        assert self._text is not None
        self.surface.fill(BGCOLOR)
        b = self.font.render(self._text, 1, FGCOLOR)
        (w,h) = b.get_size()
        self.surface.blit(b, ((self.width-w)/2, (self.height-h)/2))
        pygame.display.flip()
        return

    def init_index(self):
        self.log('init_index')
        self._files = []
        for baseurl in self.baseurls:
            if baseurl.startswith('//'):
                addr = get_server_addr()
                if addr is None: continue
                baseurl = 'http://%s/%s' % (addr, baseurl[2:])
            if baseurl.startswith('http://'):
                url = urljoin(baseurl, 'index.txt')
                self.log(' opening: %r...' % url)
                try:
                    index = urlopen(url)
                    if index.getcode() in (None, 200): 
                        files = index.read()
                        for name in files.splitlines():
                            (name,_,_) = name.strip().partition('#')
                            if not name: continue
                            url = urljoin(baseurl, name)
                            self.log('  loading: %r...' % url)
                            fp = urlopen(url)
                            if fp.getcode() in (None, 200):
                                data = fp.read()
                                self._files.append((name, data))
                            fp.close()
                    index.close()
                    break
                except IOError as e:
                    self.log('  error: %s' % e)
                    continue
            else:
                # fallback to local files.
                path = os.path.join(baseurl, 'index.txt')
                self.log(' opening: %r...' % path)
                try:
                    index = open(path)
                    for name in index:
                        (name,_,_) = name.strip().partition('#')
                        if not name: continue
                        path = os.path.join(baseurl, name)
                        self.log('  loading: %r...' % path)
                        fp = open(path, 'rb')
                        data = fp.read()
                        self._files.append((name, data))
                        fp.close()
                    index.close()
                    break
                except IOError as e:
                    self.log('  error: %s' % e)
                    continue
        self.mode = 'index'
        self._text = 'INDEX'
        self.refresh()
        self.playSound('sound_close')
        self._curfile = None
        return
        
    def keydown_index(self, key):
        pygame.mixer.stop()
        if key in (pygame.K_BACKSPACE, pygame.K_TAB):
            self.init_index()
            return
        if key in (pygame.K_RETURN, pygame.K_SPACE, pygame.K_KP5):
            if self._curfile is not None:
                self.init_file(self._curfile)
            return
        if key in (pygame.K_LEFT, pygame.K_KP4):
            if self._curfile is None:
                if 0 < len(self._files):
                    self._curfile = 0
            elif 0 < self._curfile:
                self._curfile -= 1
        elif key in (pygame.K_RIGHT, pygame.K_KP6):
            if self._curfile is None:
                if 0 < len(self._files):
                    self._curfile = 0
            elif self._curfile+1 < len(self._files):
                self._curfile += 1
        elif key in (pygame.K_UP, pygame.K_KP8):
            if 0 < len(self._files):
                self._curfile = 0
        elif key in (pygame.K_DOWN, pygame.K_KP2):
            if 0 < len(self._files):
                self._curfile = len(self._files)-1
        if self._curfile is not None:
            (name, data) = self._files[self._curfile]
            self._sound = pygame.mixer.Sound(file=StringIO(data))
            self._sound.play()
            self._text = name
            self.refresh()
        return

    def init_file(self, index):
        assert index is not None
        self.log('init_file: %r' % index)
        (name, data) = self._files[index]
        reader = WaveReader(StringIO(data))
        self._samples = reader.read()
        self.mode = 'file'
        self._text = 'FILE'
        self.refresh()
        self.playSound('sound_open')
        self._curpos = None
        return
        
    def keydown_file(self, key):
        pygame.mixer.stop()
        if key in (pygame.K_BACKSPACE, pygame.K_TAB):
            self.init_index()
            return
        if key in (pygame.K_RETURN, pygame.K_SPACE, pygame.K_KP5):
            self._sound.play()
            return
        if key in (pygame.K_LEFT, pygame.K_KP4):
            if self._curpos is None:
                if 0 < len(self._samples):
                    self._curpos = 0
            elif 0 < self._curpos:
                self._curpos -= 1
        elif key in (pygame.K_RIGHT, pygame.K_KP6):
            if self._curpos is None:
                if 0 < len(self._samples):
                    self._curpos = 0
            elif self._curpos+1 < len(self._samples):
                self._curpos += 1
        elif key in (pygame.K_UP, pygame.K_KP8):
            if 0 < len(self._samples):
                self._curpos = 0
        elif key in (pygame.K_DOWN, pygame.K_KP2):
            if 0 < len(self._samples):
                self._curpos = len(self._samples)-1
        if self._curpos is not None:
            p = self._curpos*5
            v = self._samples[p]*32767
            v = map7(v)
            #self.log('  pos %r: %r' % (self._pos, v))
            self.playSound('voice%d' % v)
            self._text = str(v)
            self.refresh()
        return

    def run(self):
        while 1:
            e = pygame.event.wait()
            if e.type == pygame.QUIT:
                break
            elif e.type == pygame.KEYDOWN:
                if e.key in (pygame.K_q, pygame.K_ESCAPE, pygame.K_F4):
                    break
                else:
                    if self.mode == 'index':
                        self.keydown_index(e.key)
                    elif self.mode == 'file':
                        self.keydown_file(e.key)
            elif e.type == pygame.VIDEOEXPOSE:
                self.refresh()
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
    fontpath = './fonts/VeraMono.ttf'
    sounddir = './sounds/'
    for (k, v) in opts:
        if k == '-d': debug += 1
        elif k == '-f': flags = pygame.FULLSCREEN
        elif k == '-F': fontpath = v
        elif k == '-S': sounddir = v
    if not args:
        args = ['./wavs/']
    #
    pygame.mixer.pre_init(24000, -16, 1)
    pygame.init()
    modes = pygame.display.list_modes()
    if mode not in modes:
        mode = modes[0]
    pygame.display.set_mode(mode, flags)
    pygame.mouse.set_visible(0)
    pygame.key.set_repeat()
    font = pygame.font.Font(fontpath, 64)
    sounds = {}
    for name in SOUNDS:
        path = os.path.join(sounddir, name+'.wav')
        sounds[name] = pygame.mixer.Sound(path)
    #
    app = App(pygame.display.get_surface(), font, sounds, args)
    app.init_index()
    return app.run()

if __name__ == '__main__': sys.exit(main(sys.argv))
