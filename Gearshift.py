# Gearshift.py - monitors the rFactor 2 shared memory values for the shifter
# and clutch and if a gear change is not done properly it repeatedly sends a
# "Neutral" key press to prevent the gear being selected.
#
# Inspired by http://www.richardjackett.com/grindingtranny
# I borrowed Grind_default.wav from there to make the noise of the grinding
# gears.
#
# The game has to have a key mapped as "Neutral". (Default: Numpad 0)
#

BUILD_REVISION = 61 # The git branch commit count
versionStr = 'gearshift V3.2.%d' % BUILD_REVISION
versionDate = '2020-02-20'

credits = "Reads the clutch and shifter from rF2 using\n" \
 "The Iron Wolf's rF2 Shared Memory Tools.\n" \
 "https://github.com/TheIronWolfModding/rF2SharedMemoryMapPlugin\n" \
 "Inspired by http://www.richardjackett.com/grindingtranny\n" \
 "I borrowed Grind_default.wav from there to make the noise of the grinding gears.\n\n"

from threading import Timer
from winsound import PlaySound, SND_FILENAME, SND_LOOP, SND_ASYNC
from tkinter import messagebox

try:
    from configIni import Config, configFileName
except: # It's a rFactory component
    from gearshift.configIni import Config, configFileName
import pyDirectInputKeySend.directInputKeySend as directInputKeySend
from readJSONfile import Json
from pyDirectInputKeySend.directInputKeySend import DirectInputKeyCodeTable, rfKeycodeToDIK
from mockMemoryMap import gui
from memoryMapInputs import Controls

# Main config variables, loaded from gearshift.ini
mockInput      =    False   # If True then use mock input

ClutchEngaged  =    90      # (0 - 100) the point in the travel where the clutch engages
doubleDeclutch =    False   # Not yet implemented
reshift =           True    # If True then neutral has to be selected before
                            # retrying failed change. If False then just have
                            # to de-clutch

###############################################################################

# Nothing much to twiddle with from here on

# Config variables, also loaded from gearshift.ini
global debug
debug           =   0       # 0, 1, 2 or 3
neutralButton   =   None  # The key used to force neutral, whatever the shifter says
graunchWav = None
controller_file = None

# Gear change events
clutchDisengage         = 'clutchDisengage'
clutchEngage            = 'clutchEngage'
gearSelect              = 'gearSelect'
gearDeselect            = 'gearDeselect'
graunchTimeout          = 'graunchTimeout'  # Memory-mapped mode
smStop                  = 'stop'  # Stop the state machine

#globals
gearState = 'neutral' # TBD

ClutchPrev = 2  # Active states are 0 and 1 so 2 is "unknown"
graunch_o = None

#################################################################################
# AHK replacement fns
def SetTimer(callback, mS):
  if mS > 0:
    timer = Timer(mS / 1000, callback)
    timer.start()
  else:
    pass # TBD delete timer?

def SoundPlay(soundfile):
  PlaySound(soundfile, SND_FILENAME|SND_LOOP|SND_ASYNC)

def SoundStop():
  PlaySound(None, SND_FILENAME)

def msgBox(str):
  print(str)

#################################################################################
def quit(errorCode):
  # User presses a key before exiting program
  print('\n\nPress Enter to exit')
  input()
  sys.exit(errorCode)

#################################################################################
class graunch:
  def __init__(self):
        self.graunching = False
  def graunchStart(self):
        # Start the graunch noise and sending "Neutral"
        # Start the noise
        global graunchWav
        SoundPlay(graunchWav)
        self.graunching = True
        self.graunch2()
        if debug >= 2:
            msgBox('GRAUNCH!')


  def graunchStop(self):
        if self.graunching:
          SoundStop()  # stop the noise
        self.graunching = False
        self.graunch1()


  def graunch1(self):
        # Send the "Neutral" key release
        directInputKeySend.ReleaseKey(neutralButton)
        if self.graunching:
          SetTimer(self.graunch2, 20)


  def graunch2(self):
      if self.graunching:
        # Send the "Neutral" key press
        directInputKeySend.PressKey(neutralButton)
        SetTimer(self.graunch3, 3000)
        SetTimer(self.graunch1, 20) # Ensure neutralButton is released
        if debug >= 1:
            directInputKeySend.PressReleaseKey('DIK_G')

  def graunch3(self):
      """ Shared memory.
      Neutral key causes gearDeselect event but if player doesn't move shifter
      to neutral then rF2 will quickly report that it's in gear again,
      causing a gearSelect event.
      If SM is still in neutral (gearSelect hasn't happened) when this timer
      expires then player has moved shifter to neutral
      """
      gearStateMachine(graunchTimeout)

  def isGraunching(self):
    return self.graunching


######################################################################

def gearStateMachine(event):
    global gearState
    global graunch_o
    global debug

    # Gear change states
    neutral                = 'neutral'
    clutchDown             = 'clutchDown'
    waitForDoubleDeclutchUp= 'waitForDoubleDeclutchUp'
    clutchDownGearSelected = 'clutchDownGearSelected'
    inGear                 = 'inGear'
    graunching             = 'graunching'
    graunchingClutchDown   = 'graunchingClutchDown'
    neutralKeySent         = 'neutralKeySent'

    if debug >= 3:
        msgBox('gearState %s event %s' % (gearState, event))
    # event check (debug)
    if   event == clutchDisengage:
      pass
    elif event == clutchEngage:
      pass
    elif event == gearSelect:
      pass
    elif event == gearDeselect:
      pass
    elif event == graunchTimeout:
      pass
    elif event == smStop:
      graunch_o.graunchStop()
      gearState = neutral
    else:
            msgBox('gearStateMachine() invalid event %s' % event)

    if    gearState == neutral:
        if event == clutchDisengage:
                gearState = clutchDown
                if debug >= 1:
                    directInputKeySend.PressKey('DIK_D')
        elif event == gearSelect:
                graunch_o.graunchStart()
                gearState = graunching
        elif event == graunchTimeout:
                graunch_o.graunchStop()

    elif gearState == clutchDown:
        if event == gearSelect:
                gearState = clutchDownGearSelected
        elif event == clutchEngage:
                gearState = neutral
                if debug >= 1:
                    directInputKeySend.PressKey('DIK_U')

    elif gearState == waitForDoubleDeclutchUp:
        if event == clutchEngage:
                gearState = neutral
                if debug >= 2:
                    msgBox('Double declutch spin up the box')
        elif event == gearSelect:
                graunch_o.graunchStart()
                gearState = graunching

    elif gearState == clutchDownGearSelected:
        if event == clutchEngage:
                gearState = inGear
                if debug >= 2:
                    msgBox('In gear')
        elif event == gearDeselect:
                if doubleDeclutch:
                    gearState = waitForDoubleDeclutchUp
                else:
                    gearState = clutchDown

    elif gearState == inGear:
        if event == gearDeselect:
                gearState = neutral
                if debug >= 2:
                    msgBox('Knocked out of gear')
        elif event == clutchDisengage:
                gearState = clutchDownGearSelected
        elif event == gearSelect: # smashed straight through without neutral.
                # I don't think this can happen if rF2, only with mock inputs...
                graunch_o.graunchStart()
                gearState = graunching

    elif gearState == graunching:
        if event == clutchDisengage:
                if reshift == False:
                        if debug >= 1:
                            directInputKeySend.PressKey('DIK_R')
                        gearState = clutchDownGearSelected
                else:
                        gearState = graunchingClutchDown
                graunch_o.graunchStop()
                if debug >= 1:
                    directInputKeySend.PressKey('DIK_G')
        elif event == clutchEngage:
                graunch_o.graunchStart()   # graunch again
        elif event == gearDeselect:
                gearState = neutralKeySent
        elif event == gearSelect:
                graunch_o.graunchStop()
                graunch_o.graunchStart()   # graunch again
                pass

    elif gearState == neutralKeySent:
        # rF2 will have put it into neutral but if shifter
        # still in gear it will have put it back in gear again
        if event == gearSelect:
                gearState = graunching
        elif event == graunchTimeout:
                # timed out and still not in gear, player has
                # shifted to neutral
                gearState = neutral
                graunch_o.graunchStop()

    elif gearState == graunchingClutchDown:
        if event == clutchEngage:
                graunch_o.graunchStart()   # graunch again
                gearState = graunching
        elif event == gearDeselect:
                gearState = clutchDown
                graunch_o.graunchStop()

    else:
           msgBox('Bad gearStateMachine() state gearState')

    if gearState != graunching and gearState != neutralKeySent:
        graunch_o.graunchStop()   # belt and braces - sometimes it gets stuck. REALLY????



def WatchClutch(Clutch):
    # Clutch 100 is up, 0 is down to the floor
    global ClutchPrev
    ClutchState = 1 # engaged

    if Clutch < ClutchEngaged:
        ClutchState = 0  # clutch is disengaged

    if ClutchState != ClutchPrev:
        if ClutchState == 0:
            gearStateMachine(clutchDisengage)
        else:
            gearStateMachine(clutchEngage)

    ClutchPrev = ClutchState

#############################################################

def memoryMapCallback(clutchEvent=None, gearEvent=None, stopEvent=False):
  if clutchEvent != None:
    WatchClutch(clutchEvent)
  if gearEvent != None:
    if gearEvent == 0: # Neutral
            gearStateMachine(gearDeselect)
    else:
            gearStateMachine(gearSelect)
  if stopEvent:
    gearStateMachine(smStop)

def ShowButtons():
  pass

global neutralButtonKeycode

def main():
  global graunch_o
  global debug
  global graunchWav
  global ClutchEngaged
  global controller_file
  global neutralButton

  config_o = Config()
  debug = config_o.get('miscellaneous', 'debug')
  if not debug: debug = 0
  graunchWav = config_o.get('miscellaneous', 'wav file')
  mockInput = config_o.get('miscellaneous', 'mock input')
  reshift = config_o.get('miscellaneous', 'reshift') == 1

  ClutchEngaged = config_o.get('clutch', 'bite point')

  neutralButton = config_o.get('miscellaneous', 'neutral button')
  ignitionButton = config_o.get('miscellaneous', 'ignition button')
  controller_file = config_o.get_controller_file()
  if neutralButton in DirectInputKeyCodeTable: # (it must be)
    neutralButtonKeycode = neutralButton[4:]
  else:
    print('\ngearshift.ini "neutral button" entry "%s" not recognised.\nIt must be one of:' % neutralButton)
    for _keyCode in DirectInputKeyCodeTable:
      print(_keyCode, end=', ')
    quit(99)
  if ignitionButton in DirectInputKeyCodeTable: # (it must be)
    _ignitionButton = ignitionButton[4:]
  else:
    print('\ngearshift.ini "ignition button" entry "%s" not recognised.\nIt must be one of:' % ignitionButton)
    for _keyCode in DirectInputKeyCodeTable:
      print(_keyCode, end=', ')
    quit(99)

  graunch_o = graunch()


  controls_o = Controls(debug=debug,mocking=mockInput)
  controls_o.run(memoryMapCallback)

  return controls_o, graunch_o, neutralButtonKeycode

#############################################################

def get_neutral_control(_controller_file_test=None):
    """
    Get the keycode specified in controller.json
    """
    global controller_file
    global neutralButton

    if _controller_file_test:
        _controller_file = _controller_file_test
    else:
        _controller_file = controller_file
    _JSON_O = Json(_controller_file)
    neutral_control = _JSON_O.get_item("Control - Neutral")
    if neutral_control:
        keycode = rfKeycodeToDIK(neutral_control[1])
        if not keycode == neutralButton:
            err = F'"Control - Neutral" in {_controller_file}\n'\
                F'does not match {configFileName} "neutral button" entry'.format()
            messagebox.showinfo('Config error', err)
        return

    err = F'"Control - Neutral" not in {_controller_file}\n'\
        F'See {configFileName} "controller_file" entry'.format()
    messagebox.showinfo('Config error', err)

if __name__ == "__main__":
  controls_o, graunch_o, neutralButtonKeycode = main()
  instructions = 'If gear selection fails this program will send %s ' \
    'to the active window until you reselect a gear.\n\n' \
    'You can minimise this window now.\n' \
    'Do not close it until you have finished racing.' % neutralButtonKeycode

  #############################################################
  # Using shared memory, reading clutch state and gear selected direct from rF2
  # mockInput: testing using the simple GUI to poke inputs into the memory map
  # otherwise just use the GUI slightly differently
  root = gui(mocking=mockInput,
              instructions=instructions,
              graunch_o=graunch_o,
              controls_o=controls_o
              )

  get_neutral_control()
  if root != 'OK':
    root.mainloop()
    controls_o.stop()
