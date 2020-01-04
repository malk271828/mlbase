import numpy as np
from tqdm import tqdm
from colorama import *
init()

# Image Processing
from skimage.draw import rectangle
from PIL import Image, ImageDraw
import matplotlib.pyplot as plt

# Machine Learning Libraries
from sklearn.preprocessing import MinMaxScaler

def generateNormalizedGroupedPatchedImage(list_grouped_patch_xy:list,
                                   shape:tuple,
                                   cmStr:str = "jet",
                                   verbose:int = 0):
    data_max = 0
    return_scaler = None
    list_original_array = list()
    list_grouped_normalized_array = list()
    list_grouped_colored_array = list()
    cm = plt.get_cmap(cmStr)

    for i, list_patch_xy in enumerate(list_grouped_patch_xy):
        if verbose > 0:
            print("--------------------")
            print("{0} patches in group {1}:".format(len(list_patch_xy), i))
        original_array, _, _, scaler = generateNormalizedPatchedImage(list_patch_xy, shape, cmStr, verbose)
        if data_max < scaler.data_max_:
            data_max = scaler.data_max_
            return_scaler = scaler
        list_original_array.append(original_array)

    # calculate inter-group maximum scaling factor
    for original_array, list_patch_xy in zip(list_original_array, list_grouped_patch_xy):
        grouped_normalized_flatten_array = return_scaler.transform(np.reshape(original_array, newshape=(-1, 1)))
        grouped_normalized_array = np.reshape(grouped_normalized_flatten_array, newshape=shape)
        list_grouped_normalized_array.append(grouped_normalized_array)

        # generate colored image
        colored_array = cm(grouped_normalized_array)
        list_grouped_colored_array.append(colored_array)

    if verbose > 0:
        print("")
        print("number of groups: {0}".format(len(list_original_array)))
        print("data_max: {0}".format(data_max))
        print("[Grouped] range:[{0}, {1}]".format(np.min(list_grouped_colored_array), np.max(list_grouped_colored_array)))

    return list_original_array, list_grouped_normalized_array, list_grouped_colored_array, return_scaler

def generateNormalizedPatchedImage(list_patch_xy:list,
                                   shape:tuple,
                                   cmStr:str = "jet",
                                   verbose:int = 0):
    """
    Parameters
    ----------
    list_patch_xy : list of (x, y, cx, cy, alpha)
        specify locations of each patch.
        The range of x and cx must be within [0, height], and y and cy [0, width]
    shape : tuple of (width, height)
        indicate size of image
    cmStr : string indicating color-map
        available color-maps will be displayed in the following link:
        https://matplotlib.org/3.1.0/tutorials/colors/colormaps.html
    verbose : control verbosity level, default=0
        Lv.1 - show statistics on standard output
        Lv.2 - output generated image to file

    Return
    ------
    tuple of array of normalized image and color-map image

    Reference
    ---------
        https://stackoverflow.com/questions/43457308/is-there-any-good-color-map-to-convert-gray-scale-image-to-colorful-ones-using-p
        https://stackoverflow.com/questions/24571492/stacking-line-drawing-for-float-images-in-pillow
    """
    width, height = shape
    original_array = np.zeros(shape=(height, width), dtype=np.float)
    scaler = MinMaxScaler(feature_range=(0, 1))
    cm = plt.get_cmap(cmStr)

    for (x, y, cx, cy, alpha) in list_patch_xy:
        # clipping
        if x + cx >= height:
            cx = height - x
        if y + cy >= width:
            cy = width - y

        # pointwise addition
        rr, cc = rectangle(start=(x, y), extent=(cx, cy))
        original_array[rr, cc] += alpha

    scaler.fit(np.reshape(original_array, newshape=(-1, 1)))
    normalized_flatten_array = scaler.transform(np.reshape(original_array, newshape=(-1, 1)))
    normalized_array = np.reshape(normalized_flatten_array, newshape=(height, width))
    colored_array = cm(normalized_array)

    if verbose > 0:
        print(Fore.CYAN)
        print("[Original] shape: {0} range:[{1}, {2}]".format(original_array.shape, np.min(original_array), np.max(original_array)))
        print("[Normalized] shape: {0} range:[{1}, {2}]".format(normalized_array.shape, np.min(normalized_array), np.max(normalized_array)))
        print("[Colored] shape: {0} range:[{1}, {2}]".format(colored_array.shape, np.min(colored_array), np.max(colored_array)))
        print(Style.RESET_ALL)
        if verbose > 1:
            VIS_DIR = "visualization/"
            normalized_image = Image.fromarray(normalized_array*255)
            colored_image = Image.fromarray((colored_array*255).astype(np.uint8))

            Image.fromarray(original_array).convert("L").save(VIS_DIR + 'original.gif', quality=95)
            normalized_image.save(VIS_DIR + 'normalized.gif', quality=95)
            colored_image.save(VIS_DIR + "colored_" + cmStr + ".png", quality=95)
            print(Fore.MAGENTA + "output to files to {0}".format(VIS_DIR) + Style.RESET_ALL)

    return original_array, normalized_array, colored_array, scaler