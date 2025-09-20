"""
Patch for PIL/Pillow compatibility issues
"""
import PIL.Image

# Add ANTIALIAS as alias for LANCZOS if not exists
if not hasattr(PIL.Image, 'ANTIALIAS'):
    PIL.Image.ANTIALIAS = PIL.Image.LANCZOS

# Add Resampling enum compatibility
if not hasattr(PIL.Image, 'Resampling'):
    class Resampling:
        NEAREST = PIL.Image.NEAREST
        BOX = PIL.Image.BOX if hasattr(PIL.Image, 'BOX') else PIL.Image.NEAREST
        BILINEAR = PIL.Image.BILINEAR
        HAMMING = PIL.Image.HAMMING if hasattr(PIL.Image, 'HAMMING') else PIL.Image.BILINEAR
        BICUBIC = PIL.Image.BICUBIC
        LANCZOS = PIL.Image.LANCZOS
    PIL.Image.Resampling = Resampling