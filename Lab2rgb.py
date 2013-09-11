import numpy as np

def lab2rgb(c):
    """accepts and returns tuple"""
    L,a,b = c
    # D65 reference white XYZ coords
    d65 = 0.95047, 1.00000, 1.08883
    # from CIE ...
    eps = 216./24389.
    kappa = 24389./27.
    fy = (L+16.)/116.
    fx = a/500. + fy
    fz = fy - b/200.
    if fx**3 > eps:
        x = fx**3
    else:
        x = (116*fx - 16)/kappa

    if L > kappa * eps:
        y = ((L + 16)/116)**3
    else:
        y = L/kappa

    if fz**3 > eps:
        z = fz**3
    else:
        z = (116*fz - 16)/kappa

    XYZ = np.array([d65[0] * x, d65[1] * y, d65[2] * z])
    # XYZ -> RGB matrix for AppleRGB
    M_inv = np.array([[2.9515373, -1.2894116, -0.4738445],
                      [-1.0851093, 1.9908566,  0.0372026],
                      [0.0854934, -0.2694964,  1.0912975]])

    # linear rgb (v)
    v = np.dot(M_inv, XYZ)

    gam = 1.8 # AppleRGB gamma

    # gamma correction and scale to [0,255]
    V = np.round(255 * (v ** (1./gam))).astype(int)

    return tuple(V)
