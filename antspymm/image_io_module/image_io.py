"""
Image I/O utilities for ANTsPyMM
Extracted from mm.py - maintains exact original functionality
"""

import os
import re
import numpy as np

# Import ants conditionally
try:
    import ants
except ImportError:
    ants = None


def mm_read( x, standardize_intensity=False, modality='' ):
    """
    read an image from a filename - same as ants.image_read (for now)

    standardize_intensity : boolean ; if True will set negative values to zero and normalize into the range of zero to one

    modality : not used
    """
    if x is None:
        raise ValueError( " None passed to function antspymm.mm_read." )
    if not isinstance(x,str):
        raise ValueError( " Non-string passed to function antspymm.mm_read." )
    if not os.path.exists( x ):
        raise ValueError( " file " + x + " does not exist." )
    
    if ants is None:
        raise ImportError("ants package is required for mm_read function")
    img = ants.image_read( x, reorient=False )
    if standardize_intensity:
        img[img<0.0]=0.0
        img=ants.iMath(img,'Normalize')
    if modality == "T1w" and img.dimension == 4:
        print("WARNING: input image is 4D - we attempt a hack fix that works in some odd cases of PPMI data - please check this image: " + x, flush=True )
        i1=ants.slice_image(img,3,0)
        i2=ants.slice_image(img,3,1)
        kk=np.concatenate( [i1.numpy(),i2.numpy()], axis=2 )
        kk=ants.from_numpy(kk)
        img=ants.copy_image_info(i1,kk)
    return img


def mm_read_to_3d( x, slice=None, modality='' ):
    """
    read an image from a filename - and return as 3d or None if that is not possible
    """
    if ants is None:
        raise ImportError("ants package is required for mm_read_to_3d function")
    
    img = ants.image_read( x, reorient=False )
    if img.dimension <= 3:
        return img
    elif img.dimension == 4:
        nslices = img.shape[3]
        if slice is None:
            sl = np.round( nslices * 0.5 )
        else:
            sl = slice
        if sl > nslices:
            sl = nslices-1
        return ants.slice_image( img, axis=3, idx=int(sl) )
    elif img.dimension > 4:
        return img
    return None


def image_write_with_thumbnail( x,  fn, y=None, thumb=True ):
    """
    will write the image and (optionally) a png thumbnail with (optional) overlay/underlay
    """
    if ants is None:
        raise ImportError("ants package is required for image_write_with_thumbnail function")
    
    ants.image_write( x, fn )
    if not thumb or x.components > 1:
        return
    thumb_fn=re.sub(".nii.gz","_3dthumb.png",fn)
    if thumb and x.dimension == 3:
        if y is None:
            try:
                ants.plot_ortho( x, crop=True, filename=thumb_fn, flat=True, xyz_lines=False, orient_labels=False, xyz_pad=0 )
            except:
                pass
        else:
            try:
                ants.plot_ortho( y, x, crop=True, filename=thumb_fn, flat=True, xyz_lines=False, orient_labels=False, xyz_pad=0 )
            except:
                pass
    if thumb and x.dimension == 4:
        thumb_fn=re.sub(".nii.gz","_4dthumb.png",fn)
        nslices = x.shape[3]
        sl = np.round( nslices * 0.5 )
        if sl > nslices:
            sl = nslices-1
        xview = ants.slice_image( x, axis=3, idx=int(sl) )
        if y is None:
            try:
                ants.plot_ortho( xview, crop=True, filename=thumb_fn, flat=True, xyz_lines=False, orient_labels=False, xyz_pad=0 )
            except:
                pass
        else:
            if y.dimension == 3:
                try:
                    ants.plot_ortho(y, xview, crop=True, filename=thumb_fn, flat=True, xyz_lines=False, orient_labels=False, xyz_pad=0 )
                except:
                    pass
    return