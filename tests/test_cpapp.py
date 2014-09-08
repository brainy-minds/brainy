import os
import sys
import tempfile
import brainy_tests
from brainy.apps.cellprofiler import CellProfilerImages


IMAGES_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)),
                           'mock', 'images')


def test_cpimages_basic():
    output_path = tempfile.mkdtemp()
    cpimages = CellProfilerImages()
    cpimages.split_images(IMAGES_PATH, output_path)
    output_files = os.listdir(output_path)
    assert len(output_files) > 0
    with open(os.path.join(output_path, output_files[0])) as f:
        lines = f.readlines()
        # Expect 18 images plus header.
        assert len(lines) == 10
    # Uncomment to print
    #print lines
    #assert False


def test_cpimages_set_size():
    output_path = tempfile.mkdtemp()
    cpimages = CellProfilerImages({
        'image_set_size_per_batch': '4',
    })
    cpimages.split_images(IMAGES_PATH, output_path)
    output_files = os.listdir(output_path)
    assert len(output_files) > 0
    print output_files
    for filename in output_files:
        with open(os.path.join(output_path, filename)) as f:
            lines = f.readlines()
            # Expect 18 images plus header.
            print ''.join(lines)
            #assert len(lines) == 19
    #assert False
