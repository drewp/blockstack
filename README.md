
Running:

buildout2.7
bin/python blockstack --sound --colors yellow green blue


Dependencies

ubuntu packages:

  ttf-aenigma
  ttf-ubuntu-font-family

  panda3d1.8

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

lightning between the live+opengl matching blocks
more auto calibration
more game: react better to fast players, let them build chains of fast matches
synth the entering sound according to the exact block layout
better lighting in game mode, glsl and spots and beams

what happened to ground's lighting? see if the old version just worked. layout the scene better. don't update cube pos only when there's a video frame, maybe panda has a more frequent update callback to use. on-screen text, check the sample programs for lots of it. different lighting for training/timed modes. 
