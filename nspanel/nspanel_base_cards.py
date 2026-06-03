# python
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
This file contain the differnt base classe for cards shown in the panel.
"""

#general imports

# project specific imports:
from file_logger import file_logger as FLOGGER
from lang import translate
from skin import skin

#
# global constants
#

#
# Class definitions
#
class NSPanelCard():
    """
    base class for an nspanel
    """
    MY_TYPE = "NSPanelCard"

    #CARD TYPE constants
    CARD_ENTITIES="cardEntities"
    CARD_THERMO="cardThermo"
    CARD_MEDIA="cardMedia"
    CARD_ALARM="cardAlarm"
    CARD_QR="cardQR"
    CARD_POWER="cardPower"
    CARD_SCREENSAVER="screensaver"
    CARD_SCREENSAVER2="screensaver2"
    CARD_GRID="cardGrid"
    CARD_GRID2="cardGrid2"
    CARD_CHARD="cardChart"
    CARD_STATUS="statusCard"
    CARD_POPUP_NOTIFY="popupNotify"
    CARD_DEFAULT_STATUS="_default_status_"
    FONT_SIZES = ["0","1","2","3","4","5"]

    #special card groups
    CARDS_HOME = "home"
    STATUS_CARD_GROUP = "_status_cards_"
    NOTIFY_CARD_GROUP = "_notify_cards_"

    # all derived classes from the base class
    card_types = {}
    #All cards by their group
    cards_by_group = {}
    #translator
    translator = None
    #skin
    skin = None
    #global list for panals which are connected to openhab
    all_connected_panels = {}
    #List of all panels by their name
    all_panels = {}
    #global card logger
    log = FLOGGER.create_log_handler("NSPanelcard")

    @classmethod
    def set_translator_db( cls, db):
        """
        set translator db
        """
        translate.set_transloator_db( db )

    @classmethod
    def set_skin_db( cls, db):
        """
        set skin db
        """
        skin.set_skin_db( db )

    def __init__(self, name, group=CARDS_HOME ):
        """
        Constructor of a NSPanel card
        """
        #nspanel root topic
        self.name = str(name) #to ensure that name is of type string
        self.type = None
        self.group = group
        self.title = self.name
        self.icon_size = skin.key(self.MY_TYPE, "iconSize")
        self.connected_panels = {}

        #popup card handling
        self.popup = None #point to the popup card if a popup opened
        self.log.debug("Constructed!" )

    def icon_size_payload(self):
        """
        create payload for icon size. Must be overridden in sub class if icon size is not supported
        """
        if self.icon_size is not None:
            return '¬'+str(self.icon_size)
        return ""

    def next(self, i=None):
        """
        find next main card in list to this one
        """
        card_names = list(self.cards_by_group[self.group].keys())
        if len(card_names) < 0:
            #only one card in this group
            return self

        if i is None:
            #find index of current card
            i = card_names.index(self.name.lower())

        if i+1 >= len(card_names):
            next_i = 0
        else:
            next_i = i+1
        #jump over screensavers
        if self.cards_by_group[self.group][card_names[next_i]].MY_TYPE in [NSPanelCard.CARD_SCREENSAVER, NSPanelCard.CARD_SCREENSAVER2]:
            return self.next(next_i)
        return self.cards_by_group[self.group][card_names[next_i]]


    def previous(self, i=None):
        """
        find previous main card in list to this one
        """
        card_names = list(self.cards_by_group[self.group].keys())
        if len(card_names) < 0:
            #only one card in this group
            return self

        if i is None:
            #find index of current card
            i = card_names.index(self.name.lower())

        if i > 0:
            next_i = i-1
        else:
            next_i = len(card_names)-1

        #jump over screensavers
        if self.cards_by_group[self.group][card_names[next_i]].MY_TYPE in [NSPanelCard.CARD_SCREENSAVER, NSPanelCard.CARD_SCREENSAVER2]:
            return self.previous(next_i)
        return self.cards_by_group[self.group][card_names[next_i]]

    def attrib( self, info, dictionaries, name):
        """
        helper method to get an attribute value.
        if attribute does not exist in dict an empty string is retuned and a error log is generated
        """
        if name in dictionaries:
            return str(dictionaries[name])
        self.log.error("No '%s' attribute defined in %s.", name, info )
        return ""

    def load_card_yaml(self, card_yaml):
        """
        Loads the panel definition from yaml dictionary
        """
        self.log.debug("Load card yaml: %s",str(card_yaml))
        if "type" in card_yaml and card_yaml["type"] is not None:
            self.type = str(card_yaml["type"])
        else:
            self.log.error("Attribute 'type' not defined in card %s", self.name )
            return False

        self.title = self.name
        if "title" in card_yaml and card_yaml["title"] is not None:
            #replace title with the title from the yaml otherwise use the name as title
            self.title = str(card_yaml["title"])

        #the attribute icon_size is controlled over the skin file. If its in the skin you can also override it.
        if self.icon_size is not None and "iconSize" in card_yaml and card_yaml["iconSize"] is not None:
            if skin.key("iconSize", str(card_yaml["iconSize"]).lower()) is not None:
                self.icon_size = skin.key( "iconSize", str(card_yaml["iconSize"]).lower())
            else:
                if card_yaml["iconSize"] in skin.key("iconSizeRange"):
                    self.icon_size = card_yaml["iconSize"]
                else:
                    self.log.error("Invalid icon size '%s' defined in card '%s'. Value will be ignored.", card_yaml["iconSize"], self.name )

        return True

    def create_color_payload(self):
        """
        Must be implemented in sub class
        """
        return None

    def create_update_payload(self):
        """
        Must be implemented in sub class
        """
        return None

    def create_cmd_payload(self):
        """
        Must be implemented in sub class
        """
        return None

    @classmethod
    def factory_yaml_file( cls, filename, card_yaml ): #pylint: disable=too-many-branches
        """
        Instantiate classes for a card definition in a yaml file and add them to the card list. Returns true if an error occurred during the process.
        """
        error = True
        cls.log.debug("Create new card from file '%s' data '%s'", filename, str(card_yaml))
        if "name" in card_yaml: #pylint: disable=too-many-nested-blocks
            if "type" in card_yaml and card_yaml["name"] is not None:
                if card_yaml["type"] in cls.card_types:
                    #construct corresponding card type
                    if "group" not in card_yaml or card_yaml["group"] is None:
                        group_list = [NSPanelCard.CARDS_HOME]
                    else:
                        group_list = str(card_yaml["group"]).split(',')
                    #create a card object in each card group where its assigned to
                    for group in group_list:
                        group = group.strip()
                        card = cls.card_types[card_yaml["type"]](card_yaml["name"],group)
                        if(card is not None and card.load_card_yaml( card_yaml )):
                            cls.log.debug("Add new card '%s' to panel group: %s", card.name, card.group)
                            if card.group not in cls.cards_by_group:
                                cls.cards_by_group[card.group] = {}
                            if card_yaml["name"].lower() not in cls.cards_by_group[card.group]:
                                cls.cards_by_group[card.group][card_yaml["name"].lower()] = card
                                cls.log.info("Card '%s' in file '%s' created for group '%s'.", card_yaml["name"], filename, card.group)
                                error = False
                            else:
                                cls.log.error("Card '%s' in file '%s exists already in card group '%s'.", card_yaml["type"], filename, card.group)
                        else:
                            cls.log.error("Card '%s' in file '%s could not be created'.", card_yaml["type"], filename)
                else:
                    cls.log.error("Unknown card type '%s' in file '%s'.", card_yaml["type"], filename)
            else:
                cls.log.error("Attribute 'type' not defined in file '%s'.", filename)

        else:
            cls.log.error("Attribute 'name' not defined in file '%s'.", filename)
        return error

    @classmethod
    def factory( cls, card_type, slot ):
        """
        factory for popup cards
        """
        cls.log.debug("Create card type '%s' for '%s'", card_type, slot.name)

        if card_type in cls.card_types:
            return cls.card_types[card_type](slot.name, slot)
        return None

    @classmethod
    def get_card( cls, group_name, card_name):
        """
        returns the card object by group and name
        """
        cls.log.debug("Get card '%s' from group '%s'", card_name, group_name)
        group_name = group_name.lower()
        card_name = card_name.lower()

        if group_name in cls.cards_by_group:
            if card_name in cls.cards_by_group[group_name]:
                return cls.cards_by_group[group_name][card_name]
            cls.log.debug("get_card: Unknown card '%s' in group '%s'", card_name, group_name)
        else:
            cls.log.warning("get_card: Unknown card group '%s'", group_name)
        return None

    @classmethod
    def get_first_card( cls, group_name):
        """
        returns the first card in this group
        """
        cls.log.debug("Get first card for group '%s'", group_name)
        group_name = group_name.lower()

        if group_name in cls.cards_by_group:
            i=0
            cards = list(cls.cards_by_group[group_name].values())
            while len(cards) > i and cards[i].type in [NSPanelCard.CARD_SCREENSAVER, NSPanelCard.CARD_SCREENSAVER2]:
                i=i+1
            if len(cards) > i:
                return cards[i]
            cls.log.warning("Card group '%s' has no card inside", group_name)
        else:
            cls.log.warning("get_first_card: Unknown card group '%s'", group_name)
        return None


class NSPanelCardWithNav(NSPanelCard):
    """
    Base class for cards with nav icon left and right
    """
    MY_TYPE = "cardWithNav"

    def create_update_payload(self):
        """
        Create nav card payload
        """
        #check how many cards exist in this card
        if len(NSPanelCard.cards_by_group[self.group]) > 1:
            #OK generate left right navigation buttons
            left_icon = skin.key( NSPanelCardWithNav.MY_TYPE, "icon_left")
            right_icon = skin.key( NSPanelCardWithNav.MY_TYPE, "icon_right")
            return "entityUpd~"+self.title+"~button~navigate.prev~"+left_icon+"~65535~~~button~navigate.next~"+right_icon+"~65535~~"
        return "entityUpd~"+self.title+"~~~~~~~~~~~~"

    def create_cmd_payload(self):
        """
        create command payload to switch to this card type
        """
        return "pageType~"+self.MY_TYPE

    def event_button_press( self, params):
        """
        process a button press event for this card
        """
        #example event params:
        #navigate.prev,button"

        #check for navigate card events
        if params[0] == "navigate.next" and params[1] == 'button':
            return self.next()
        if params[0] == "navigate.prev" and params[1] == 'button':
            return self.previous()
        self.log.warning("Event not processed for '%s'", str(params))
        return None
