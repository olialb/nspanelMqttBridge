# python
#
# This file is part of the NspanelMqttBridge distribution
# (https://github.com/olialb/NspanelMqttBridge).
# Copyright (c) 2026 Oliver Albold.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, version 3.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.
#
"""
Module implements a MQTT client as bridge to openhab for NsPanels with lovelace ui
This file contain some small helper functions
"""
import math
import webcolors

#project imports
from file_logger import file_logger as FLOGGER

#
# global constants
#
LOGGER = FLOGGER.create_logger("Helpers")
#
# some helper functions
#

def int2ordinal(n: int):
    """Convert an integer into its ordinal representation"""
    if 11 <= (n % 100) <= 13:
        suffix = 'th'
    else:
        suffix = ['th', 'st', 'nd', 'rd', 'th'][min(n % 10, 4)]
    return str(n) + suffix


def map_state_pannel2oh(state_type, state):
    """
    maps the state value of the ns panel to an openhab state value
    """
    ret = state
    if state_type == 'OnOff' or state_type.lower() == 'switch':
        #switch state type
        if state in ['1', 1]:
            ret = 'ON'
        else:
            ret = 'OFF'
    if state_type.lower() == 'shutter':
        if state.lower() in ['up','stop','down']:
            ret = state.upper()
    if state_type.lower() == 'tilt':
        if state.lower() == 'tiltclose':
            ret = "DOWN"
        if state.lower() == 'tiltstop':
            ret = "STOP"
        if state.lower() == 'tiltopen':
            ret = "UP"
    return ret

def map_state_oh2panel(state_type, state):
    """
    maps the state value of the ns panel to an openhab state value
    """
    if state_type == 'OnOff' or state_type.lower() == 'switch':
        #switch state type
        if state == 'ON':
            return '1'
        return '0'
    return state

def interpret_icon(data):
    """
    Interpret the icon definition as a string which represents a unicode icon and retrun ut as unicode
    """
    string = str(data) #make a string in case string is of type number
    if string[:2] in ["\\u", "\\h"]:
        #string starts with a hex or unicode coding characters
        try:
            return chr(int(string[2:],16))
        except ValueError:
            LOGGER.error("interpret_icon: Unsupported icon value %s", string)
    if len(string) == 1:
        #string is only one character long, return it as unicode
        return string
    return "?" #show a question mark if the icon could not be interpreted

def interpret_options( options ):
    """
    create from an option list an dictionary.
    Example option list: TUNER=Radio,PHONO=Plattenspieler,AV1=PS3,AV2=vu2+,AV3,AV4=AV4,AV5=AV5,AV6=AV6,Bluetooth=Bluetooth,USB=USB,NET RADIO=NET RADIO,AUDIO1=Fernseher
    """
    d={}
    for option in options.split(","):
        v = option.split("=")
        if len(v) > 1:
            d[v[0].strip().upper()] = v[1].strip()
        else:
            d[option.strip().upper()] = option.strip()
    return d

def color16to24bits(value):
    """
    covert 16 bit color to 24 bit color
    """
    top5bits = value >> 11
    if top5bits == 0b11111:
        # round up if max => preserve maxed out red
        red = 0xff
    elif top5bits == 0:
        # round down if min
        red = 0
    else:
        red = (top5bits << 3) + int(0b111 / 2) # interpolate missing bits with average

    middle6bits = (value >> 5) &  0b111111
    if middle6bits == 0b111111:
        # round up if max => preserve maxed out green
        green = 0xff
    elif middle6bits == 0:
        # round down if min
        green = 0
    else:
        green = (middle6bits << 2) + int(0b11 / 2) # interpolate missing bits with average

    low5bits = value & 0b11111
    if low5bits == 0b11111:
        # round up if max => preserve maxed out blue
        blue = 0xff
    elif low5bits == 0:
        # round down if min
        blue = 0
    else:
        blue = (low5bits << 3) + int(0b111 / 2) # interpolate missing bits with average

    return [red,green,blue]

def color24to16bits(rgb):
    """
    converts an array of rgb values to a 16bit color value
    """
    return ((rgb[0] >> 3) << 11) + ((rgb[1] >> 2) << 5) +  (rgb[2] >> 3)

def name_to_rgb(name):
    """
    converts a color name to a rgb list value based on webcolors
    """
    name = str(name).strip()
    try:
        if name[0] == '#':
            #seams to be hex color
            color= webcolors.hex_to_rgb(webcolors.normalize_hex(name))
        else:
            #seams to be a color name
            color = webcolors.name_to_rgb(name)
    except ValueError:
        LOGGER.debug("Webcolor '%s' is not defined. White used instead!", name)
        color = webcolors.name_to_rgb("white")
    return color

def name_to_16bit_color(name):
    """
    converts a color name to a 16bit color value
    """
    return color24to16bits(name_to_rgb(name))

def rad_2_deg(rad):
    """
    converts radians to degrees
    """
    return (90 + (180 * rad) / math.pi) % 360

def pos_to_hs_color(x, y):
    """
    Convert colorwheel position to HS part of HSB color.
    Default color spave for openhab is HSB (Hue, Saturation, Brightness)
    The ns panel uses a color wheel with x and y coordinates.
    This function converts the x and y coordinates to a degree (hue) and radius (saturation) value on the color wheel.
    """
    colorweel_diameter = 160.0
    #x and y range is 0-160 because colorweel has a diameter of 160px. The center of the colorwheel is at (80,80).
    x=max(x, 0)
    y=max(y, 0)
    x=min(x, colorweel_diameter)
    y=min(y, colorweel_diameter)

    r = colorweel_diameter / 2.0
    #pos_x = round((x - r) / r * 100) / 100 #180,90,0,270
    #pos_y = round((y - r) / r * 100) / 100
    pos_x = round((r - x) / r * 100) / 100 #0,90,180,270
    pos_y = round((r - y) / r * 100) / 100
    #calculate hue as angle of the position on the color wheel
    hue = rad_2_deg(math.atan2(pos_x, pos_y))

    r = math.sqrt(pos_x * pos_x + pos_y * pos_y)
    if r > 1:
        sat = 100
    else:
        sat = r*100

    return str(hue) +','+ str(sat)
