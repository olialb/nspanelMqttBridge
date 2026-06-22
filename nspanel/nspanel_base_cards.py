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
from nspanel.nspanel_globals import name_to_16bit_color
from file_logger import file_logger as FLOGGER
from lang import translate
from skin import skin

#
# global constants
#
C_MODE_DEFAULT = "default"
C_MODE_FORK1 = "ioBroker.nspanel-lovelace-ui"

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
    CARD_SCHEDULE="cardSchedule"
    CARD_THERMO="cardThermo"
    CARD_THERMO2="cardThermo2"
    CARD_MEDIA="cardMedia"
    CARD_ALARM="cardAlarm"
    CARD_QR="cardQR"
    CARD_QR_WIFI="cardQRWifi"
    CARD_POWER="cardPower"
    CARD_MEDIA="cardMedia"
    CARD_SCREENSAVER="screensaver"
    CARD_SCREENSAVER2="screensaver2"
    CARD_SCREENSAVER3="screensaver3"
    CARD_GRID="cardGrid"
    CARD_GRID2="cardGrid2"
    CARD_GRID3="cardGrid3"
    CARD_CHARD="cardChart"
    CARD_STATUS="statusCard"
    CARD_POPUP_NOTIFY="popupNotify"
    CARD_POPUP_LIGHT = "popupLight"
    CARD_POPUP_INPUT_SEL = "popupInSel"
    CARD_POPUP_SHUTTER = "popupShutter"
    CARD_POPUP_THERMO = "popupThermo"
    #CARD_POPUP_3_INPUT_SEL = "popup3InSel" #Not supported in UIs
    CARD_POPUP_TIMER = "popupTimer"

    CARD_DEFAULT_STATUS="_default_status_"
    FONT_SIZES = ["0","1","2","3","4","5"]

    #special card groups
    CARDS_HOME = "home"
    STATUS_CARD_GROUP = "_status_cards_"
    NOTIFY_CARD_GROUP = "_notify_cards_"

    #compatibility modes
    COMPATIBILITY_MODE_DEFAULT = C_MODE_DEFAULT
    COMPATIBILITY_MODE_FORK1 = C_MODE_FORK1
    #card categories
    NAV_CARDS="navCards"
    POPUP_CARDS="popupCards"
    SCREENSAVER="scrennsaver"

    compatible_cards = {
        COMPATIBILITY_MODE_DEFAULT: { NAV_CARDS: [CARD_ENTITIES,CARD_THERMO,CARD_MEDIA,CARD_ALARM,
                                                  CARD_QR,CARD_QR_WIFI,CARD_POWER,CARD_MEDIA,
                                                  CARD_GRID,CARD_GRID2,CARD_CHARD ],
                                      SCREENSAVER: [CARD_SCREENSAVER,CARD_SCREENSAVER2],
                                      POPUP_CARDS: [CARD_POPUP_NOTIFY,CARD_POPUP_LIGHT,
                                                    CARD_POPUP_INPUT_SEL,CARD_POPUP_SHUTTER,CARD_POPUP_THERMO
                                                    ]
        },
        COMPATIBILITY_MODE_FORK1: { NAV_CARDS: [CARD_ENTITIES,CARD_THERMO,CARD_MEDIA,CARD_ALARM,
                                                  CARD_QR,CARD_QR_WIFI,CARD_POWER,CARD_MEDIA,
                                                  CARD_GRID,CARD_GRID2,CARD_GRID3, CARD_CHARD,
                                                   CARD_THERMO2,CARD_SCHEDULE ],
                                      SCREENSAVER: [CARD_SCREENSAVER,CARD_SCREENSAVER2,CARD_SCREENSAVER3],
                                      POPUP_CARDS: [CARD_POPUP_NOTIFY,CARD_POPUP_LIGHT,
                                                    CARD_POPUP_INPUT_SEL,CARD_POPUP_SHUTTER,CARD_POPUP_THERMO,
                                                    CARD_POPUP_TIMER ]
        }
    }

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
    #all time tick callbacks
    time_tick_callbacks = []

    #global card logger
    log = FLOGGER.create_log_handler("NSPanelcard")

    @classmethod
    def set_translator_db( cls, db):
        """
        set translator db
        """
        translate.set_translator_db( db )

    @classmethod
    def set_skin_db( cls, db):
        """
        set skin db
        """
        skin.set_skin_db( db )

    @classmethod
    def add_time_tick_callback(cls, callback):
        """
        adds a new time tick callback
        """
        cls.time_tick_callbacks.append(callback)

    @classmethod
    def time_tick(cls):
        """
        Time tick
        """
        for callback in cls.time_tick_callbacks:
            callback()

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
        if self.icon_size is not None and self.icon_size > 0:
            return '¬'+str(self.icon_size)
        return ""

    def next(self, panel, i=None):
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
        #jump over non navigation cards (screensavers...)
        if self.cards_by_group[self.group][card_names[next_i]].MY_TYPE not in NSPanelCard.compatible_cards[panel.compatibility_mode][self.NAV_CARDS]:
            return self.next(panel, next_i)
        return self.cards_by_group[self.group][card_names[next_i]]


    def previous(self, panel, i=None):
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

        #jump over non navigation cards (screensavers...)
        if self.cards_by_group[self.group][card_names[next_i]].MY_TYPE not in NSPanelCard.compatible_cards[panel.compatibility_mode][self.NAV_CARDS]:
            return self.previous(panel, next_i)
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
        self.log.error("create_color_payload(self) not implemented")

    def create_update_payload(self, compatibility=C_MODE_DEFAULT):
        """
        Must be implemented in sub class
        """
        self.log.error("create_update_payload(self, %s) not implemented", compatibility)

    def create_cmd_payload(self):
        """
        Must be implemented in sub class
        """
        self.log.error("create_cmd_payload(self) not implemented")

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
    def card_by_path(cls, path, panel):
        """
        return the correct card from a specific card path
        """
        nav_to = str(path).strip()
        if nav_to == '.':
            nav_to = './.'
        nav_to = nav_to.split("/")
        if len(nav_to) == 1:
            #navigate to card in same group
            card_name = nav_to[0].strip()
            if card_name in NSPanelCard.cards_by_group[panel.current_group]:
                cls.log.debug("Navigate to card '%s' in group '%s' with panel name.", card_name, panel.current_group)
                return NSPanelCard.cards_by_group[panel.current_group][card_name]
            cls.log.error("Can not navigate to card '%s'. Not defined in group '%s'.", card_name, panel.current_group)
        if len(nav_to) == 2:
            if nav_to[0].strip() != '.':
                group = nav_to[0].strip()
            else:
                group = panel.current_group.lower()
            card_name = nav_to[1].strip().lower()
            if group in NSPanelCard.cards_by_group:
                if card_name == '.':
                    if panel.name.lower() in NSPanelCard.cards_by_group[group]:
                        #check for a card with same name as panel in the group
                        cls.log.debug("Navigate to card '%s' in group '%s' with panel name.", panel.name, group)
                        return NSPanelCard.cards_by_group[group][panel.name.lower()]
                    #take first card in group:
                    return NSPanelCard.get_first_card(panel, group)
                if card_name in NSPanelCard.cards_by_group[group]:
                    cls.log.debug("Navigate to card '%s' in group '%s'.", card_name, group)
                    return NSPanelCard.cards_by_group[group][card_name]
                cls.log.error("Can not navigate to card '%s' in group '%s'. Card does not exist", card_name, group)
            else:
                cls.log.error("Unknown group '%s' in navTo '%s'.", group, path )
        else:
            cls.log.error("Illegal navigation format '%s'.", path )
        return None

    @classmethod
    def get_first_card( cls, panel, group_name):
        """
        returns the first card in this group
        """
        cls.log.debug("Get first card for group '%s'", group_name)
        group_name = group_name.lower()

        if group_name in cls.cards_by_group:
            i=0
            cards = list(cls.cards_by_group[group_name].values())
            while len(cards) > i and cards[i].type not in NSPanelCard.compatible_cards[panel.compatibility_mode][cls.NAV_CARDS]:
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

    def __init__(self, name, group=NSPanelCard.CARDS_HOME):
        """
        Constructor of a NSPanel card with slots
        """
        super().__init__( name, group )
        #create attributes
        self.nav_icon_left = skin.key( NSPanelCardWithNav.MY_TYPE, "icon_left")
        self.nav_icon_right = skin.key( NSPanelCardWithNav.MY_TYPE, "icon_right")
        self.nav_color_left = str(name_to_16bit_color(skin.key( NSPanelCardWithNav.MY_TYPE, "icon_color_left")))
        self.nav_color_right = str(name_to_16bit_color(skin.key( NSPanelCardWithNav.MY_TYPE, "icon_color_right")))
        self.nav_right = None
        self.nav_left = None

    def load_card_yaml(self, card_yaml):
        """
        Loads the panel definition from yaml dictionary
        """
        ret = super().load_card_yaml( card_yaml )

        if "navIconLeft" in card_yaml and card_yaml["navIconLeft"] is not None:
            self.nav_icon_left = skin.icon(str(card_yaml["navIconLeft"]))
        if "navIconRight" in card_yaml and card_yaml["navIconRight"] is not None:
            self.nav_icon_right = skin.icon(str(card_yaml["navIconRight"]))
        if "navIconColorLeft" in card_yaml and card_yaml["navIconColorLeft"] is not None:
            self.nav_color_left = str(name_to_16bit_color(card_yaml["navIconColorLeft"]))
        if "navIconColorRight" in card_yaml and card_yaml["navIconColorRight"] is not None:
            self.nav_color_right = str(name_to_16bit_color(card_yaml["navIconColorRight"]))
        if "navToLeft" in card_yaml and card_yaml["navToLeft"] is not None:
            self.nav_left = str(card_yaml["navToLeft"])
        if "navToRight" in card_yaml and card_yaml["navToRight"] is not None:
            self.nav_right = str(card_yaml["navToRight"])
        return ret

    def create_update_payload(self, compatibility=C_MODE_DEFAULT):
        """
        Create nav card payload
        """
        #check how many cards exist in this card
        if len(NSPanelCard.cards_by_group[self.group]) > 1:
            #OK generate left right navigation buttons
            payload = "entityUpd~"+self.title
            if self.nav_left == "":
                payload += "~~~~~~"
            else:
                payload += "~button~navigate.prev~"+self.nav_icon_left+"~"+self.nav_color_left+""
            if self.nav_right == "":
                return payload + "~~~~~~"
            return payload+"~~~button~navigate.next~"+self.nav_icon_right+"~"+self.nav_color_right+"~~"
        return "entityUpd~"+self.title+"~~~~~~~~~~~~"

    def create_cmd_payload(self):
        """
        create command payload to switch to this card type
        """
        return "pageType~"+self.MY_TYPE

    def event_button_press( self, params, panel):
        """
        process a button press event for this card
        """
        #example event params:
        #navigate.prev,button"

        #check for navigate card events
        if params[0] == "navigate.next" and params[1] == 'button':
            if self.nav_right is None:
                return self.next(panel)
            if self.nav_right != "":
                return NSPanelCard.card_by_path( self.nav_right, panel)

        if params[0] == "navigate.prev" and params[1] == 'button':
            if self.nav_left is None:
                return self.previous(panel)
            if self.nav_left != "":
                return NSPanelCard.card_by_path( self.nav_left, panel)

        self.log.warning("Event not processed for '%s'", str(params))
        return None
