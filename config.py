import json, tempfile, time, subprocess

class Config(object):
    def __init__(self, wtree, blockHues, cameraDevice):
        self.wtree, self.blockHues = wtree, blockHues
        self.cameraDevice = cameraDevice
        
    def load(self):
        self.config = json.load(open("config.json"))
        self.adjKeys = self.config['adjustments'].keys()
        for k in self.adjKeys:
            adj = self.wtree.get_object(k)
            adj.set_value(self.config['adjustments'][k])
            adj.connect("value-changed", self.save)

        for k, adj in self.blockHues.adjs.items():
            adj.set_value(self.config.get('hues', {}).get(k, 0))
            adj.connect("value-changed", self.save)

        if self.config.get('cameras', {}).get(self.cameraDevice):
            conf = self.config['cameras'][self.cameraDevice]
            conf["White Balance Temperature, Auto"]['val'] = 1
            wbt = conf.pop("White Balance Temperature")
            print "white balance.."
            self.v4lSet(conf)
            time.sleep(.7)
            conf["White Balance Temperature, Auto"]['val'] = 0
            self.v4lSet(conf)
            print "locked"
            # it looks like if you put this in while turning off auto,
            # there's an error, like it set WBT before sending the
            # setting for Auto
            conf["White Balance Temperature"] = wbt
            self.v4lSet(conf)
            
            print "camera set"

    def saveCameraConfig(self, *args):
        self.config.setdefault('cameras', {}).update({
            self.cameraDevice : self.v4lGet()})
        self.save()
            
    def save(self, *args):
        adjs = dict((k, self.wtree.get_object(k).get_value())
                    for k in self.adjKeys)
        hues = dict((color, adj.get_value())
                    for (color, adj) in self.blockHues.adjs.items())

        self.config.update({"adjustments":adjs, "hues":hues})

        f = open("config.json", "w")
        f.write(json.dumps(self.config, indent=2))
        f.close()

    def v4lGet(self):
        tf = tempfile.NamedTemporaryFile()
        subprocess.check_call(["v4l2ctrl", "-d", self.cameraDevice,
                               "-s", tf.name])
        ctls = {}
        for line in tf.readlines():
            ctl, name, val = map(str.strip, line.split(':'))
            ctls[name] = {"ctl":int(ctl), "val":int(val)}
        return ctls

    def v4lSet(self, conf):
        tf = tempfile.NamedTemporaryFile()
        for name, d in conf.items():
            tf.write("%s:%31s:%s\n" % (d['ctl'], name, d['val']))
        tf.flush()
        subprocess.check_call(["v4l2ctrl", "-d", self.cameraDevice,
                               "-l", tf.name])
