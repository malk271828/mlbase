import os
import sys
import warnings
import subprocess
sys.path.insert(0, os.getcwd())
warnings.filterwarnings('ignore', category=DeprecationWarning)
warnings.filterwarnings('ignore', category=FutureWarning)

import pytest
from random import seed, random, randrange
seed(123)

from cv_util import generateNormalizedPatchedImage

@pytest.mark.parametrize("cmStr", ["jet", "spring", "plasma"])
def test_image(cmStr):
    n_sample = 255
    WIDTH, HEIGHT = 500, 300
    alpha = 1

    list_xy = list()
    for _ in range(n_sample):
        x = randrange(WIDTH)
        y = randrange(HEIGHT)
        cx = 100
        cy = 100
        list_xy.append((x, y, cx, cy, alpha))

    n, c = generateNormalizedPatchedImage(list_xy, WIDTH, HEIGHT, cmStr=cmStr, verbose=2)