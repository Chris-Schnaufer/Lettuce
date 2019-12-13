"""My nifty plot-level RGB algorithm
"""

# Importing modules. Please add any additional import statements below
import numpy as np
from keras.models import load_model
from whole_field_test import evaluate_whole_field, draw_boxes
import tempfile
import os
os.environ['KMP_DUPLICATE_LIB_OK'] ='True' # This prevents a crash from improperly loading a GPU library, but prevents using it I think. Comment out to see if it will work on your machine
import logging
import keras 
from skimage.io import imread, imsave, imshow, show
from skimage.color import grey2rgb
from skimage.transform import resize, rescale, pyramid_expand
from size_calculator import calculate_sizes, create_for_contours
from construct_quadrant_file import create_quadrant_file
from zipfile import ZipFile
from contours_test import create_quadrant_image
from PIL import Image
# Definitions
# Please replace these definition's values with the correct ones
VERSION = '1.0'

# Information on the creator of this algorithm
ALGORITHM_AUTHOR = 'Emmanuel'
ALGORITHM_AUTHOR_EMAIL = 'emmanuelgonzalez@email.arizona.edu'

ALGORITHM_NAME = 'Size_counts'
ALGORITHM_DESCRIPTION = 'Takes in RGB images and outputs a CSV with counts.'

# Citation information for publication (more information in HOW_TO.md)
CITATION_AUTHOR = 'unknown'
CITATION_TITLE = ''
CITATION_YEAR = ''

# The name of one or more variables returned by the algorithm, separated by commas (more information in HOW_TO.md)
# If only one name is specified, no comma's are used.
# Note that variable names cannot have comma's in them: use a different separator instead. Also,
# all white space is kept intact; don't add any extra whitespace since it may cause name comparisons
# to fail.
VARIABLE_NAMES = 'quadrant,total_count,small_count,medium_count,large_count,size_type'

# Optional override for the generation of a BETYdb compatible csv file
# Set to False to suppress the creation of a compatible file
WRITE_BETYDB_CSV = False

# Optional override for the generation of a TERRA REF Geostreams compatible csv file
# Set to False to suppress the creation of a compatible file
WRITE_GEOSTREAMS_CSV = False


# Entry point for plot-level RBG algorithm
def calculate(pxarray: np.ndarray):
    output_dir = tempfile.mkdtemp()
    boxes = os.path.join(output_dir, "boxes.npy")
    labels = os.path.join(output_dir, "size_labels.npy")
    logging.debug("Evaluating Field")
    keras.backend.clear_session()
    loaded_model = load_model('/home/extractor/model/trained_model_new2.h5')
    evaluate_whole_field(output_dir, pxarray, loaded_model)
    boxes = np.load(boxes).astype("int")

    im = draw_boxes(grey2rgb(pxarray.copy()), boxes, color=(255, 0, 0))
    imsave(output_dir + "counts.png", im)

    logging.debug("Calculating Sizes")

    labels, size_labels = calculate_sizes(boxes, pxarray)
    label_ouput= np.array([size_labels[label] for label in labels])

    np.save(labels, label_ouput)

    RGB_tuples = [[0, 0, 255], [0, 255, 0], [255, 0, 0]]
    color_field = create_for_contours("contour.png", pxarray, boxes, labels, size_labels, RGB_tuples=RGB_tuples)

    imsave(output_dir + "sizes.png", color_field)
    
    width = 1200
    height = 900
    img_width = pxarray.shape[1]
    img_height = pxarray.shape[0]

    output_field = create_quadrant_image("overview.png", color_field)
    im = Image.fromarray(output_field.astype(np.uint8), mode="RGB")
    im = im.resize((width, height))
    im = np.array(im.getdata(), np.uint8).reshape(height, width,3)

    imsave(output_dir + "harvest_regions.png", im)
    
    region_size = 230
    regions = {}

    for box, label in zip(boxes, labels):
        x1, y1, x2, y2 = box
        x = np.mean([x2,x1])
        y = np.mean([y2,y1])
        regions[str(int(x / region_size)) + ":" + str(int(y / region_size))].append(label)

    for nme, labs in regions.items():
    #get lat long in here.
    #lati, longi = lat_long[nme]
        size = len(labs)
        if size == 0:
            continue
            #counts = [0,0,0]
            #type = -1
        else:
            counts, _ = np.histogram(np.array(labs), bins=[0,1,2,3])
            typ = np.argmax(counts)
            #print(lati, ",", longi)

        return[nme, str(size), str(counts[0]), str(counts[1]), str(counts[2]), str(typ)]