from distutils.core import setup
from distutils.extension import Extension
from Pyrex.Distutils import build_ext
setup(
  name = "cam",
  version="1.0",
  description="webcam access",
  
 
  ext_modules=[ 
    Extension("cam",
              ["cam.pyx", "camgrab-0.1/camgrab.c"],
              define_macros=[('main', 'camgrab_main'),
                             ('X_DISPLAY_MISSING', '1'), # for Imlib.h
                             ],
              include_dirs=['/usr/include/giblib'],
              library_dirs=['/usr/lib'],
              libraries=["Imlib2", "giblib"],
              )
    ],
  cmdclass = {'build_ext': build_ext}
)
