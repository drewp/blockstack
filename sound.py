import pyglet
from pyglet.media import load

class Sound(object):
    def __init__(self, enabled=True):
        if not enabled:
            self.idle = lambda *args: None
            return
        self.intro = load("music/dldn-intro.wav", streaming=True)
        self.mid = load("music/dldn-mid.wav", streaming=True)
        self.bgMusic = pyglet.media.Player()
        self.bgMusic.queue(self.intro)
        self.bgMusic.queue(self.mid)
        self.bgMusic.volume = .4
        
        self.bgMusic.play()

        self.effects = {
            'match' : load("sound/match.wav", streaming=False),
            'explode' : load("sound/Missile_Impact-2012236287-cut.wav", streaming=False),
            'swoosh' : load("sound/Swoosh-1-SoundBible.com-231145780.wav", streaming=False),
            }
        
    def playEffect(self, name):
        self.effects[name].play()

    def idle(self):
        # this may be adding 20% cpu load
        pyglet.clock.tick(poll=True)
        self.bgMusic.dispatch_events()

        if self.bgMusic.source == self.mid:
            self.bgMusic.eos_action = pyglet.media.Player.EOS_LOOP    
        
        return True

