
Blockstack is an open-source game combining real colored blocks, a
webcam, and a virtual 3d scene. Players of the game are in a race to
arrange the real-life blocks to match the tower configuration shown on
the virtual blocks. The computer watches the real blocks and figures
out the moment the player has made the correct tower. The game score
is a function of how many towers the player can match within a fixed
time. 

The software uses Panda3d, opengl, gstreamer (camera pipeline), v4l2
(camera controls), opencv (colorspace), numpy (image analysis), and
goocanvas (debugging diagram).



Dependencies
============

ubuntu packages
---------------

* ttf-aenigma
* ttf-ubuntu-font-family
* python-twisted-core
* python-pygoocanvas
* python-gtk2
* python-numpy

* panda3d1.8 (add to /etc/apt/sources.list 'deb http://archive.panda3d.org/ubuntu oneiric main')

Running
=======

    buildout2.7
    bin/python blockstack --sound --colors yellow green blue

easy_install vs ppython
-----------------------

If ppython has sys.version like '2.7.2+ ...', you might get this failure:

    File "/usr/lib/python2.7/dist-packages/zc/buildout/easy_install.py", line 191, in _get_version
    version = re.match('(\d[.]\d)([.].*\d)?$', version).group(1)

A workaround is to hack that line to look like this:

    version = re.match('(\d[.]\d)([.].*[\d\+])?$', version).group(1)


-----------------------------------------------------------------

Question.wav is converted from this sound set:
    KDE Sound theme "Borealis"
    Version 0.8 (09/01/2004)

    by Ivica Ico Bukvic (SlipStreamScapes)
    ico at fuse net
    http://meowing.ccm.uc.edu/~ico/
    http://kde-look.org/content/show.php?content=12584

    LICENSE
    =======
    The sound package is provided under the Artistic License with minor additions to it. See below for more info. That being said, if someone wants to merge it with the vanilla KDE project
    I am completely fine with that and if that will require a license change I would be willing to make appropriate changes to the license.

    The only additional clause to this license is as follows:

    You may not use these sounds in any non GPL-ed or LGPL-ed software/OS for profit-making purposes. In other words, you may freely distribute it and use it for personal needs however you
    wish (even in Windows or MacOS), but any commercial endeavors are allowed only if they are associated solely with the GPL-ed and LGPL-ed software which also includes software that exi
    sts as both GPL/LGPL and commercial version, i.e. Trolltech's Qt.


------------

new opencv:

OpenCV-2.3.1% cmake -D WITH_TBB=ON -D BUILD_NEW_PYTHON_SUPPORT=ON -D WITH_V4L=OFF -D INSTALL_C_EXAMPLES=ON -D INSTALL_PYTHON_EXAMPLES=ON -D BUILD_EXAMPLES=ON -D WITH_FFMPEG=OFF .   
make


------------
docs:

http://people.gnome.org/~gianmt/pygoocanvas/

http://opencv.itseez.com/modules/refman.html

http://docs.scipy.org/doc/numpy/reference/index.html

http://gstreamer.freedesktop.org/data/doc/gstreamer/head/gstreamer/html/index.html
http://developer.gnome.org/gst-plugins-libs/0.10/gst-plugins-good-plugins-gdkpixbufsink.html

numpy hsv convertors:

http://stackoverflow.com/questions/4890373/detecting-thresholds-in-hsv-color-space-from-rgb-using-python-pil

http://fwarmerdam.blogspot.com/2010/01/hsvmergepy.html (bug in numpy.choose line)

--------------
dldn music from http://dig.ccmixter.org

--------------

todo:
lightning between the live+opengl matching blocks
more auto calibration
more game: react better to fast players, let them build chains of fast matches
synth the entering sound according to the exact block layout



