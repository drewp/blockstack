
class Sound(object):
    musicVolume = .3
    def __init__(self, loader, base, enabled=True):
        self.base = base
        if not enabled:
            self.playEffect = lambda *args: None
            return
        print "loading music"
        self.intro = loader.loadSfx("music/dldn-intro.wav")
        self.mid = loader.loadSfx("music/dldn-mid.wav")
        self.crash = loader.loadSfx("music/dldn-crash.ogg")
        print "done"

        self.restartBgMusic()
        
        self.effects = {
            'match' : loader.loadSfx("sound/match.ogg"),
            'explode' : loader.loadSfx("sound/Missile_Impact-2012236287-cut.ogg"),
            'swoosh' : loader.loadSfx("sound/Swoosh-1-SoundBible.com-231145780.ogg"),
            }

    def restartBgMusic(self):
        self.mid.stop()
        self.intro.setVolume(self.musicVolume)
        self.intro.play()
        self.intro.setFinishedEvent("introFinished")
        def fin():
            self.mid.setVolume(self.musicVolume)
            self.mid.setLoop(True)
            self.mid.play()
        self.base.accept("introFinished", fin)


    def playEffect(self, name):

        if name == 'gameStart':
            self.restartBgMusic()
            return
        elif name == 'gameOver':
            self.intro.stop()
            self.mid.stop()
            self.crash.setVolume(self.musicVolume)
            self.crash.play()
            self.crash.setFinishedEvent("crashFinished")
            self.base.accept("crashFinished", self.restartBgMusic)
            return
            
        self.effects[name].play()
