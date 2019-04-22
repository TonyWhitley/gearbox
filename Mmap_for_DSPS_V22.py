# k3nny's Python mapping of The Iron Wolf's rF2 Shared Memory Tools
# https://github.com/TheIronWolfModding/rF2SharedMemoryMapPlugin
# https://forum.studio-397.com/index.php?members/k3nny.35143/
# Some of the original comments from ISI/S392's InternalsPlugin.hpp
# restored.

import mmap
import ctypes
import time

MAX_MAPPED_VEHICLES = 128
MAX_MAPPED_IDS = 512


class rF2Vec3(ctypes.Structure):
    _pack_ = 4
    _fields_ = [
        ('x', ctypes.c_double),
        ('y', ctypes.c_double),
        ('z', ctypes.c_double),
    ]

# sbyte = ctypes.c_byte
# byte = ctypes.c_ubyte

class rF2Wheel(ctypes.Structure):
    _pack_ = 4
    _fields_ = [
        ('mSuspensionDeflection', ctypes.c_double),               # metres
        ('mRideHeight', ctypes.c_double),                         # metres
        ('mSuspForce', ctypes.c_double),                          # pushrod load in Newtons
        ('mBrakeTemp', ctypes.c_double),                          # Celsius
        ('mBrakePressure', ctypes.c_double),                      # currently 0.0-1.0, depending on driver input and brake balance; will convert to true brake pressure (kPa) in future

        ('mRotation', ctypes.c_double),                           # radians/sec
        ('mLateralPatchVel', ctypes.c_double),                    # lateral velocity at contact patch
        ('mLongitudinalPatchVel', ctypes.c_double),               # longitudinal velocity at contact patch
        ('mLateralGroundVel', ctypes.c_double),                   # lateral velocity at contact patch
        ('mLongitudinalGroundVel', ctypes.c_double),              # longitudinal velocity at contact patch
        ('mCamber', ctypes.c_double),                             # radians (positive is left for left-side wheels, right for right-side wheels)
        ('mLateralForce', ctypes.c_double),                       # Newtons
        ('mLongitudinalForce', ctypes.c_double),                  # Newtons
        ('mTireLoad', ctypes.c_double),                           # Newtons

        ('mGripFract', ctypes.c_double),                          # an approximation of what fraction of the contact patch is sliding
        ('mPressure', ctypes.c_double),                           # kPa (tire pressure)
        ('mTemperature', ctypes.c_double*3),                      # Kelvin (subtract 273.15 to get Celsius), left/center/right (not to be confused with inside/center/outside!)
        ('mWear', ctypes.c_double),                               # wear (0.0-1.0, fraction of maximum) ... this is not necessarily proportional with grip loss
        ('mTerrainName', ctypes.c_ubyte*16),                      # the material prefixes from the TDF file
        ('mSurfaceType', ctypes.c_ubyte),                         # 0=dry, 1=wet, 2=grass, 3=dirt, 4=gravel, 5=rumblestrip, 6=special
        ('mFlat', ctypes.c_ubyte),                                # whether tire is flat
        ('mDetached', ctypes.c_ubyte),                            # whether wheel is detached

        ('mVerticalTireDeflection', ctypes.c_double),             # how much is tire deflected from its (speed-sensitive) radius
        ('mWheelYLocation', ctypes.c_double),                     # wheel's y location relative to vehicle y location
        ('mToe', ctypes.c_double),                                # current toe angle w.r.t. the vehicle

        ('mTireCarcassTemperature', ctypes.c_double),             # rough average of temperature samples from carcass (Kelvin)
        ('mTireInnerLayerTemperature', ctypes.c_double*3),        # rough average of temperature samples from innermost layer of rubber (before carcass) (Kelvin)
        ('mExpansion', ctypes.c_ubyte*24),
    ]


class rF2VehicleTelemetry(ctypes.Structure):
    _pack_ = 4
    _fields_ = [
        # Time
        ('mID', ctypes.c_int),                                    # slot ID (note that it can be re-used in multiplayer after someone leaves)
        ('mDeltaTime', ctypes.c_double),                          # time since last update (seconds)
        ('mElapsedTime', ctypes.c_double),                        # game session time
        ('mLapNumber', ctypes.c_int),                             # current lap number
        ('mLapStartET', ctypes.c_double),                         # time this lap was started
        ('mVehicleName', ctypes.c_ubyte*64), # byte               # current vehicle name
        ('mTrackName', ctypes.c_ubyte*64), # byte                 # current track name

        # Position and derivatives
        ('mPos', rF2Vec3),                                        # world position in metres
        ('mLocalVel', rF2Vec3),                                   # velocity (metres/sec) in local vehicle coordinates
        ('mLocalAccel', rF2Vec3),                                 # acceleration (metres/sec^2) in local vehicle coordinates

        # Orientation and derivatives
        ('mOri', rF2Vec3*3),                                      # rows of orientation matrix (use TelemQuat conversions if desired), also converts local
                                                                  # vehicle vectors into world X, Y, or Z using dot product of rows 0, 1, or 2 respectively
        ('mLocalRot', rF2Vec3),                                   # rotation (radians/sec) in local vehicle coordinates
        ('mLocalRotAccel', rF2Vec3),                              # rotational acceleration (radians/sec^2) in local vehicle coordinates

        # Vehicle status
        ('mGear', ctypes.c_int),                                  # -1=reverse, 0=neutral, 1+=forward gears
        ('mEngineRPM', ctypes.c_double),                          # engine RPM
        ('mEngineWaterTemp', ctypes.c_double),                    # Celsius
        ('mEngineOilTemp', ctypes.c_double),                      # Celsius
        ('mClutchRPM', ctypes.c_double),                          # clutch RPM

        # Driver input
        ('mUnfilteredThrottle', ctypes.c_double),                 # ranges  0.0-1.0
        ('mUnfilteredBrake', ctypes.c_double),                    # ranges  0.0-1.0
        ('mUnfilteredSteering', ctypes.c_double),                 # ranges -1.0-1.0 (left to right)
        ('mUnfilteredClutch', ctypes.c_double),                   # ranges  0.0-1.0

        # Filtered input (various adjustments for rev or speed limiting, TC, ABS?, speed sensitive steering, clutch work for semi-automatic shifting, etc.)
        ('mFilteredThrottle', ctypes.c_double),                   # ranges  0.0-1.0
        ('mFilteredBrake', ctypes.c_double),                      # ranges  0.0-1.0
        ('mFilteredSteering', ctypes.c_double),                   # ranges -1.0-1.0 (left to right)
        ('mFilteredClutch', ctypes.c_double),                     # ranges  0.0-1.0

        # Misc
        ('mSteeringShaftTorque', ctypes.c_double),                # torque around steering shaft (used to be mSteeringArmForce, but that is not necessarily accurate for feedback purposes)
        ('mFront3rdDeflection', ctypes.c_double),                 # deflection at front 3rd spring
        ('mRear3rdDeflection', ctypes.c_double),                  # deflection at rear 3rd spring

        # Aerodynamics
        ('mFrontWingHeight', ctypes.c_double),                    # front wing height
        ('mFrontRideHeight', ctypes.c_double),                    # front ride height
        ('mRearRideHeight', ctypes.c_double),                     # rear ride height
        ('mDrag', ctypes.c_double),                               # drag
        ('mFrontDownforce', ctypes.c_double),                     # front downforce
        ('mRearDownforce', ctypes.c_double),                      # rear downforce
        ('mFuel', ctypes.c_double),                               # amount of fuel (litres)

        # State/damage info
        ('mEngineMaxRPM', ctypes.c_double),                       # rev limit
        ('mScheduledStops', ctypes.c_ubyte), # byte               # number of scheduled pitstops
        ('mOverheating', ctypes.c_ubyte), # byte                  # whether overheating icon is shown
        ('mDetached', ctypes.c_ubyte), # byte                     # whether any parts (besides wheels) have been detached
        ('mHeadlights', ctypes.c_ubyte), # byte                   # whether headlights are on
        ('mDentSeverity', ctypes.c_ubyte*8), # byte               # dent severity at 8 locations around the car (0=none, 1=some, 2=more)
        ('mLastImpactET', ctypes.c_double),                       # time of last impact
        ('mLastImpactMagnitude', ctypes.c_double),                # magnitude of last impact
        ('mLastImpactPos', rF2Vec3),                              # location of last impact

        # Expanded
        ('mEngineTorque', ctypes.c_double),                       # current engine torque (including additive torque) (used to be mEngineTq, but there's little reason to abbreviate it)
        ('mCurrentSector', ctypes.c_int),                         # the current sector (zero-based) with the pitlane stored in the sign bit (example: entering pits from third sector gives 0x80000002)
        ('mSpeedLimiter', ctypes.c_ubyte), # byte                 # whether speed limiter is on
        ('mMaxGears', ctypes.c_ubyte), # byte                     # maximum forward gears
        ('mFrontTireCompoundIndex', ctypes.c_ubyte), # byte       # index within brand
        ('mRearTireCompoundIndex', ctypes.c_ubyte), # byte        # index within brand
        ('mFuelCapacity', ctypes.c_double),                       # capacity in litres
        ('mFrontFlapActivated', ctypes.c_ubyte), # byte           # whether front flap is activated
        ('mRearFlapActivated', ctypes.c_ubyte), # byte            # whether rear flap is activated
        ('mRearFlapLegalStatus', ctypes.c_ubyte), # byte          # 0=disallowed, 1=criteria detected but not allowed quite yet, 2=allowed
        ('mIgnitionStarter', ctypes.c_ubyte), # byte              # 0=off 1=ignition 2=ignition+starter

        ('mFrontTireCompoundName', ctypes.c_ubyte*18), # byte     # name of front tire compound
        ('mRearTireCompoundName', ctypes.c_ubyte*18), # byte      # name of rear tire compound

        ('mSpeedLimiterAvailable', ctypes.c_ubyte), # byte        # whether speed limiter is available
        ('mAntiStallActivated', ctypes.c_ubyte), # byte           # whether (hard) anti-stall is activated
        ('mUnused', ctypes.c_ubyte*2), # byte                     #
        ('mVisualSteeringWheelRange', ctypes.c_float),            # the *visual* steering wheel range

        ('mRearBrakeBias', ctypes.c_double),                      # fraction of brakes on rear
        ('mTurboBoostPressure', ctypes.c_double),                 # current turbo boost pressure if available
        ('mPhysicsToGraphicsOffset', ctypes.c_float*3),           # offset from static CG to graphical center
        ('mPhysicalSteeringWheelRange', ctypes.c_float),          # the *physical* steering wheel range

        # Future use
        ('mExpansion', ctypes.c_ubyte*152), # byte

        # keeping this at the end of the structure to make it easier to replace in future versions
        ('mWheels', rF2Wheel*4), # byte
    ]


class rF2Telemetry(ctypes.Structure):
    _pack_ = 4
    _fields_ = [
        ('mVersionUpdateBegin', ctypes.c_uint),
        ('mVersionUpdateEnd', ctypes.c_uint),
        ('mBytesUpdatedHint', ctypes.c_int),
        ('mNumVehicles', ctypes.c_int),
        ('mVehicles', rF2VehicleTelemetry*MAX_MAPPED_VEHICLES),
    ]


class rF2ScoringInfo(ctypes.Structure):
    _pack_ = 4
    _fields_ = [
        ('mTrackName', ctypes.c_ubyte*64), # byte
        ('mSession', ctypes.c_int),
        ('mCurrentET', ctypes.c_double),
        ('mEndET', ctypes.c_double),
        ('mMaxLaps', ctypes.c_int),
        ('mLapDist', ctypes.c_double),
        ('pointer1', ctypes.c_ubyte*8), # byte
        ('mNumVehicles', ctypes.c_int),
        ('mGamePhase', ctypes.c_ubyte), # byte
        ('mYellowFlagState', ctypes.c_byte), # sbyte
        ('mSectorFlag', ctypes.c_byte*3), # sbyte
        ('mStartLight', ctypes.c_ubyte), # byte
        ('mNumRedLights', ctypes.c_ubyte), # byte
        ('mInRealtime', ctypes.c_ubyte), # byte                  # in realtime as opposed to at the monitor
        ('mPlayerName', ctypes.c_ubyte*32), # byte
        ('mPlrFileName', ctypes.c_ubyte*64), # byte
        ('mDarkCloud', ctypes.c_double),
        ('mRaining', ctypes.c_double),
        ('mAmbientTemp', ctypes.c_double),
        ('mTrackTemp', ctypes.c_double),
        ('mWind', rF2Vec3),
        ('mMinPathWetness', ctypes.c_double),
        ('mMaxPathWetness', ctypes.c_double),
        ('mExpansion', ctypes.c_ubyte*256), # byte
        ('pointer2', ctypes.c_ubyte*8), # byte
    ]


class rF2VehicleScoring(ctypes.Structure):
    _pack_ = 4
    _fields_ = [
        ('mID', ctypes.c_int),                                    # slot ID (note that it can be re-used in multiplayer after someone leaves)
        ('mDriverName', ctypes.c_ubyte*32), # byte                # driver name
        ('mVehicleName', ctypes.c_ubyte*64), # byte               # vehicle name
        ('mTotalLaps', ctypes.c_short),                           # laps completed
        ('mSector', ctypes.c_byte), # sbyte                       # 0=sector3, 1=sector1, 2=sector2 (don't ask why)
        ('mFinishStatus', ctypes.c_byte), # sbyte                 # 0=none, 1=finished, 2=dnf, 3=dq
        ('mLapDist', ctypes.c_double),                            # current distance around track
        ('mPathLateral', ctypes.c_double),                        # lateral position with respect to *very approximate* "center" path
        ('mTrackEdge', ctypes.c_double),                          # track edge (w.r.t. "center" path) on same side of track as vehicle

        ('mBestSector1', ctypes.c_double),                        # best sector 1
        ('mBestSector2', ctypes.c_double),                        # best sector 2 (plus sector 1)
        ('mBestLapTime', ctypes.c_double),                        # best lap time
        ('mLastSector1', ctypes.c_double),                        # last sector 1
        ('mLastSector2', ctypes.c_double),                        # last sector 2 (plus sector 1)
        ('mLastLapTime', ctypes.c_double),                        # last lap time
        ('mCurSector1', ctypes.c_double),                         # current sector 1 if valid
        ('mCurSector2', ctypes.c_double),                         # current sector 2 (plus sector 1) if valid
        # no current laptime because it instantly becomes "last"

        ('mNumPitstops', ctypes.c_short),                         # number of pitstops made
        ('mNumPenalties', ctypes.c_short),                        # number of outstanding penalties
        ('mIsPlayer', ctypes.c_ubyte),  # byte                    # is this the player's vehicle

        ('mControl', ctypes.c_byte), # sbyte                      # who's in control: -1=nobody (shouldn't get this), 0=local player, 1=local AI, 2=remote, 3=replay (shouldn't get this)
        ('mInPits', ctypes.c_ubyte), # byte                       # between pit entrance and pit exit (not always accurate for remote vehicles)
        ('mPlace', ctypes.c_ubyte), # byte                        # 1-based position
        ('mVehicleClass', ctypes.c_ubyte*32), # byte              # vehicle class


        ('mTimeBehindNext', ctypes.c_double),                     # time behind vehicle in next higher place
        ('mLapsBehindNext', ctypes.c_int),                        # laps behind vehicle in next higher place
        ('mTimeBehindLeader', ctypes.c_double),                   # time behind leader
        ('mLapsBehindLeader', ctypes.c_int),                      # laps behind leader
        ('mLapStartET', ctypes.c_double),                         # time this lap was started


        ('mPos', rF2Vec3),                                        # world position in metres
        ('mLocalVel', rF2Vec3),                                   # velocity (metres/sec) in local vehicle coordinates
        ('mLocalAccel', rF2Vec3),                                 # acceleration (metres/sec^2) in local vehicle coordinates


        ('mOri', rF2Vec3*3),                                      # rows of orientation matrix (use TelemQuat conversions if desired), also converts local
                                                                  # vehicle vectors into world X, Y, or Z using dot product of rows 0, 1, or 2 respectively
        ('mLocalRot', rF2Vec3),                                   # rotation (radians/sec) in local vehicle coordinates
        ('mLocalRotAccel', rF2Vec3),                              # rotational acceleration (radians/sec^2) in local vehicle coordinates

        # tag.2012.03.01 - stopped casting some of these so variables now have names and mExpansion has shrunk, overall size and old data locations should be same
        ('mHeadlights', ctypes.c_ubyte), # byte                   # status of headlights
        ('mPitState', ctypes.c_ubyte), # byte                     # 0=none, 1=request, 2=entering, 3=stopped, 4=exiting
        ('mServerScored', ctypes.c_ubyte), # byte                 # whether this vehicle is being scored by server (could be off in qualifying or racing heats)
        ('mIndividualPhase', ctypes.c_ubyte), # byte              # game phases (described below) plus 9=after formation, 10=under yellow, 11=under blue (not used)

        ('mQualification', ctypes.c_int),                         # 1-based, can be -1 when invalid

        ('mTimeIntoLap', ctypes.c_double),                        # estimated time into lap
        ('mEstimatedLapTime', ctypes.c_double),                   # estimated laptime used for 'time behind' and 'time into lap' (note: this may changed based on vehicle and setup!?)
        ('mPitGroup', ctypes.c_ubyte*24),  # byte
                                                                  # pit group (same as team name unless pit is shared)
        ('mFlag', ctypes.c_ubyte),  # byte                        # primary flag being shown to vehicle (currently only 0=green or 6=blue)
        ('mUnderYellow', ctypes.c_ubyte),  # byte                 # whether this car has taken a full-course caution flag at the start/finish line
        ('mCountLapFlag', ctypes.c_ubyte),  # byte                # 0 = do not count lap or time, 1 = count lap but not time, 2 = count lap and time
        ('mInGarageStall', ctypes.c_ubyte),  # byte               # appears to be within the correct garage stall

        ('mUpgradePack', ctypes.c_ubyte*16),  # byte              # Coded upgrades
        ('mExpansion', ctypes.c_ubyte*60),  # byte
    ]


class rF2Scoring(ctypes.Structure):
    _pack_ = 4
    _fields_ = [
        ('mVersionUpdateBegin', ctypes.c_uint),
        ('mVersionUpdateEnd', ctypes.c_uint),
        ('mBytesUpdatedHint', ctypes.c_int),
        ('mScoringInfo', rF2ScoringInfo),
        ('mVehicles', rF2VehicleScoring*MAX_MAPPED_VEHICLES),
    ]

class rF2PhysicsOptions(ctypes.Structure):
    _pack_ = 4
    _fields_ = [
        ('mTractionControl', ctypes.c_ubyte),
        ('mAntiLockBrakes', ctypes.c_ubyte),
        ('mStabilityControl', ctypes.c_ubyte),
        ('mAutoShift', ctypes.c_ubyte),
        ('mAutoClutch', ctypes.c_ubyte),
        ('mInvulnerable', ctypes.c_ubyte),
        ('mOppositeLock', ctypes.c_ubyte),
        ('mSteeringHelp', ctypes.c_ubyte),
        ('mBrakingHelp', ctypes.c_ubyte),
        ('mSpinRecovery', ctypes.c_ubyte),
        ('mAutoPit', ctypes.c_ubyte),
        ('mAutoLift', ctypes.c_ubyte),
        ('mAutoBlip', ctypes.c_ubyte),
        ('mFuelMult', ctypes.c_ubyte),
        ('mTireMult', ctypes.c_ubyte),
        ('mMechFail', ctypes.c_ubyte),
        ('mAllowPitcrewPush', ctypes.c_ubyte),
        ('mRepeatShifts', ctypes.c_ubyte),
        ('mHoldClutch', ctypes.c_ubyte),
        ('mAutoReverse', ctypes.c_ubyte),
        ('mAlternateNeutral', ctypes.c_ubyte),
        ('mAIControl', ctypes.c_ubyte),
        ('mUnused1', ctypes.c_ubyte),
        ('mUnused2', ctypes.c_ubyte),
        ('mManualShiftOverrideTime', ctypes.c_float),
        ('mAutoShiftOverrideTime', ctypes.c_float),
        ('mSpeedSensitiveSteering', ctypes.c_float),
        ('mSteerRatioSpeed', ctypes.c_float),
    ]

class rF2TrackedDamage(ctypes.Structure):
    _pack_ = 4
    _fields_ = [
        ('mMaxImpactMagnitude', ctypes.c_double),
        ('mAccumulatedImpactMagnitude', ctypes.c_double),
    ]

class rF2VehScoringCapture(ctypes.Structure):
    _pack_ = 4
    _fields_ = [
        ('mID', ctypes.c_int),
        ('mPlace', ctypes.c_ubyte),
        ('mIsPlayer', ctypes.c_ubyte),
        ('mFinishStatus', ctypes.c_byte),
    ]

class rF2SessionTransitionCapture(ctypes.Structure):
    _pack_ = 4
    _fields_ = [
        ('mGamePhase', ctypes.c_ubyte),
        ('mSession', ctypes.c_int),
        ('mNumScoringVehicles', ctypes.c_int),
        ('mScoringVehicles', rF2VehScoringCapture*MAX_MAPPED_VEHICLES),
    ]

class rF2HostedPluginVars(ctypes.Structure):
    _pack_ = 4
    _fields_ = [
        ('StockCarRules_IsHosted', ctypes.c_ubyte),
        ('StockCarRules_DoubleFileType', ctypes.c_int),
    ]


class rF2Extended(ctypes.Structure):
    _pack_ = 4
    _fields_ = [
        ('mVersionUpdateBegin', ctypes.c_uint),
        ('mVersionUpdateEnd', ctypes.c_uint),
        ('mVersion', ctypes.c_ubyte*8),
        ('is64bit', ctypes.c_ubyte),
        ('mPhysics', rF2PhysicsOptions),
        ('mTrackedDamages', rF2TrackedDamage*MAX_MAPPED_IDS),
        ('mInRealtimeFC', ctypes.c_ubyte),
        ('mMultimediaThreadStarted', ctypes.c_ubyte),
        ('mSimulationThreadStarted', ctypes.c_ubyte),
        ('mSessionStarted', ctypes.c_ubyte),
        ('mTicksSessionStarted', ctypes.c_longlong),
        ('mTicksSessionEnded', ctypes.c_longlong),
        ('mSessionTransitionCapture',rF2SessionTransitionCapture ),
        ('mDisplayedMessageUpdateCapture', ctypes.c_ubyte*128),
        ('mHostedPluginVars', rF2HostedPluginVars),
    ]


class SimInfo:
    def __init__(self):


        self._rf2_tele = mmap.mmap(0, ctypes.sizeof(rF2Telemetry), "$rFactor2SMMP_Telemetry$")
        self.Rf2Tele = rF2Telemetry.from_buffer(self._rf2_tele)
        self._rf2_scor = mmap.mmap(0, ctypes.sizeof(rF2Scoring), "$rFactor2SMMP_Scoring$")
        self.Rf2Scor = rF2Scoring.from_buffer(self._rf2_scor)
        self._rf2_ext = mmap.mmap(0, ctypes.sizeof(rF2Extended), "$rFactor2SMMP_Extended$")
        self.Rf2Ext = rF2Extended.from_buffer(self._rf2_ext)

    def close(self):
      try:
        self._rf2_tele.close()
        self._rf2_scor.close()
        self._rf2_ext.close()
      except BufferError: # "cannot close exported pointers exist"
        pass

    def __del__(self):
        self.close()

if __name__ == '__main__':
    # Example usage
    info = SimInfo()
    clutch = info.Rf2Tele.mVehicles[0].mUnfilteredClutch # 1.0 clutch down, 0 clutch up
    info.Rf2Tele.mVehicles[0].mGear = 1
    gear   = info.Rf2Tele.mVehicles[0].mGear  # -1 to 6
    info.Rf2Tele.mVehicles[0].mGear = 2
    gear   = info.Rf2Tele.mVehicles[0].mGear  # -1 to 6
    #TBD driver = info.Rf2Scor.mVehicles[0].mDriverName
    driver = 'Max Snell'
    print('%s Gear: %d, Clutch position: %d' % (driver, gear, clutch))

