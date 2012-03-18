import pyglet

class Sound(object):
    def __init__(self):

        self.intro = pyglet.media.load("music/dldn-intro.wav", streaming=True)
        self.mid = pyglet.media.load("music/dldn-mid.wav", streaming=True)
        self.bgMusic = pyglet.media.Player()
        self.bgMusic.queue(self.intro)
        self.bgMusic.queue(self.mid)
        self.bgMusic.volume = .4
        
        self.bgMusic.play()

        self.match = pyglet.media.load("match.wav", streaming=False)
        
    def playMatch(self):
        self.match.play()

    def idle(self):
        # this may be adding 20% cpu load
        pyglet.clock.tick(poll=True)
        self.bgMusic.dispatch_events()

        if self.bgMusic.source == self.mid:
            self.bgMusic.eos_action = pyglet.media.Player.EOS_LOOP    
        
        return True

