import sys
import math

from operator import itemgetter, attrgetter
from joblib import Parallel, delayed
import numpy as np
from tqdm import tqdm
from colorama import *
init()

# Image Processing
from skimage.draw import rectangle, rectangle_perimeter
from PIL import Image, ImageDraw
import matplotlib.pyplot as plt

# Machine Learning Libraries
from sklearn.preprocessing import MinMaxScaler

class groupedNorm:
    def __init__(self):
        self.scaler = None
        self.data_max = -sys.maxsize

    def _fitScaler(self, array) -> MinMaxScaler:
        scaler = MinMaxScaler()
        scaler.fit(np.reshape(array, newshape=(-1, 1)))
        if self.data_max < scaler.data_max_[0]:
            self.data_max = scaler.data_max_[0]
            self.scaler = scaler

    def computeScaler(self,
                      GroupedArray,
                      deeper: bool = False,
                      verbose:int = 0) -> MinMaxScaler:
        """
        compute scaling factor without applying normalization.
        Groupding axis is the first dimension of 1st argument tensor.

        GroupedArray: array, required
            Source array which to be normalized
        deeper: boolean, optional
            If enabled, grouping axis get an additional dimension
        """
        for array in GroupedArray:
            # TODO: can take n-dimensional loop
            if deeper:
                for subArray in array:
                    self._fitScaler(subArray)
            else:
                self._fitScaler(array)

        if verbose > 0:
            print("data_max:{0}".format(self.data_max))
        assert self.scaler != None
        return self.scaler

    def ApplyScaling(self,
                     GroupedArray,
                     newshape:tuple,
                     verbose:int = 0) -> np.array:
        """
        Apply normalization with computed scaling factor
        """
        if self.scaler == None:
            raise Exception("before invoking this method")
        normalizedArray = GroupedArray.copy()
        for i, array in enumerate(GroupedArray):
            normalized_flattened_array = self.scaler.transform(np.reshape(array, newshape=(-1, 1)))
            if newshape == None:
                length = int(math.sqrt(len(normalized_flattened_array)))
                newshape = (length, length)
            normalizedArray[i] = np.reshape(normalized_flattened_array, newshape=newshape)
        if verbose > 0:
            print("length:{0}".format(length))
            print("range [{0}, {1}]->[{2}, {3}]".format(np.min(GroupedArray), np.max(GroupedArray), np.min(normalizedArray), np.max(normalizedArray)))
        return normalizedArray

def generateNormalizedGroupedPatchedImage(list_grouped_patch_xy:list,
                                   shape:tuple,
                                   mode:str,
                                   cmStr:str = "jet",
                                   verbose:int = 0,
                                   n_jobs:int = 1):
    # note:
    # To access shared variables from an inter function to be paralleled,
    # it should be declared as list or numpy array
    data_max = np.array([0], dtype=np.float32)
    list_original_array = list()
    list_grouped_normalized_array = list()
    cm = plt.get_cmap(cmStr)

    def _processGroup(i, group):
        if verbose > 0:
            print("--------------------")
            print("{0} patches in group {1}:".format(len(group), i))
        original_array = generateNormalizedPatchedImage(group, shape, mode=mode,
                                                                      cmStr=cmStr,
                                                                      verbose=verbose)
        list_original_array.append(original_array)

    Parallel(n_jobs=n_jobs, require='sharedmem')( [delayed(_processGroup)(i, group) for i, group in enumerate(list_grouped_patch_xy)] )

    # compute scaling factor for normalization
    gn = groupedNorm()
    if mode == "add":
        gn.computeScaler(list_original_array)
    elif mode == "overwrite" or mode == "overwrite_perimeter":
        pass
    else:
        raise ValueError

    # apply scaling
    if mode == "add":
        grouped_normalized_array = gn.ApplyScaling(list_original_array, newshape=shape)
    elif mode == "overwrite" or mode == "overwrite_perimeter":
        grouped_normalized_array = list_original_array
    else:
        raise ValueError
    colored_array = cm(grouped_normalized_array)

    if verbose > 0:
        print("")
        print("number of groups: {0}".format(len(list_original_array)))
        print("data_max: {0}".format(data_max))
        print("[Grouped] range:[{0}, {1}]".format(np.min(colored_array), np.max(colored_array)))

    return list_original_array, list_grouped_normalized_array, colored_array

def generateNormalizedPatchedImage(list_patch_xy:list,
                                   shape:tuple,
                                   mode:str,
                                   cmStr:str = "jet",
                                   verbose:int = 0,
                                   n_jobs:int = 1):
    """
    Parameters
    ----------
    list_patch_xy : list of (x, y, cx, cy, alpha)
        specify locations of each patch.
        The range of x and cx must be within [0, height], and y and cy [0, width]
    shape : tuple of (width, height)
        indicate size of image
    mode : string specifying mode
        "add"       - add alpha value of each patch and normalize to limit range to [0, 1]
        "overwrite" - overwrite alpha value without normaling
    cmStr : string specifying color-map
        available color-maps will be listed in the following link:
        https://matplotlib.org/3.1.0/tutorials/colors/colormaps.html
    verbose : control verbosity level, default=0
        Lv.1 - show statistics on standard output
        Lv.2 - output generated image to file
    n_jobs : number of thread for multiprocessing parallerism, default=1

    Return
    ------
    tuple of array of (original image, normalized image, color-map image, scaler)
    The last scaler which have the highest data_max_ value will be chosen, and
    when mode is "add", scaler is always None.

    Reference
    ---------
        https://stackoverflow.com/questions/43457308/is-there-any-good-color-map-to-convert-gray-scale-image-to-colorful-ones-using-p
        https://stackoverflow.com/questions/24571492/stacking-line-drawing-for-float-images-in-pillow
    """
    width, height = shape
    original_array = np.zeros(shape=(height, width), dtype=np.float)
    cm = plt.get_cmap(cmStr)

    def _processPatch(patch:tuple):
        x, y, cx, cy, alpha = patch
        # clipping
        if x + cx >= height:
            cx = height - x - 1
        if y + cy >= width:
            cy = width - y - 1
        if cx <= 0 or cy <= 0:
            return

        # pointwise addition
        if mode == "add":
            rr, cc = rectangle(start=(x, y), extent=(cx, cy))
            original_array[rr, cc] += alpha
        elif mode == "overwrite":
            rr, cc = rectangle(start=(x, y), extent=(cx, cy))
            original_array[rr, cc] = alpha
        elif mode == "overwrite_perimeter":
            rr, cc = rectangle_perimeter(start=(x, y), extent=(cx, cy))
            original_array[rr, cc] = alpha
        else:
            raise ValueError

    Parallel(n_jobs=n_jobs, require='sharedmem')([delayed(_processPatch)(patch) for patch in sorted(list_patch_xy, key=itemgetter(4))])

    if verbose > 0:
        print(Fore.CYAN)
        print("[Original] shape: {0} range:[{1}, {2}]".format(original_array.shape, np.min(original_array), np.max(original_array)))
        if "normalized_array" in locals():
            print("[Normalized] shape: {0} range:[{1}, {2}]".format(normalized_array.shape, np.min(normalized_array), np.max(normalized_array)))
        if "colored_array" in locals():
            print("[Colored] shape: {0} range:[{1}, {2}]".format(colored_array.shape, np.min(colored_array), np.max(colored_array)))
        print(Style.RESET_ALL)
        if verbose > 1:
            VIS_DIR = "visualization/"
            print(Fore.MAGENTA + "output to files to {0}".format(VIS_DIR) + Style.RESET_ALL)

            # output original
            Image.fromarray(original_array).convert("L").save(VIS_DIR + 'original.gif', quality=95)

            # output normalized
            if "normalized_array" in locals():
                normalized_image = Image.fromarray(normalized_array*255)
                normalized_image.save(VIS_DIR + 'normalized.gif', quality=95)

            # output colored
            if "colored_array" in locals():
                colored_image = Image.fromarray((colored_array*255).astype(np.uint8))
                colored_image.save(VIS_DIR + "colored_" + cmStr + ".png", quality=95)

    return original_array