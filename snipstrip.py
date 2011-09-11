#!/usr/bin/python
# Copyright 2007 by Steven Fernandez <steve@lonetwin.net>
#
# This program is free software; you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free Software
# Foundation; either version 2 of the License, or (at your option) any later
# version.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE.  See the GNU General Public License for more
# details.
#
# You should have received a copy of the GNU General Public License along with
# this program.  If not, see <http://www.gnu.org/licenses/>.
#
# This program has been modified by the following people for Podhurl Inc.
#
# Robin Monks <devlinks AT gmail DOT com>
"""
This module provides the ComicPage class which exports methods to split images
of comic pages into individual rows or frames thus making it easier to read
comics on handheld devices such as mobile phones, PDAs and handheld multimedia
players.
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
    raise

DEBUG = False

class ComicPage:
    """ Represents a single 'Page' of the comic.

    Terminology used in the code and comments:
    Assuming that this is a comic page image ...

  (0,0)-------------------------3-----+-\
    |         | |         | |         | |
    |    1    |2|         | 4         | 6
    |         | |         | |         | |
    |         | |         | |         | |
    |=========   ====5====   =========|=/
    |         | |         | |         |
    |         | |         | |         |
    |         | |         | |         |
    |         | |         | |         |
    +---------------------------(width,height)

    The entire thing above - Page
    1 - A single Frame
    2 - A vertical gutter
    3 - A point in the X-candidates list
    4 - A point in the Y-candidates list
    5 - A horizontal gutter
    6 - A single row
    """

    def __init__(self, filename):
        """ open() filename and get size information """

        self.odir, self.ofile = os.path.split(os.path.abspath(filename))
        self.page = Image.open(filename)
        # (0, 0) == (top, left)
        self.width, self.height = self.page.size
        # Convert to monochrome (easier to create a color map)
        self.mono_page = self.page.convert(mode="1")
        # list of rows in self.page. Each row is represented as a pair of
        # diagonal points in the form of a flattened tuple
        # (top, left, bottom, right)
        self.rows   = []
        # dict of frames within a row (keyed by row tuple)
        self.frames = {}

    def __gen_map_for_ycord(self, y_cord):
        """ __gen_map_for_ycord(y_cord) -> {color1: [(x1, y1), ...], ...}

        Given a y-coordinate, returns a map of colors found along the line
        (0, y_cord) to (width, y_cord).

        ie: a map with colors as keys and list of points where the color
        was found as the values.
        """
        color_map = {}
        for x_cord in range(self.width):
            color = self.mono_page.getpixel((x_cord, y_cord))
            color_map[color] = color_map.get(color, [])
            color_map[color].append((x_cord, y_cord))
        return color_map

    def __gen_map_for_xcord(self, x_cord, row):
        """ __gen_map_for_xcord(x_cord, row) -> {color1: [(x1, y1), ...], ...}

        Given a x-coordinate and a row (as generated by get_by_row()), returns
        a map of colors found along the line
        (x_cord, row_top) to (x_cord, row_height).

        ie: a map with colors as keys and list of points where the color
        was found as the values.
        """
        color_map = {}
        for y_cord in range(row[1], row[3]):
            color = self.mono_page.getpixel((x_cord, y_cord))
            color_map[color] = color_map.get(color, [])
            color_map[color].append((x_cord, y_cord))
        return color_map

    def get_by_row(self):
        """ get_by_row() -> [row1, ...]

        This method returns a list of frame rows, where a 'row' is a diagonal
        pair of points enclosing the row, which one may pass to crop() to
        obtain the row -- [(top, left, bottom, right), ...]
        """
        y_candidates = []
        # iterate over each y co-ordinate on the page ...
        for y_cord in range(self.height):
            # ...generate a color_map for all points on the x-axis for this
            # y_cord.
            color_map = self.__gen_map_for_ycord(y_cord)
            # Now, if there was just one color all along the x-axis (ie:
            # len(color_map) == 1), it is quite likely this y-coordinate is
            # part of a horizontal gutter.
            # We'll add the y_cord to the y_candidates list
            if (len(color_map.keys()) == 1):
                y_candidates.append(y_cord)

        # For the frames of the bottom-most strip, always assume 'self.height'
        # as the last 'candidate'
        y_candidates.append(self.height)

        # Now we filter out the candidate closest to the end of the gutter
        # XXX note side effect: self.rows is populated
        self.find_gutters('horizontal', y_candidates)

        if DEBUG:
            print "Number of rows in this comic: %d" % len(self.rows)
            print "The rows are: %s" % self.rows
            for row in self.rows:
                self.page.crop(row).show()
                raw_input("press any key to continue ...")

        # all done !
        return self.rows

    def get_by_frame(self, row):
        """ get_by_frame(row) -> [frame1, ...]

        Given a 'row' (in the manner returned by get_by_row()), this method
        returns a list of frames within the row. Each frame represented as the
        set of diagonal co-ordinates, where you may crop() to obtain the frame,
        ie: [(top, left, bottom, right), ...]
        """
        x_candidates = []
        # iterate over each x co-ordinate in the row...
        for x_cord in range(row[0], self.width):
            # generate a color_map for all points on the y-axis for this
            # x_cord.
            color_map = self.__gen_map_for_xcord(x_cord, row)
            # Now, if there was just one color all along the y-axis (ie:
            # len(color_map) == 1), it is quite likely this x-coordinate is
            # part of a vertical gutter.
            # We'll add the x_cord to the x_candidates list
            if (len(color_map.keys()) == 1):
                x_candidates.append(x_cord)

        # For the frames at the right-most part of the strip, always assume
        # 'self.width' as the last 'candidate'
        x_candidates.append(self.width)

        # Now we filter out the candidate closest to the end of the gutter
        # XXX note side effect: self.frames is populated
        self.find_gutters('vertical', x_candidates, row)

        if DEBUG:
            print "Number of frames in this row %s are %d" % \
                                    (row, len(self.frames[row]))
            print "The frames are: %s" % self.frames[row]
            for frame in self.frames[row]:
                self.page.crop(frame).show()
                raw_input("press any key to continue ...")
        return self.frames

    def find_gutters(self, gtype, candidates, row=None):
        """ find_gutters(gtype, candidates, row=None) -> None

        The workhorse of this class. Given the gutter-type to find (either
        'horizontal' or 'vertical') and a list of candidate points, this
        method filters out the actual gutters along which one might 'snip'.
        The method sets self.rows/self.frames.

        row is required for snipping frames from rows correctly ! Ugly, I know
        """
        assert(gtype in ('horizontal', 'vertical'))
        if gtype == 'vertical':
            if row == None:
                raise("asked to find vertical gutters, but row is missing")
            else:
                self.frames[row] = []

        # We have a list of candidates for the gutters, we need to filter out
        # the 'best' coordinate to snip along. We do this by:
        # a. Selecting the first from a group of possibly adjacent points
        #    (where adjacent means difference <5px hard coded, ugly I know!)
        #
        # b. If we are sufficiently far (>5px hard coded, ugly, I know!) from
        #    the previous candidate, we assume that we are in the next gutter,
        #    (ie: we assume that we have a row or a frame between the current
        #    and the previous candidate), so, the previous candidate was the
        #    'best' coordinate.
        gutter_start = gutter_end = 0
        # start examining the candidate co-ordinates ...
        for index, gutter_end in enumerate(candidates):
            # If the current candidate is 0 or is too close to the start
            # co-ordinate (ie: difference is less than 5px) skip it.
            if (gutter_end == 0) or ((gutter_end - gutter_start) < 5):
                continue
            # If the current candidate co-ordinate is too close to the next one
            # (ie: difference is less than 5px) skip it.
            if (index + 1 < len(candidates)) and \
                    ((candidates[index + 1] - gutter_end) < 5):
                continue
            else:
                if gtype == 'horizontal':
                    # save off the co-ordinates where we 'snip' this row
                    self.rows.append((0, gutter_start, self.width, gutter_end))
                elif gtype == 'vertical':
                    # save off the co-ordinates where we 'snip' this frame
                    self.frames[row].append((gutter_start, row[1], gutter_end, row[-1]))
                gutter_start = gutter_end

    def process(self):
        """ process() -> None

        Populate self.rows and self.frames
        """
        # From each row ...
        for index, row in enumerate(self.get_by_row()):
            if DEBUG:
                print "extracting frames from row %d (%s)" % (index, row)
            # ...snip each frame
            self.get_by_frame(row)

    def write_to_disk(self, filename, row_or_frame):
        """ write_to_disk(row_or_frame) -> None

        Writes out the row or frame to disk.
        """
        fl = open(filename, 'w')
        cropped = self.page.crop(row_or_frame)
        cropped.save(fl)
        fl.close()

    def create_files(self, split_by='row'):
        """ create_files(split_by='row') -> None

        Splits the page by 'row' or 'frame' and creates files named with a two
        digit number prefix in the same directory as the image file.
        """
        assert(split_by in ('row', 'frame'))
        if split_by == 'row':
            for index, row in enumerate(self.get_by_row()):
                fname = os.path.join(self.odir, "%.2d-%s" % (index, self.ofile))
                self.write_to_disk(fname, row)
        else:
            self.process()
            index = 0
            for row in self.rows:
                for frame in self.frames[row]:
                    fname = os.path.join(self.odir, "%.2d-%s" % (index, self.ofile))
                    self.write_to_disk(fname, frame)
                    index += 1

    def dump_data(self):
        """ dump_data() -> <ComicPage DATA>

        returns the data obtained after calling process()
        (format yet to be decided)
        """
        pass

usage = """%s <filename> [...]
    where the arguments are comic strip images.""" % sys.argv[0]

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print usage
        sys.exit(1)
    for f in sys.argv[1:]:
        c = ComicPage(f)
        c.process()
        # c.create_files(split_by='row')
         c.create_files(split_by='frame')
else:
    DEBUG = False
