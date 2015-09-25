from distutils.core import setup
from distutils.extension import Extension

setup(
    name = "alsamidi",
    version = "0.1",
    description = "alsa midi access",
    author = "Ivan Hernandez",
    author_email="ihernandez@kiusys.com",
    ext_modules=[Extension("alsamidi",["alsamidi.c"],libraries=['asound'])
                 ]
    )
    
    
setup(
    name = "nanosleep",
    version = "0.1",
    description = "Nanosleep for Python",
    author = "Izak Burger",
    ext_modules=[Extension("nanosleep",["nanosleep.c"])
                 ]
    )
    
    
