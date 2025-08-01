"""
Transform and deformation functions for ANTsPyMM
Extracted from mm.py - maintains exact original functionality
"""

import numpy as np

# Import conditionally
try:
    import ants
except ImportError:
    ants = None

try:
    from scipy.linalg import polar
except ImportError:
    polar = None


def deformation_gradient_optimized(warp_image, to_rotation=False, to_inverse_rotation=False):
    """
    Compute the deformation gradient tensor from a displacement (warp) field image.

    This function computes the **deformation gradient** `F = ∂φ/∂x` where `φ(x) = x + u(x)` is the mapping
    induced by the displacement field `u(x)` stored in `warp_image`.

    The returned tensor field has shape `(x, y, z, dim, dim)` (for 3D), where each matrix represents 
    the **Jacobian** of the transformation at that voxel. The gradient is computed in the physical space 
    of the image using spacing and direction metadata.

    Optionally, the deformation gradient can be projected onto the space of pure rotations using the polar
    decomposition (via SVD). This is useful for applications like reorientation of tensors (e.g., DTI).

    Parameters
    ----------
    warp_image : ants.ANTsImage
        A vector-valued ANTsImage encoding the warp/displacement field. It must have `dim` components
        (e.g., shape `(x, y, z, 3)` for 3D) representing the displacements in each spatial direction.
        
    to_rotation : bool, optional
        If True, the deformation gradient will be replaced with its **nearest rotation matrix**
        using the polar decomposition (`F → R`, where `F = R U`).
        
    to_inverse_rotation : bool, optional
        If True, the deformation gradient will be replaced with the **inverse of the rotation**
        (`F → R.T`), which is often needed for transforming tensors **back** to their original frame.

    Returns
    -------
    F : np.ndarray
        A NumPy array of shape `(x, y, z, dim, dim)` (or `(dim1, dim2, ..., dim, dim)` in general),
        representing the deformation gradient tensor field at each voxel.

    Raises
    ------
    RuntimeError
        If `warp_image` is not an `ants.ANTsImage`.

    Notes
    -----
    - The function computes gradients in physical space using the spacing of the image and applies 
      the image direction matrix (`tdir`) to properly orient gradients.
    - The gradient is added to the identity matrix to yield the deformation gradient `F = I + ∂u/∂x`.
    - The polar decomposition ensures `F` is replaced with the closest rotation matrix (orthogonal, det=1).
    - This is a **vectorized pure NumPy implementation**, intended for performance and simplicity.

    Examples
    --------
    >>> warp = ants.create_warp_image(reference_image, displacement_field)
    >>> F = deformation_gradient_optimized(warp)
    >>> R = deformation_gradient_optimized(warp, to_rotation=True)
    """
    if ants is None:
        raise ImportError("ants package is required for deformation_gradient_optimized function")
    
    # Ensure warp_image is an ANTsImage (otherwise it has no spacing or direction)
    if not isinstance(warp_image, ants.ANTsImage):
        raise RuntimeError("warp_image must be an ants.ANTsImage.")
    
    # Extract data, spacing, direction
    data = warp_image.numpy()
    spacing = warp_image.spacing
    
    # Correct direction retrieval using .data_pointer and .view()
    direction_flat = warp_image.direction.data_pointer
    dim = warp_image.dimension
    tdir = direction_flat.view()[:dim**2].reshape((dim, dim))
    
    # For displacement fields, the last dimension is the number of components
    shape = data.shape[:-1]
    
    # Initialize the deformation gradient tensor field
    F = np.zeros(shape + (dim, dim))
    
    # For each displacement component, compute spatial gradients
    for comp in range(dim):
        displacement_comp = data[..., comp]
        
        for axis in range(dim):
            grad = np.gradient(displacement_comp, axis=axis, edge_order=2)
            
            # Apply spacing (divide by voxel size along the axis) to get gradient in physical space
            grad /= spacing[axis]
            
            # Apply the image direction matrix to the gradient
            # Store in the appropriate location of the Jacobian matrix
            F[..., comp, :] += grad[..., np.newaxis] * tdir[axis, :]
    
    # Add the identity matrix to get the deformation gradient (F = I + ∂u/∂x)
    identity = np.eye(dim)
    F += identity
    
    # Optional: project onto rotation manifold
    if to_rotation or to_inverse_rotation:
        if polar is None:
            raise ImportError("scipy package is required for rotation decomposition")
        
        # Flatten F to iterate over each gradient matrix
        F_flat = F.reshape(-1, dim, dim)
        
        for i in range(F_flat.shape[0]):
            # Polar decomposition: F = R @ U
            R, _ = polar(F_flat[i])
            
            # Ensure R is a proper rotation (det(R) = 1)
            if np.linalg.det(R) < 0:
                R[:, -1] *= -1  # Flip one column to make det(R) = 1
            
            if to_inverse_rotation:
                F_flat[i] = R.T  # Use the inverse rotation (transpose)
            else:
                F_flat[i] = R
        
        # Reshape back to the original shape
        F = F_flat.reshape(shape + (dim, dim))
    
    return F