#!/usr/bin/python

#luma.oled library used: https://github.com/rm-hull/luma.oled

try:
    from luma.core.interface.serial import spi, i2c
except ImportError:
    from luma.core.serial import spi, i2c #Compatilibity with older luma.oled version
from luma.core.render import canvas

from threading import Lock

from backlight import *

from ..output import GraphicalOutputDevice, CharacterOutputDevice


class LumaScreen(GraphicalOutputDevice, CharacterOutputDevice, BacklightManager):
    """An object that provides high-level functions for interaction with display. It contains all the high-level logic and exposes an interface for system and applications to use."""

    #buffer = " "
    #redraw_coefficient = 0.5
    current_image = None

    __base_classes__ = (GraphicalOutputDevice, CharacterOutputDevice)

    type = ["char", "b&w-pixel"] 
    cursor_enabled = False
    cursor_pos = (0, 0) #x, y

    def __init__(self, hw = "spi", port=None, address = 0, buffering = True, **kwargs):
        if hw == "spi":
            if port is None: port = 0
            try:
                self.serial = spi(port=port, device=address, gpio_DC=6, gpio_RST=5)
            except TypeError:
                #Compatibility with older luma.oled versions
                self.serial = spi(port=port, device=address, bcm_DC=6, bcm_RST=5)
        elif hw == "i2c":
            if port is None: port = 1
            if isinstance(address, basestring): address = int(address, 16)
            self.serial = i2c(port=port, address=address)
        else:
            raise ValueError("Unknown interface type: {}".format(hw))
        self.address = address
        self.busy_flag = Lock()
        self.width = 128
        self.height = 64
        self.char_width = 6
        self.char_height = 8
        self.cols = self.width / self.char_width
        self.rows = self.height / self.char_height
        self.init_display(**kwargs)
        BacklightManager.init_backlight(self, **kwargs)

    @enable_backlight_wrapper
    def enable_backlight(self):
        self.device.show()

    @disable_backlight_wrapper
    def disable_backlight(self):
        self.device.hide()

    @activate_backlight_wrapper
    def display_image(self, image):
        """Displays a PIL Image object onto the display
        Also saves it for the case where display needs to be refreshed"""
        with self.busy_flag:
            self.current_image = image
            self._display_image(image)

    def _display_image(self, image):
        self.device.display(image)

    def display_data_onto_image(self, *args, **kwargs):
        """
        This method takes lines of text and draws them onto an image,
        helping emulate a character display API.
        """
        cursor_position = kwargs.pop("cursor_position", None)
        if not cursor_position:
            cursor_position = self.cursor_pos if self.cursor_enabled else None
        args = args[:self.rows]
        draw = canvas(self.device)
        d = draw.__enter__()
        if cursor_position:
            dims = (self.cursor_pos[0] - 1 + 2, self.cursor_pos[1] - 1, self.cursor_pos[0] + self.char_width + 2,
                    self.cursor_pos[1] + self.char_height + 1)
            d.rectangle(dims, outline="white")
        for line, arg in enumerate(args):
            y = (line * self.char_height - 1) if line != 0 else 0
            d.text((2, y), arg, fill="white")
        return draw.image

    @activate_backlight_wrapper
    def display_data(self, *args):
        """Displays data on display. This function does the actual work of printing things to display.

        ``*args`` is a list of strings, where each string corresponds to a row of the display, starting with 0."""
        image = self.display_data_onto_image(*args)
        with self.busy_flag:
            self.current_image = image
            self._display_image(image)

    def home(self):
        """Returns cursor to home position. If the display is being scrolled, reverts scrolled data to initial position.."""
        self.setCursor(0, 0)

    def clear(self):
        """Clears the display."""
        draw = canvas(self.device)
        self.display_image(draw.image)
        del draw

    def setCursor(self, row, col):
        """ Set current input cursor to ``row`` and ``column`` specified """
        self.cursor_pos = (col * self.char_width, row * self.char_height)

    def createChar(self, char_num, char_contents):
        """Stores a character in the LCD memory so that it can be used later.
        char_num has to be between 0 and 7 (including)
        char_contents is a list of 8 bytes (only 5 LSBs are used)"""
        pass

    def noDisplay(self):
        """ Turn the display off (quickly) """
        pass

    def display(self):
        """ Turn the display on (quickly) """
        pass

    def noCursor(self):
        """ Turns the underline cursor off """
        self.cursor_enabled = False

    def cursor(self):
        """ Turns the underline cursor on """
        self.cursor_enabled = True

    def noBlink(self):
        """ Turn the blinking cursor off """
        pass
	
    def blink(self):
        """ Turn the blinking cursor on """
        pass

    def scrollDisplayLeft(self):
        """ These commands scroll the display without changing the RAM """
        pass

    def scrollDisplayRight(self):
        """ These commands scroll the display without changing the RAM """
        pass

    def leftToRight(self):
        """ This is for text that flows Left to Right """
        pass

    def rightToLeft(self):
        """ This is for text that flows Right to Left """
        pass

    def autoscroll(self):
        """ This will 'right justify' text from the cursor """
        pass

    def noAutoscroll(self):
        """ This will 'left justify' text from the cursor """
        pass
