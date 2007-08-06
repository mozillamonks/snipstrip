#!/usr/bin/python
"""
snipstrip.py: Command-line tool to split up images of comic strips into
individual frames. This is useful for reading comics on handheld devices such
as mobile phones, PDAs and handheld multimedia players.

Copyright 2007 by Steven Fernandez <steve@lonetwin.net>

This program is free software; you can redistribute it and/or modify it under
the terms of the GNU General Public License as published by the Free Software
Foundation; either version 2 of the License, or (at your option) any later
version.

This program is distributed in the hope that it will be useful, but WITHOUT
ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
FOR A PARTICULAR PURPOSE.  See the GNU General Public License for more
details.

You should have received a copy of the GNU General Public License along with
this program.  If not, see <http://www.gnu.org/licenses/>.
"""
import sys
import os
try:
    import Image
except:
    print """
Error: This script uses the Python Imaging Library. Please install it.

On rpm based linux distributions, the package is most probably called
'python-imaging'. You may obtain the latest version of the library for your
platform from the Python Imaging Library website:

http://www.pythonware.com/products/pil/

"""
    sys.exit(1)

usage = """
%s <filename> [...]

where the arguments are comic strip image filenames.

This script will create files named 00-<filename> to NN-<filename> in the same
directory as the image file.
""" % sys.argv[0]


def gen_map_on_xaxis(img, x_cord):
    color_map = {}
    height    = img.size[1]
    for y_cord in range(height):
        color = img.getpixel((x_cord, y_cord))
        color_map[color] = color_map.get(color, [])
        color_map[color].append((x_cord, y_cord))
    return color_map

def gen_map_on_yaxis(img, y_cord):
    color_map = {}
    width     = img.size[0]
    for x_cord in range(width):
        color = img.getpixel((x_cord, y_cord))
        color_map[color] = color_map.get(color, [])
        color_map[color].append((x_cord, y_cord))
    return color_map

def snip(filename):
    y_candidates = []
    odir, ofile  = os.path.split(os.path.abspath(filename))

    debug  = 0  # Print debug messages
    img    = Image.open(filename)
    bw_img = img.convert('1') # Convert to black+white
    width, height = img.size[0], img.size[1]
    print "image size: %dx%d" % (width, height)

    # First we collect the candidates for splitting the image on the y-axis
    # We do this by, iterating over each y co-ordinate in the image ...
    for y_cord in range(height):
        # ...then we generate a color_map for all co-ordinates on the x-axis
        # for this y_cord.  The color_map is a map keyed by color. The value is
        # a list of co-ordinates where the color was found.
        color_map = gen_map_on_yaxis(bw_img, y_cord)
        #for k, y in color_map.items():
        #    print "%s: %d" % (k, len(y))
        # Now, if there was just color, it is quite likely this is an 'edge'
        # for the frames grid of the comic. We'll add this y_cord to the
        # y_candidates list
        if (len(color_map.keys()) < 2):
            y_candidates.append(y_cord)

    # For the frames of the bottom-most strip, always snip at co-ordinate
    # 'height'.
    y_candidates.append(height)

    # The second stage of the script. We start splitting the image along the
    # y-axis.
    strips = []
    crop_at = start_at = 0
    # start by examining the candidate co-ordinates ...
    if debug: print "y candidates: ", y_candidates
    for i, y_cord in enumerate(y_candidates):
        if y_cord == 0:
            continue
        crop_at = y_cord
        # If the current candidate co-ordinate is too close to the start
        # co-ordinate (ie: difference is less than 10px) skip it.
        if (crop_at - start_at) < 10:
            continue
        # If the current candidate co-ordinate is too close to the next one
        # (ie: difference is less than 10px) skip it.
        if (i+1 < len(y_candidates)) and ((y_candidates[i+1] - y_cord) < 10):
            crop_at = y_candidates[i+1]
            continue
        else:
            if debug: print "crop()ing at ", (0, start_at, width, crop_at)
            c = img.crop((0, start_at, width, crop_at))
            #c.show()
            strips.append(c)
            start_at = crop_at

    # Now take each individually split 'strip' and split it along the x-axis

    # To do this we apply the same logic as above to guess the possible
    # co-ordinates for the frames.
    frames = []
    for strip in strips:
        bw_strip = strip.convert('1')
        width, height = strip.size[0], strip.size[1]
        x_candidates = []
        for x_cord in range(width):
            color_map = gen_map_on_xaxis(bw_strip, x_cord)
            if (len(color_map.keys()) < 2):
                x_candidates.append(x_cord)

        # For the left-most frames of each strip always snip at co-ordinate
        # 'width'.
        x_candidates.append(width)

        if debug: print "x candidates: ", x_candidates
        crop_at = start_at = 0
        for i, x_cord in enumerate(x_candidates):
            if x_cord == 0:
                continue
            crop_at = x_cord
            if (crop_at - start_at) < 10:
                continue
            if (i+1 < len(x_candidates)) and ((x_candidates[i+1] - x_cord) < 10):
                crop_at = x_candidates[i+1]
                continue
            else:
                if debug: print "crop()ing at ", (start_at, 0, crop_at, height)
                c = strip.crop((start_at, 0, crop_at, height))
                # c.show()
                frames.append(c)
                start_at = crop_at

    for index, frame in enumerate(frames):
        frame_name = os.path.join(odir, "%.2d-%s" % (index, ofile))
        print "writing frame %d as %s" % (index, frame_name)
        fl = open(frame_name, 'w')
        frame.save(fl)
        fl.close()

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print usage
        sys.exit(1)
    for f in sys.argv[1:]:
        try:
            snip(f)
        except IOError, e:
            if e.errno == 2:
                print "Error writing out output file"
                print usage

