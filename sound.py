import pyglet
from pyglet.media import load

class Sound(object):
    def __init__(self, enabled=True):
        if not enabled:
            self.idle = lambda *args: None
            return
        print "loading music"
        self.intro = load("music/dldn-intro.wav", streaming=False)
        self.mid = load("music/dldn-mid.wav", streaming=False)
        self.crash = load("music/dldn-crash.wav", streaming=False)
        print "done"
        self.bgMusic = pyglet.media.Player()
        self.bgMusic.volume = .6

        self.bgMusic.queue(self.intro)
        self.bgMusic.queue(self.mid)
        
        self.bgMusic.play()

        self.effects = {
            'match' : load("sound/match.wav", streaming=False),
            'explode' : load("sound/Missile_Impact-2012236287-cut.wav", streaming=False),
            'swoosh' : load("sound/Swoosh-1-SoundBible.com-231145780.wav", streaming=False),
            }


    def playEffect(self, name):
        if name == 'gameStart':
            self.bgMusic.queue(self.intro)
            self.bgMusic.queue(self.mid)
            self.bgMusic.eos_action = pyglet.media.Player.EOS_NEXT
            self.bgMusic.next()
            return
        elif name == 'gameOver':
            self.bgMusic.queue(self.crash)
            self.bgMusic.queue(self.intro)
            self.bgMusic.queue(self.mid)
            self.bgMusic.eos_action = pyglet.media.Player.EOS_NEXT
            self.bgMusic.next()
            return
            
        self.effects[name].play()

    def idle(self):
        # this may be adding 20% cpu load
        pyglet.clock.tick(poll=True)
        self.bgMusic.dispatch_events()

        if self.bgMusic.source == self.mid:
            self.bgMusic.eos_action = pyglet.media.Player.EOS_LOOP    
        
        return True

