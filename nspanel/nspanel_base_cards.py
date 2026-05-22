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
Module implements a MQTT client as bridge to openhab for NsPanels with lovelance ui
This file contain the differnt base classe for cards shown in the panel.
"""

#general imports

# project specific imports:
from nspanel.nspanel_globals import map_state_pannel2oh
from nspanel.nspanel_card_slots import NsPanelCardSlotOhItem,  NSPanelCardSlot
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
    CARDS_HOME = "home"
    CARD_ENTITIES="cardEntities"
    CARD_THERMO="cardThermo"
    CARD_MEDIA="cardMedia"
    CARD_ALARM="cardAlarm"
    CARD_QR="cardQR"
    CARD_POWER="cardPower"
    CARD_SCREENSAVER="screensaver"
    CARD_GRID="cardGrid"
    CARD_CHARD="cardChart"

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
        #popup card handling
        self.popup = None #point to the popup card if a popup opened
        self.log.debug("Constructed!" )
        self.connected_panels = {}

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
        if self.cards_by_group[self.group][card_names[next_i]].MY_TYPE == NSPanelCard.CARD_SCREENSAVER:
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
        if self.cards_by_group[self.group][card_names[next_i]].MY_TYPE == NSPanelCard.CARD_SCREENSAVER:
            return self.previous(next_i)
        return self.cards_by_group[self.group][card_names[next_i]]

    def disconnect(self, nspanel):
        """
        disconnect from openhab
        """
        self.log.debug("Disconnect nspanel '%s' to card '%s'", nspanel.name, self.name )
        if nspanel.name in self.connected_panels:
            del self.connected_panels[nspanel.name]
        if nspanel.name in NSPanelCard.all_connected_panels:
            del NSPanelCard.all_connected_panels[nspanel.name]
        if len(NSPanelCard.all_connected_panels) == 0:
            #no panel connected anymore. Stop listner
            NsPanelCardSlotOhItem.OH.disconnect()

    def connect(self, nspanel):
        """
        connect to openhab
        """
        self.log.debug("Connect nspanel '%s' to card '%s'", nspanel.name, self.name )
        if len(NSPanelCard.all_connected_panels) == 0:
            #start listening on openhab items
            NsPanelCardSlotOhItem.OH.connect()
        self.connected_panels[nspanel.name] = nspanel
        NSPanelCard.all_connected_panels[nspanel.name] = nspanel

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
            #replace title with the title from the yaml other wise use the name as title
            self.title = str(card_yaml["title"])
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
            while len(cards) > i and cards[i].type == NSPanelCard.CARD_SCREENSAVER:
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

    def event_button_press( self, slot_name, params):
        """
        process a button press event for this card
        """
        #example event params:
        #"OnOff,1"
        #"button"
        #"brightnessSlider,34'
        #colorTempSlider,89
        #navigate.prev,button"
        #down
        #tiltOpen
        #event,buttonPress2,CardAlarm,AB0|mode2,6655

        #check for navigate card events
        if slot_name == "navigate.next" and params[0] == 'button':
            return self.next()
        if slot_name == "navigate.prev" and params[0] == 'button':
            return self.previous()
        self.log.warning("Event not processed for '%s'", slot_name)
        return None


class NSPanelCardWithSlots(NSPanelCardWithNav):
    """
    Base class for cards list of items
    """
    MY_TYPE = "NSPanelCardWithSlots"
    #OH_TYPE2SLOT = { "Switch": "switch", "Dimmer": "light", "Color": "light", "Number": "number", "Rollershutter": "shutter" }
    #OH_TYPE2ICON = { "Switch": "\uE520", "Dimmer": "\uE334", "Color": "\uE334", "Rollershutter": "\uF11B" }

    def __init__(self, name, group=NSPanelCard.CARDS_HOME ):
        """
        Constructor of a NSPanel card with slots
        """
        super().__init__( name, group )

        #slot dictionary
        self.slots = {}

    def load_slots_yaml( self, slots_yaml ):
        """
        Load slots for a card
        """
        self.log.debug("Load slots yaml: %s", str(slots_yaml))

        #test if slots are iterable
        try:
            _ = (e for e in slots_yaml)
        except TypeError:
            self.log.error("Slots in card '%s' are not a valid list.", self.name )
            return False

        for slot_yaml in slots_yaml:
            slot = NSPanelCardSlot.factory( slot_yaml, len(self.slots.keys()), self)
            if slot is not None:
                self.slots[slot.name] = slot

        if len(self.slots.keys()) <= 0:
            self.log.error("No valid slots defined for card %s", self.name )
            return False
        return True

    def load_card_yaml(self, card_yaml):
        """
        Loads the panel definition from yaml dictionary
        """
        super().load_card_yaml(card_yaml)

        if "slots" in card_yaml and card_yaml["slots"] is not None:
            return self.load_slots_yaml(card_yaml["slots"])

        self.log.error("No 'slots' attribute defined in card %s", self.name )
        return False

    def create_slots_payload(self):
        """
        create upstate payload for all slots
        """
        payload = ""
        for slot in self.slots.values():
            payload = payload + slot.create_payload()

        self.log.debug("Slot payload for all slots created: %s", payload)
        return payload

    def create_update_payload(self):
        """
        Create nav card payload
        """
        return super().create_update_payload() + self.create_slots_payload()

    def popup_card(self, card_type, slot_name):
        """
        setup a popup card for this card type
        """
        self.log.debug("Create card '%s' for '%s'",card_type, slot_name)
        if slot_name in self.slots:
            self.popup = NSPanelCard.factory(card_type, self.slots[slot_name])
        else:
            if slot_name == 'CardThermo':
                #thermo popup
                self.popup = NSPanelCard.factory(card_type, self)
            else:
                self.log.warning("Popup for unknown slot '%s' received.", slot_name)
                return

        if self.popup is None:
            self.log.error("Popup card type could not be created '%s',", card_type)

    def item_update_callback(self):
        """
        this callback is called from OHItensDB if the state of an item in this card is updated
        """
        self.log.debug("Call from item listner. Item state in card has changed")
        for panel in self.connected_panels.values():

            panel.update()

    def event_button_press( self, slot_name, params, panel=None ): #pylint: disable=too-many-return-statements, disable=too-many-branches
        """
        process a button press event for this card
        """
        #example event params:
        #"OnOff,1"
        #"button"
        #"brightnessSlider,34'
        #colorTempSlider,89
        #navigate.prev,button"
        #down
        #tiltOpen
        #event,buttonPress2,CardAlarm,AB0|mode2,6655

        #check for item events
        if slot_name in self.slots:
            slot = self.slots[slot_name]
            if self.popup is not None:
                if self.popup.event_button_press( slot_name, params ):
                    return self
                return None
            self.log.debug("Process for item '%s' the button press event: %s", slot_name, str(params))

            if params[0] == "button":
                #button for this item was pressed => toggel the value
                if slot.slot_class == "ohItem":
                    if slot.item.toggle_item_state(slot.options):
                        self.log.debug("Toggle event '%s' for slot '%s'", params[0], slot.name)
                        return self
                if slot.slot_class == "navigate":
                    self.log.debug("Toggle event '%s' for slot '%s'", params[0], slot.name)
                    card=panel.card_by_path(slot.nav_to)
                    if card is not None:
                        self.log.debug("Navigate to '%s' over slot '%s'", slot.nav_to, slot.name)
                    else:
                        self.log.warning("Could not navigate to '%s' over slot '%s'", slot.nav_to, slot.name)
                    return card
            if params[0] == 'OnOff' and len(params) >= 2:
                if slot.item.set_item_state(map_state_pannel2oh(params[0], params[1])):
                    self.log.debug("Switch event '%s' for slot '%s'", params[0], slot.name)
                    return self
            if params[0] == 'number-set' and len(params) >= 2:
                if slot.item.set_item_state( params[1]):
                    self.log.debug("Number set event '%s' for slot '%s'", params[0], slot.name)
                    return self
            self.log.warning("Event not processed for '%s'", slot_name)

        return super().event_button_press( slot_name, params )
