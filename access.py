import time
import ctypes
import string
import nfc
import dataset
import os
import pygame
import time
import random
import datetime
import pprint

db = dataset.connect('sqlite:///test.db')

members = db['members']

# todo
# monitor door status
# open door
# logging
# clean up display code to remove duplication
# clean up member checking and logging to be functions

class pylcd :
    screen = None;

    def __init__(self):
        "Ininitializes a new pygame screen using the framebuffer"
        # Based on "Python GUI in Linux frame buffer"
        # http://www.karoltomala.com/blog/?p=679
        disp_no = os.getenv("DISPLAY")
        if disp_no:
            print "I'm running under X display = {0}".format(disp_no)

        # Check which frame buffer drivers are available
        # Start with fbcon since directfb hangs with composite output
        drivers = ['fbcon', 'directfb', 'svgalib']
        found = False
        for driver in drivers:
            # Make sure that SDL_VIDEODRIVER is set
            if not os.getenv('SDL_VIDEODRIVER'):
                os.putenv('SDL_VIDEODRIVER', driver)
            try:
                pygame.display.init()
            except pygame.error:
                print 'Driver: {0} failed.'.format(driver)
                continue
            found = True
            break

        if not found:
            raise Exception('No suitable video driver found!')

        size = (pygame.display.Info().current_w, pygame.display.Info().current_h)
        print "Framebuffer size: %d x %d" % (size[0], size[1])
        self.screen = pygame.display.set_mode(size, pygame.FULLSCREEN)
        # Clear the screen to start
        self.screen.fill((0, 0, 0))
        # Initialise font support
        pygame.font.init()
        # Render the screen
        pygame.display.update()

    def __del__(self):
        "Destructor to make sure pygame shuts down, etc."

    def idle(self):
        # Fill the screen with red (255, 0, 0)
        background = (0, 0, 255)
        self.screen.fill(background)
	myfont = pygame.font.SysFont("Comic Sans MS", 64)
	label = myfont.render("Place card on reader", 1, (255,255,255))
	tw = label.get_width()
	th = label.get_height()

	w = pygame.display.Info().current_w
	h = pygame.display.Info().current_h
	self.screen.blit(label, ((w/2)-(tw/2),(h/2)-(th/2)))
        # Update the display
        pygame.display.update()

    def accessdenied(self, uid):
        # Fill the screen with red (255, 0, 0)
        background = (255, 0, 0)
        self.screen.fill(background)
	myfont = pygame.font.SysFont("Comic Sans MS", 64)
	label = myfont.render("Access Denied", 1, (255,255,255))
	label2 = myfont.render(uid, 1, (255,255,255))
	tw = label.get_width()
	tw2 = label2.get_width()
	th = label.get_height()

	w = pygame.display.Info().current_w
	h = pygame.display.Info().current_h
	self.screen.blit(label, ((w/2)-(tw/2),(h/2)-th))
	self.screen.blit(label2, ((w/2)-(tw2/2),(h/2)+th))
        # Update the display
        pygame.display.update()
    def accessgranted(self, name):
        # Fill the screen with red (255, 0, 0)
        background = (0, 255, 0)
        self.screen.fill(background)
	myfont = pygame.font.SysFont("Comic Sans MS", 64)
	label = myfont.render("Welcome", 1, (255,255,255))
	label2 = myfont.render(name, 1, (255,255,255))
	tw = label.get_width()
	tw2 = label2.get_width()
	th = label.get_height()

	w = pygame.display.Info().current_w
	h = pygame.display.Info().current_h
	self.screen.blit(label, ((w/2)-(tw/2),(h/2)-th))
	self.screen.blit(label2, ((w/2)-(tw2/2),(h/2)+th))
        # Update the display
        pygame.display.update()
    def accesswarning(self, days):
        # Fill the screen with red (255, 0, 0)
        background = (255, 255, 0)
        self.screen.fill(background)
	myfont = pygame.font.SysFont("Comic Sans MS", 64)
	label = myfont.render("Renew membership", 1, (0,0,0))
	label2 = myfont.render(str(days) + " days remaining", 1, (0,0,0))
	tw = label.get_width()
	tw2 = label2.get_width()
	th = label.get_height()

	w = pygame.display.Info().current_w
	h = pygame.display.Info().current_h
	self.screen.blit(label, ((w/2)-(tw/2),(h/2)-th))
	self.screen.blit(label2, ((w/2)-(tw2/2),(h/2)+th))
        # Update the display
        pygame.display.update()
    def doorwarning(self):
        # Fill the screen with red (255, 0, 0)
        background = (255, 255, 0)
        self.screen.fill(background)
	myfont = pygame.font.SysFont("Comic Sans MS", 64)
	label = myfont.render("Please close the door", 1, (0,0,0))
	tw = label.get_width()
	th = label.get_height()

	w = pygame.display.Info().current_w
	h = pygame.display.Info().current_h
	self.screen.blit(label, ((w/2)-(tw/2),(h/2)-(th/2)))
        # Update the display
        pygame.display.update()

class NFCReader(object):
    MC_AUTH_A = 0x60
    MC_AUTH_B = 0x61
    MC_READ = 0x30
    MC_WRITE = 0xA0
    card_timeout = 2
    devices_found = 0

    def __init__(self,lcd):
        self.__context = None
        self.__device = None
        self.lcd = lcd
        self._card_present = False
        self._card_last_seen = None
        self._card_uid = None
        self._clean_card()
        lcd.idle()
        mods = [(nfc.NMT_ISO14443A, nfc.NBR_106)]

        self.__modulations = (nfc.nfc_modulation * len(mods))()
        for i in range(len(mods)):
            self.__modulations[i].nmt = mods[i][0]
            self.__modulations[i].nbr = mods[i][1]


    def _poll_loop(self):
        """Starts a loop that constantly polls for cards"""
        nt = nfc.nfc_target()
        res = nfc.nfc_initiator_poll_target(self.__device, self.__modulations, len(self.__modulations), 1, 2,
                                            ctypes.byref(nt))
        # print "RES", res
        if res < 0:
            raise IOError("NFC Error whilst polling")
        elif res >= 1:
            uid = None
            uid = "".join([chr(nt.nti.nai.abtUid[i]) for i in range(nt.nti.nai.szUidLen)])
            if uid:
                tagid =  uid.encode("hex")
                global members
                member = members.find_one(tagid=tagid)
                if member:
                    pp = pprint.PrettyPrinter(indent=4)
                    print pp.pprint(member["expires"])
                    if member["expires"]:
                        if member["expires"] > datetime.datetime.now():
                            self.lcd.accessgranted(member['firstname'])
                        elif member["expires"] > datetime.datetime.now() - datetime.timedelta(days=5):
                            self.lcd.accesswarning((member["expires"] - datetime.datetime.now() + datetime.timedelta(days=5)).days)
                        else:
                            self.lcd.accessdenied(tagid)
                    else:
                        self.lcd.accessdenied(tagid)
                    time.sleep(2)
                    self.lcd.idle()
                else:
                    self.lcd.accessdenied(tagid)
                    time.sleep(2)
                    self.lcd.idle()

                #if not ((self._card_uid and self._card_present and uid == self._card_uid) and \
                    #                time.mktime(time.gmtime()) <= self._card_last_seen + self.card_timeout):
                    #self._setup_device()
                #    self.read_card(uid)
            self._card_uid = uid
            self._card_present = True
            self._card_last_seen = time.mktime(time.gmtime())
        else:
            self._card_present = False
            self._clean_card()

    def _clean_card(self):
        self._card_uid = None

    def run(self):
        """Starts the looping thread"""
        self.__context = ctypes.pointer(nfc.nfc_context())
        nfc.nfc_init(ctypes.byref(self.__context))
        loop = True
        try:
            self._clean_card()
            conn_strings = (nfc.nfc_connstring * 10)()
    #        print self.devices_found
            if not self.devices_found:
                self.devices_found = nfc.nfc_list_devices(self.__context, conn_strings, 10)
    #            print self.devices_found
            if self.devices_found >= 1:
        #    if True:
                self.__device = nfc.nfc_open(self.__context, conn_strings[0])
                try:
                    _ = nfc.nfc_initiator_init(self.__device)
                    while True:
                        self._poll_loop()
                finally:
                    nfc.nfc_close(self.__device)
            else:
                self.log("NFC Waiting for device.")
                time.sleep(5)
        except (KeyboardInterrupt, SystemExit):
            loop = False
        except IOError, e:
            self.log("Exception: " + str(e))
            loop = True  # not str(e).startswith("NFC Error whilst polling")
        # except Exception, e:
        # loop = True
        #    print "[!]", str(e)
        finally:
            nfc.nfc_exit(self.__context)
            self.log("NFC Clean shutdown called")
        return loop
    def log(self, message):
        pass
        #print message

if __name__ == '__main__':
    lcd = pylcd()
    while NFCReader(lcd).run():
        pass
