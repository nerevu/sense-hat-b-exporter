#!/usr/bin/python
# -*- coding:utf-8 -*-
import time

try:
    import smbus
except ImportError:
    smbus = None

SGM_I2C_ADDRESS = 0x48

# Pointer Register
SGM_POINTER_CONVERT = 0x00
SGM_POINTER_CONFIG = 0x01
SGM_POINTER_LOWTHRESH = 0x02
SGM_POINTER_HIGHTHRESH = 0x03

# Config Register
SGM_CONFIG_OS_BUSY = 0x0000  # Device is currently performing a conversion
SGM_CONFIG_OS_NOBUSY = 0x8000  # Device is not currently performing a conversion
SGM_CONFIG_OS_SINGLE_CONVERT = (
    0x8000  # Start a single conversion (when in power-down state)
)
SGM_CONFIG_OS_NO_EFFECT = 0x0000  # No effect
SGM_CONFIG_MUX_MUL_0_1 = (
    0x0000  # Input multiplexer,AINP = AIN0 and AINN = AIN1(default)
)
SGM_CONFIG_MUX_MUL_0_3 = 0x1000  # Input multiplexer,AINP = AIN0 and AINN = AIN3
SGM_CONFIG_MUX_MUL_1_3 = 0x2000  # Input multiplexer,AINP = AIN1 and AINN = AIN3
SGM_CONFIG_MUX_MUL_2_3 = 0x3000  # Input multiplexer,AINP = AIN2 and AINN = AIN3
SGM_CONFIG_MUX_SINGLE_0 = 0x4000  # SINGLE,AIN0
SGM_CONFIG_MUX_SINGLE_1 = 0x5000  # SINGLE,AIN1
SGM_CONFIG_MUX_SINGLE_2 = 0x6000  # SINGLE,AIN2
SGM_CONFIG_MUX_SINGLE_3 = 0x7000  # SINGLE,AIN3
SGM_CONFIG_PGA_6144 = 0x0000  # Gain= +/- 6.144V
SGM_CONFIG_PGA_4096 = 0x0200  # Gain= +/- 4.096V
SGM_CONFIG_PGA_2048 = 0x0400  # Gain= +/- 2.048V(default)
SGM_CONFIG_PGA_1024 = 0x0600  # Gain= +/- 1.024V
SGM_CONFIG_PGA_512 = 0x0800  # Gain= +/- 0.512V
SGM_CONFIG_PGA_256 = 0x0A00  # Gain= +/- 0.256V
SGM_CONFIG_MODE_CONTINUOUS = 0x0000  # Device operating mode:Continuous-conversion mode
SGM_CONFIG_MODE_NOCONTINUOUS = (
    0x0100  # Device operating mode：Single-shot mode or power-down state (default)
)
SGM_CONFIG_DR_RATE_7_5 = 0x0000  # Data rate=7.5Hz
SGM_CONFIG_DR_RATE_15 = 0x0020  # Data rate=15Hz
SGM_CONFIG_DR_RATE_30 = 0x0040  # Data rate=30Hz
SGM_CONFIG_DR_RATE_60 = 0x0060  # Data rate=60Hz
SGM_CONFIG_DR_RATE_120 = 0x0080  # Data rate=120Hz
SGM_CONFIG_DR_RATE_240 = 0x00A0  # Data rate=240Hz
SGM_CONFIG_DR_RATE_480 = 0x00C0  # Data rate=480Hz
SGM_CONFIG_DR_RATE_960 = 0x00E0  # Data rate=960Hz
SGM_CONFIG_COMP_MODE_WINDOW = 0x0010  # Comparator mode：Window comparator
SGM_CONFIG_COMP_MODE_TRADITIONAL = (
    0x0000  # Comparator mode：Traditional comparator (default)
)
SGM_CONFIG_COMP_POL_LOW = 0x0000  # Comparator polarity：Active low (default)
SGM_CONFIG_COMP_POL_HIGH = 0x0008  # Comparator polarity：Active high
SGM_CONFIG_COMP_LAT = 0x0004  # Latching comparator
SGM_CONFIG_COMP_NONLAT = 0x0000  # Nonlatching comparator (default)
SGM_CONFIG_COMP_QUE_ONE = 0x0000  # Assert after one conversion
SGM_CONFIG_COMP_QUE_TWO = 0x0001  # Assert after two conversions
SGM_CONFIG_COMP_QUE_FOUR = 0x0002  # Assert after four conversions
SGM_CONFIG_COMP_QUE_NON = (
    0x0003  # Disable comparator and set ALERT/RDY pin to high-impedance (default)
)

Config_Set = 0


class SGM58031(object):
    def __init__(self, address=SGM_I2C_ADDRESS):
        if smbus is None:
            return

        self._address = address
        self._bus = smbus.SMBus(1)

    def SGM58031_SINGLE_READ(self, channel):  # Read single channel data
        data = 0
        Config_Set = (
            SGM_CONFIG_MODE_NOCONTINUOUS  # mode：Single-shot mode or power-down state    (default)
            | SGM_CONFIG_PGA_4096  # Gain= +/- 4.096V                              (default)
            | SGM_CONFIG_COMP_QUE_NON  # Disable comparator                            (default)
            | SGM_CONFIG_COMP_NONLAT  # Nonlatching comparator                        (default)
            | SGM_CONFIG_COMP_POL_LOW  # Comparator polarity：Active low               (default)
            | SGM_CONFIG_COMP_MODE_TRADITIONAL  # Traditional comparator                        (default)
            | SGM_CONFIG_DR_RATE_480
        )  # Data rate=480Hz                             (default)
        if channel == 0:
            Config_Set |= SGM_CONFIG_MUX_SINGLE_0
        elif channel == 1:
            Config_Set |= SGM_CONFIG_MUX_SINGLE_1
        elif channel == 2:
            Config_Set |= SGM_CONFIG_MUX_SINGLE_2
        elif channel == 3:
            Config_Set |= SGM_CONFIG_MUX_SINGLE_3
        Config_Set |= SGM_CONFIG_OS_SINGLE_CONVERT
        self._write_word(SGM_POINTER_CONFIG, Config_Set)
        time.sleep(0.02)
        data = self._read_u16(SGM_POINTER_CONVERT)
        return data

    def _read_u16(self, cmd):
        LSB = self._bus.read_byte_data(self._address, cmd)
        MSB = self._bus.read_byte_data(self._address, cmd + 1)
        return (LSB << 8) + MSB

    def _write_word(self, cmd, val):
        Val_H = val & 0xFF
        Val_L = val >> 8
        val = (Val_H << 8) | Val_L
        self._bus.write_word_data(self._address, cmd, val)


if __name__ == "__main__":
    print("\nSGM58031 Test Program ...\n")
    sgm58031 = SGM58031()
    state = sgm58031._read_u16(SGM_POINTER_CONFIG) & 0x8000

    if state != 0x8000:
        print("\nSGM58031 Error\n")

    while True:
        try:
            time.sleep(0.5)
            AIN0_DATA = sgm58031.SGM58031_SINGLE_READ(0)
            AIN1_DATA = sgm58031.SGM58031_SINGLE_READ(1)
            AIN2_DATA = sgm58031.SGM58031_SINGLE_READ(2)
            AIN3_DATA = sgm58031.SGM58031_SINGLE_READ(3)
            print(
                "\nAIN0 = %d(%.2fmv) ,AIN1 = %d(%.2fmv) ,AIN2 = %d(%.2fmv) AIN3 = %d(%.2fmv)\n\r"
                % (
                    AIN0_DATA,
                    AIN0_DATA * 0.125,
                    AIN1_DATA,
                    AIN1_DATA * 0.125,
                    AIN2_DATA,
                    AIN2_DATA * 0.125,
                    AIN3_DATA,
                    AIN3_DATA * 0.125,
                )
            )
        except KeyboardInterrupt:
            print("\nProgram end")
            break
