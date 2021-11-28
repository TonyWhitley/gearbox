# Simple GUI to poke inputs into the memory map

import tkinter as tk
from tkinter import font, ttk, messagebox
from time import sleep

try:
    from pyRfactor2SharedMemory.sharedMemoryAPI import SimInfoAPI,\
        Cbytestring2Python
except BaseException:
    pass

#fontBold = font.Font(family='Helvetica', size=8, weight='bold', slant='italic')

GEARS = ['Reverse', 'Neutral','1','2','3','4','5','6','7','8']
CLUTCH_DELAY = 100.0 / 1000.0   # 100 mS
GEAR_DELAY = 200.0 / 1000.0     # 200 mS
GRAUNCH_DELAY = 100.0 / 1000.0
GRAUNCH_DELAY2 = 200.0 / 1000.0
TICKOVER = 1000

class Gui:
  """
  Superclass for GUI items common to Mock and Live.
  """
  def __init__(self, parentFrame, maxRevs, maxFwdGears=6):
    """ Put this into the parent frame """
    self.parentFrame = parentFrame
    self.info = SimInfoAPI()
    #clutch = self.info.playersVehicleTelemetry().mUnfilteredClutch') # 1.0 clutch down, 0 clutch up
    #gear  = self.info.playersVehicleTelemetry().mGear')  # -1 to 6

    self.settings = {}
    self.vars = {}
    self._tkCheckbuttons = {}
    _tkRadiobuttons = {}

    self.xPadding = 10

    ####################################################
    # Status frame
    tkFrame_Status = tk.LabelFrame(parentFrame, text='rFactor 2 status')
    tkFrame_Status.grid(column=2, row=1, sticky='nsew', padx=self.xPadding)

    self._createBoolVar('rF2 running', False)
    self._tkCheckbuttons['rF2 running'] = tk.Checkbutton(tkFrame_Status,
                                                  text='rF2 running and\nshared memory\nworking',
                                                  justify='l',
                                                  #indicatoron=0,
                                                  variable=self.vars['rF2 running'])
    self._tkCheckbuttons['rF2 running'].grid(sticky='w')

    self._createBoolVar('Track loaded', False)
    self._tkCheckbuttons['Track loaded'] = tk.Checkbutton(tkFrame_Status,
                                                  text='Track loaded',
                                                  variable=self.vars['Track loaded'])
    self._tkCheckbuttons['Track loaded'].grid(sticky='w')

    self._createBoolVar('On track', False)
    self._tkCheckbuttons['On track'] = tk.Checkbutton(tkFrame_Status,
                                                  text='On track',
                                                  variable=self.vars['On track'])
    self._tkCheckbuttons['On track'].grid(sticky='w')

    self._createBoolVar('Escape pressed', False)
    self._tkCheckbuttons['Escape pressed'] = tk.Checkbutton(tkFrame_Status,
                                                  text='Escape pressed',
                                                  variable=self.vars['Escape pressed'])
    self._tkCheckbuttons['Escape pressed'].grid(sticky='w')

    self._createBoolVar('AI driving', False)
    self._tkCheckbuttons['AI driving'] = tk.Checkbutton(tkFrame_Status,
                                                  text='AI driving',
                                                  variable=self.vars['AI driving'])
    self._tkCheckbuttons['AI driving'].grid(sticky='w')

    self._createVar('Player', False)
    self.driverLabel = tk.Label(tkFrame_Status,
                           text='')
    self.driverLabel.grid(sticky='w')

    ####################################################
    self._createBoolVar('Clutch pressed', False)
    self._createBoolVar('Auto clutch', True)

    ####################################################
    tkFrame_Gear = tk.LabelFrame(parentFrame, text='Gear', padx=self.xPadding)
    tkFrame_Gear.grid(column=1, row=3, sticky='nsew')

    self._createVar('Gear', 'Neutral')
    _gears = GEARS[:maxFwdGears+2]
    for gear in _gears:
      _tkRadiobuttons[gear] = tk.Radiobutton(tkFrame_Gear,
                                                  text=gear,
                                                  variable=self.vars['Gear'],
                                                  value=gear,
                                                  command=self._gearChange)
      _tkRadiobuttons[gear].grid(sticky='w')
      _tkRadiobuttons[gear].update()

    ####################################################
    tkFrame_Revs = tk.LabelFrame(parentFrame, text='Revs')
    tkFrame_Revs.grid(column=2, row=1, rowspan=3, sticky='sew', padx=self.xPadding)

    _EngineRPMCol = 1
    self._createVar('EngineRPM', TICKOVER)

    tkLabel_EngineRPM = tk.Label(tkFrame_Revs,
                                          text='Engine revs',
                                          #font=fontBold,
                                          justify=tk.LEFT)
    tkLabel_EngineRPM.grid(column=_EngineRPMCol, row=1, sticky='nw')

    tkScale_EngineRPM = tk.Scale(tkFrame_Revs,
                                  from_=TICKOVER,
                                  to=maxRevs,
                                  orient=tk.VERTICAL,
                                  variable=self.vars['EngineRPM'],
                                  command=self.EngineRPM)
    tkScale_EngineRPM.grid(column=_EngineRPMCol, row=2, rowspan=3, sticky='ew')

    tkLabel_EngineRPM_0 = tk.Label(tkFrame_Revs, text='Tickover')
    tkLabel_EngineRPM_0.grid(column=_EngineRPMCol, row=2, sticky='nw')
    tkLabel_EngineRPM_10 = tk.Label(tkFrame_Revs, text='Rev limit')
    tkLabel_EngineRPM_10.grid(column=_EngineRPMCol, row=4, sticky='nw')

    _ClutchRPMCol = 2
    self._createVar('ClutchRPM', 0)

    tkLabel_ClutchRPM = tk.Label(tkFrame_Revs,
                                          text='Gearbox Revs',
                                          #font=fontBold,
                                          justify=tk.LEFT)
    tkLabel_ClutchRPM.grid(column=_ClutchRPMCol, row=1, sticky='n')
    tkScale_ClutchRPM = tk.Scale(tkFrame_Revs,
                                  from_=0,
                                  to=maxRevs*2,
                                  orient=tk.VERTICAL,
                                  variable=self.vars['ClutchRPM'],
                                  command=self.ClutchRPM)
    tkScale_ClutchRPM.grid(column=_ClutchRPMCol, row=3, sticky='ewns')

    tkLabel_ClutchRPM_10 = tk.Label(tkFrame_Revs, text='Stationary')
    tkLabel_ClutchRPM_10.grid(column=_ClutchRPMCol, row=2, sticky='nw')
    tkLabel_ClutchRPM_0 = tk.Label(tkFrame_Revs, text='Downshift\nover rev')
    tkLabel_ClutchRPM_0.grid(column=_ClutchRPMCol, row=4, sticky='nw')

  def _createVar(self, name, value):
    self.vars[name] = tk.StringVar(name=name)
    self.vars[name].set(value)

  def _createBoolVar(self, name, value):
    self.vars[name] = tk.BooleanVar(name=name)
    self.vars[name].set(value)

  def EngineRPM(self, event):
    self.info.playersVehicleTelemetry().mEngineRPM = int(self.vars['EngineRPM'].get())

  def ClutchRPM(self, event):
    self.info.playersVehicleTelemetry().mClutchRPM = int(self.vars['ClutchRPM'].get())

  #######################################

  def on_closing(self):
    self.info.close()
    self.parentFrame.destroy()

####################################################
class mock(Gui):
  # Subclass for GUI items for Mock.
  def __init__(self, parentFrame, graunch_o, maxRevs=10000, maxFwdGears=6):
    Gui.__init__(self, parentFrame, maxRevs, maxFwdGears)
    self.graunch_o = graunch_o
    tkLabel_Options = tk.Label(parentFrame,
                                text='Simple GUI to fake clutch, gear selection and revs\n'
                                '"Auto clutch" presses and releases the clutch')
    tkLabel_Options.grid(column=1, row=0, columnspan=3)

    tkFrame_Clutch = tk.LabelFrame(parentFrame, text='Clutch')
    tkFrame_Clutch.grid(column=1, row=1, sticky='nsew', padx=self.xPadding)

    self._tkCheckbuttons['Clutch pressed'] = tk.Checkbutton(tkFrame_Clutch,
                                                  text='Pressed',
                                                  variable=self.vars['Clutch pressed'],
                                                  command=self.__clutchOperation)

    self._tkCheckbuttons['Clutch pressed'].grid(sticky='w')

    self._tkCheckbuttons['Auto clutch'] = tk.Checkbutton(tkFrame_Clutch,
                                                  text='Automatic',
                                                  variable=self.vars['Auto clutch'])

    self._tkCheckbuttons['Auto clutch'].grid(sticky='w')

  ####################################### Commands
  def __operateClutch(self, pressed):
    if pressed:
      self.info.playersVehicleTelemetry().mUnfilteredClutch = 1.0 # 1.0 clutch down, 0 clutch up
      sleep(CLUTCH_DELAY)
      print('[Mock: Clutch pressed]')
    else:
      self.info.playersVehicleTelemetry().mUnfilteredClutch = 0.0 # 1.0 clutch down, 0 clutch up
      sleep(CLUTCH_DELAY)
      print('[Mock: Clutch released]')
  def __clutchOperation(self):
    self.__operateClutch(self.vars['Clutch pressed'].get())

  def _gearChange(self):
    # Gear has been changed
    _gear = GEARS.index(self.vars['Gear'].get())-1
    # -1=reverse, 0=neutral, 1+=forward gears

    if _gear != 0:
      if self.vars['Auto clutch'].get():
        self.__operateClutch(True)
      print('[Mock: gear %s]' % self.vars['Gear'].get())
      self.info.playersVehicleTelemetry().mGear = _gear
      sleep(GEAR_DELAY)
      if self.vars['Auto clutch'].get():
        self.__operateClutch(False)

      # if we're graunching it rF2 will set gear to Neutral
      # momentarily before putting it back in gear if it hasn't
      # been shifted to neutral
      if self.graunch_o.isGraunching():
        sleep(GRAUNCH_DELAY)
        self.info.playersVehicleTelemetry().mGear = 0
        sleep(GRAUNCH_DELAY2)
        self.info.playersVehicleTelemetry().mGear = _gear
    else: # Neutral
      self.info.playersVehicleTelemetry().mGear = _gear

####################################################
class live(Gui):
  # Subclass for GUI items for Live.
  def __init__(self, parentFrame, graunch_o, controls_o, maxRevs=10000, maxFwdGears=6, instructions=''):
    Gui.__init__(self, parentFrame, maxRevs, maxFwdGears)
    self._timestamp = 0
    self.graunch_o = graunch_o
    self.controls_o = controls_o

    self._createBoolVar('SMactive', False)
    self._createBoolVar('Graunching', False)
    self._createVar('Clutch', 0)

    tkFrame_Instructions = tk.LabelFrame(parentFrame)
    tkFrame_Instructions.grid(column=1, row=1, sticky='nsew', padx=self.xPadding)
    tkLabel_instructions = tk.Label(tkFrame_Instructions,
                                    justify='l',
                                    wraplength=200,
                                    text=instructions)
    tkLabel_instructions.grid(column=1, row=0, sticky='ew', padx=self.xPadding, columnspan=2)

    tkLabel_Clutch = tk.Label(tkFrame_Instructions,
                                          text='Clutch engaged',
                                          #font=fontBold,
                                          justify=tk.LEFT)
    tkLabel_Clutch.grid(column=1, row=1, sticky='e')
    tkScale_Clutch = tk.Scale(tkFrame_Instructions,
                              from_=0,
                              to=100,
                              orient=tk.HORIZONTAL,
                              showvalue=0,
                              variable=self.vars['Clutch'])
    tkScale_Clutch.grid(column=2, row=1, sticky='wns')

    self._tkCheckbuttons['SMactive'] = tk.Checkbutton(tkFrame_Instructions,
                                                      text='SM active',
                                                      variable=self.vars['SMactive'])
    self._tkCheckbuttons['SMactive'].grid(column=1, row=2, sticky='sw', padx=self.xPadding)

    self._tkCheckbuttons['Graunching'] = tk.Checkbutton(tkFrame_Instructions,
                                                        text='Graunching',
                                                        variable=self.vars['Graunching'])
    self._tkCheckbuttons['Graunching'].grid(column=2, row=2, sticky='sw', padx=self.xPadding)

    ##########################################################
    """
    Displaying it needs work
    _match_label = ttk.Label(tkFrame_Instructions,
                                text='Controller.json keycode\nmust match, it is:')
    _match_label.grid(row=3, columnspan=2, sticky='e')
    #Tooltip(_match_label, text='Note: only written when rFactor exits')

    _key_label = tk.Label(tkFrame_Instructions,
                            text=self.get_neutral_control(controller_file),
                            fg='SystemInactiveCaptionText',
                            relief=tk.GROOVE,
                            borderwidth=4,
                            anchor='e',
                            padx=4)
    _key_label.grid(row=3, column=2)

    Tooltip(_key_label, text='Note: only written when rFactor exits')

    Tooltip(rfactor_headlight_control['rFactor Toggle']['ControllerName'],
    text='Must be a keyboard key')
    Tooltip(rfactor_headlight_control['rFactor Toggle']['tkButton'],
    text='Must be a keyboard key')
    """

    # Kick off the tick
    self.__tick()


  #######################################

  def __tick(self):
    # timed callback to update live status
    mEngineRPM = int(self.info.playersVehicleTelemetry().mEngineRPM)
    mClutchRPM = int(self.info.playersVehicleTelemetry().mClutchRPM)
    mClutch = int(self.info.playersVehicleTelemetry().mUnfilteredClutch*100)
    self.vars['EngineRPM'].set(mEngineRPM)
    self.vars['ClutchRPM'].set(mClutchRPM)
    self.vars['Clutch'].set(mClutch)
    self.vars['Gear'].set(GEARS[self.info.playersVehicleTelemetry().mGear+1])
    self.vars['rF2 running'].set(self.info.isRF2running())
    self.vars['Track loaded'].set(self.info.isTrackLoaded())
    self.vars['On track'].set(self.info.isOnTrack())
    self.driverLabel.config(text=self.info.driverName())
    #self.vars['Escape pressed'].set(not self._timestamp < self.info.playersVehicleScoring().mTimeIntoLap)
    if not self.info.isOnTrack() or \
      self._timestamp < self.info.playersVehicleTelemetry().mElapsedTime:
      self.vars['Escape pressed'].set(False)
    else:
      self.vars['Escape pressed'].set(True)
    self._timestamp = self.info.playersVehicleTelemetry().mElapsedTime

    self.vars['AI driving'].set(self.info.isOnTrack() and \
      self.info.isAiDriving())
    self.vars['Graunching'].set(self.graunch_o.isGraunching())
    self.vars['SMactive'].set(self.controls_o.SMactive())
    self.parentFrame.after(200, self.__tick)

  def _gearChange(self):
    # Null command
    pass
####################################### Commands

class Menu:
  def __init__(self,
               menubar,
               menu2tab=None):
    helpmenu = tk.Menu(menubar, tearoff=0)
    helpmenu.add_command(label="Credits", command=credits)
    helpmenu.add_command(label="About", command=about)
    menubar.add_cascade(label="Help", menu=helpmenu)
def about():
  from Gearshift import versionStr, versionDate
  messagebox.askokcancel(
            'About gearshift',
            '%s  %s\nby Tony Whitley\n\n' \
            'https://github.com/TonyWhitley/gearshift' \
            % (versionStr, versionDate)
        )
def credits():
  from Gearshift import credits
  messagebox.askokcancel(
            'FAQ',
            credits
        )

def gui(maxRevs=10000, maxFwdGears=6, mocking=False, instructions='', graunch_o=None, controls_o=None):
  root = tk.Tk()
  root.title('gearshift')
  menubar = tk.Menu(root)
  _m = Menu(menubar)
  root.config(menu=menubar)

  mockMemoryMap = ttk.Frame(root, width=1200, height=1200, relief='sunken', borderwidth=5)
  mockMemoryMap.grid()

  if mocking:
    o_gui = mock(mockMemoryMap,graunch_o,maxRevs,maxFwdGears)
  else:
    o_gui = live(mockMemoryMap,
                 graunch_o,                 # to read Graunch status
                 controls_o,                # to read whether state machine is active
                 maxRevs,
                 maxFwdGears,
                 instructions=instructions  # Text
                 )

  # Trying for a clean shutdown
  # root.protocol("WM_DELETE_WINDOW", o_gui.on_closing)
  return root
  pass

def test_main():
  class graunch:  #dummy
    def isGraunching(self):
      return False
    def SMactive(self):
      return True

  graunch_o = graunch()

  root = gui(mocking=True,
             instructions='Ipso lorem\nBlah blah blah blah blah blah blah blah blah blah',
             graunch_o=graunch_o)
  return root

if __name__ == '__main__':
  # To run this frame by itself for development
  root = test_main()
  root.mainloop() # having that separate allows for unit testing test_main()