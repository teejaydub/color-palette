""" color_palette.py
    Generates colors that harmonize well.
    Uses perceptually-based colorspaces.

    A palette is completely defined by its starting color, and you can generate arbitrary
    numbers of colors in the palette.  Effort is made to keep each color both harmonized
    with the rest of the palette and distinguishable from all other colors previously
    generated - though this gets difficult as the size of the palette increases.

    The first 6 colors are quite "good" by these metrics; the next 6, pretty good, etc.

    Currently samples the hue space six times with the same saturation and value,
    then repeats that with interleaved hue values with varying values and then saturations.

    Colors are represented as "RGB byte triples" (a tuple of red, green, and blue values from 0-255),
    "RGB float triples" (the same but using floating-point values from 0.0 - 1.0),
    "HSV float triples" (like RGB float triples but in the HSV space),
    and "HTML hex codes" (as a string like "#010101").
"""

import colorsys
import math

HUE_STEPS = 6  # Number of discernible colors in the hue space.
HUE_STEP = 1.0 / HUE_STEPS  # In the HSV space of 0 - 1.
MIN_VALUE = 0.5  # The minimum usable Value, below which things get murky.
MAX_VALUE = 0.9
MIN_SATURATION = 0.2
MAX_SATURATION = 1.0

class Color(): 
    """ Expresses a color in a variety of formats, converting between them.
    """

    def __init__(self, x = '#000000'):
        """ Initializes via either an RGB byte triple or an HTML hex code. 
        """
        if isinstance(x, basestring):
            self.set_html_hex(x)
        else:
            self.set_rgb_bytes(x)

    def set_rgb_bytes(self, rgb_bytes):
        """ Sets this color to the given RGB byte triple. 
        """
        self._r = rgb_bytes[0]
        self._g = rgb_bytes[1]
        self._b = rgb_bytes[2]

    def set_html_hex(self, h):
        """ Sets this color to the given HTML hex code.
            The leading '#' is tolerated but optional.
        """
        if h[0] == '#':
            s = h[1:]
        else:
            s = h

        self._r = int(s[0:2], 16)
        self._g = int(s[2:4], 16)
        self._b = int(s[4:6], 16)

    def set_hsv(self, hsv_float):
        """ Sets this color as an HSV float triple.
        """
        self.set_rgb_float(colorsys.hsv_to_rgb(hsv_float[0], hsv_float[1], hsv_float[2]))

    def set_rgb_float(self, rgb_float):
        """ Sets this color as an RGB float triple.
        """
        self._r = max(0, min(255, int(round(rgb_float[0] * 255))))
        self._g = max(0, min(255, int(round(rgb_float[1] * 255))))
        self._b = max(0, min(255, int(round(rgb_float[2] * 255))))

    def get_rgb_bytes(self):
        """ Returns this color as an RGB byte triple.
        """
        return (self._r, self._g, self._b)

    def get_rgb_float(self):
        """ Returns the color as an RGB float triple.
        """
        return (self._r / 255.0, self._g / 255.0, self._b / 255.0)

    def get_hsv(self):
        """ Returns the color as an HSV float triple.
        """
        return colorsys.rgb_to_hsv(self._r / 255.0, self._g / 255.0, self._b / 255.0)

    def get_html_hex(self):
        """ Returns the color as an HTML hex code.
        """
        return '#{:02X}{:02X}{:02X}'.format(self._r, self._g, self._b)

def mean(a, b):
    """ Returns the arithmetic mean (simple average) of two numbers.
    """
    return (a + b) / 2.0

def rms(a, b, weights = None):
    """ Returns the root-mean-squared difference between all the values in corresponding members of two tuples.
        If weights is not None, weights each corresponding component accordingly, from 0.0 - 1.0.
    """
    d = [ai - bi for (ai, bi) in zip(a, b)]

    if weights is not None:
        d = [di * wi for (di, wi) in zip(d, weights)]

    x = sum(d)

    if x > 0: 
        return math.sqrt(x)
    else:
        return 0

def color_distance(a, b):
    """ Returns a single measure of the perceptual color distance between two colors.
        The smaller the value, the closer the colors are to each other.
    """
    return rms(a.get_hsv(), b.get_hsv(), (1.0, 0.5, 0.8))

def explore_range(min_val, max_val, start, i):
    """ Explores a one-dimensional space using progressively smaller steps, never repeating previous positions.
        i is the step number.
        At the zeroth step, returns the starting value.
        After that, traverses a progressively finer grid between min and max (inclusive).
        Returns the i-th element of the series, which will be within the range (min_val, max_val).
    """
    if i == 0:
        return start
    else:
        # Intervals go like this, starting with i = 1, 2, ...:
        # 1/2, 1/4, 1/4, 1/8, 1/8, 1/8, 1/8, 1/16...
        level = math.ceil(math.log(i + 1, 2))  # i = 1 => level = 1; 2 => 2; 3 => 2; 4 => 3...
        denominator = pow(2, level)  # 2, 4, 4, 8, 8, 8, 8, 16...

        # Positions go like this:
        # 1/2, 1/4, 3/4, 1/8, 3/8, 5/8, 7/8, 1/16, 3/16, 5/16...
        prev_level = level - 1  # 0, 1, 1, 2...
        prev_denominator = pow(2, prev_level)  # 1, 2, 2, 4, 4, 4, 4, 8, 8...
        level_i = i - prev_denominator  # 0, 0, 1, 0, 1, 2, 3, 0, 1, 2...
        odd_i = 1 + 2*level_i  # 1, 1, 3, 1, 3, 5, 7, 1, 3, 5...
        position = 1.0 * odd_i / denominator

        # Map that position to the interval from min to max, and make it relative to start.
        map_range = max_val - min_val
        mapped_start = start - min_val
        mapped_result = (mapped_start + position * map_range) % map_range
        return mapped_result + min_val

def explore_2d(min_x, max_x, min_y, max_y, start_x, start_y, i):
    """ Like explore_range, but moves within a two-dimensional space.
        Returns a tuple of x and y positions at each i.
    """
    # Generate this sequence for explore_range:
    # (0,0), 
    # (0,1), (1,1), (1,0), 
    # (0,2), (1,2), (2,2), (2,1), (2,0)
    # (0,3), (1,3), (2,3), (3,3), (3,2), (3,1), (3,0)
    # (0,4), (1,4), (2,4), (3,4), (4,4), (4,3), (4,2), (4,1), (4,0)
    # At each level, it adds a row and a column to a square grid, and adds the new cells from that row and column.
    dimension = math.floor(math.sqrt(i)) + 1  # 1, 2, 2, 2, 3, 3, 3, 3, 3, 4
    square = dimension*dimension  # 1, 4, 4, 4, 9, 9, 9, 9, 9, 16...
    last_dimension = dimension - 1  # 0, 1, 1, 1, 2, 2, 2, 2, 2, 3
    last_square = last_dimension*last_dimension  # 0, 1, 1, 1, 4, 4, 4, 4, 4, 9
    i_level = i - last_square  # 0, 0, 1, 2, 0, 1, 2, 3, 4, 0, 1...
    if (i_level < last_dimension):
        # Move in x
        x = i_level
        y = last_dimension
    else:
        # Move in Y
        x = last_dimension
        y = 2 * last_dimension - i_level
    return (explore_range(min_x, max_x, start_x, x), (min_y, max_y, start_y, y))

def get_color(start_color, i):
    """ Given a starting Color, generate the i-th color in the palette.
        If i is 0, returns start_color.
    """
    (h, s, v) = start_color.get_hsv()
    result = Color()

    hstep = i % HUE_STEPS
    svstep = i / HUE_STEPS

    h = (h + hstep * HUE_STEP + explore_range(0, HUE_STEP, 0, svstep)) % 1.0
    (s, v) = explore_2d(MIN_SATURATION, MAX_SATURATION, MIN_VALUE, MAX_VALUE, s, v, svstep)

    result.set_hsv((h, s, v))
    return result

def old_one():
    (h, s, v) = start_color.get_hsv()
    result = Color()

    # There are really only about 5 * HUE_STEPS distinguishable colors (at most).
    # So, start over after that.
    i = i % (5 * HUE_STEPS)

    if i == 0:
        result = start_color
    elif i < HUE_STEPS:
        # The first several colors have the same S and V, and evenly-spaced hues.
        h = (h + i * HUE_STEP) % 1.0
    elif i < HUE_STEPS * 2:
        # The next set move in Value toward the further bound from the current,
        # and are offset in Hue by a half a hue step.
        h = (h + (i + 0.5) * HUE_STEP) % 1.0
        if v > mean(MIN_VALUE, MAX_VALUE):
            # Reduce Value.
            v = mean(MIN_VALUE, v)
            s = mean(s, MAX_SATURATION)
        else:
            # Increase Value.
            v = mean(v, MAX_VALUE)
            s = mean(MIN_SATURATION, 0)
    elif i < HUE_STEPS * 3:
        # The next set move in the opposite direction in the Value region,
        # and are offset in Hue by a quarter of a hue step.
        h = (h + (i + 0.25) * HUE_STEP) % 1.0
        if v <= mean(MIN_VALUE, MAX_VALUE):
            # Reduce Value.
            v = mean(MIN_VALUE, v)
            s = mean(s, MAX_SATURATION)
        else:
            # Increase Value.
            v = mean(v, MAX_VALUE)
            s = mean(MIN_SATURATION, 0)
    elif i < HUE_STEPS * 4:
        # The next set move to the extreme Value,
        # and are offset in Hue by two-thirds of a hue step.
        h = (h + (i + 0.66) * HUE_STEP) % 1.0
        if v > mean(MIN_VALUE, MAX_VALUE):
            # Reduce Value.
            v = MIN_VALUE
            s = MAX_SATURATION
        else:
            # Increase Value.
            v = MAX_VALUE
            s = MIN_SATURATION
    elif i < HUE_STEPS * 5:
        # The next set move to the other extreme Value,
        # and are offset in Hue by one-thirds of a hue step.
        h = (h + (i + 0.33) * HUE_STEP) % 1.0
        if v <= mean(MIN_VALUE, MAX_VALUE):
            # Reduce Value.
            v = MIN_VALUE
            s = MAX_SATURATION
        else:
            # Increase Value.
            v = MAX_VALUE
            s = MIN_SATURATION

    result.set_hsv((h, max(MIN_SATURATION, min(MAX_SATURATION, s)), max(MIN_VALUE, min(MAX_VALUE, v))))
    return result

def get_palette(start_color, length):
    """ Return a list of all the colors in the palette of the given length,
        starting with the given color.
    """
    return [get_color(start_color, i) for i in range(length)]

if __name__ == "__main__":
    def outputColor(c, label):
        print "<div style='background-color: {};'>{} = {}</div>".format(c.get_html_hex(), label, c.get_html_hex())

    # Unit test: generate a palette of 24 colors and display them in HTML.
    base_color = Color('#EACE8C')
    print "<html><body>"
    outputColor(base_color, 'Base color')

    print "<h2>Palette</h2>"
    for i, c in enumerate(get_palette(base_color, 6 * HUE_STEPS)):
        outputColor(c, str(i+1))

    print "<h2>Palette sorted by similarity</h2>"
    for i, c in enumerate(sorted(get_palette(base_color, 6 * HUE_STEPS), key=lambda c: color_distance(c, base_color))):
        outputColor(c, str(i+1))

    print "</body></html>"
