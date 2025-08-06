#!/usr/bin/python
# -*- coding:utf-8 -*-
import time

try:
    import lgpio as sbc
except ImportError:
    sbc = None

SHTC3_I2C_ADDRESS = 0x70

SHTC3_ID = 0xEFC8
CRC_POLYNOMIAL = 0x0131
SHTC3_WakeUp = 0x3517
SHTC3_Sleep = 0xB098
SHTC3_Software_RES = 0x805D
SHTC3_NM_CD_ReadTH = 0x7866
SHTC3_NM_CD_ReadRH = 0x58E0


class SHTC3:
    def __init__(self, bus=1, sbc=sbc, address=SHTC3_I2C_ADDRESS, flags=0):
        if sbc is None:
            return

        self._sbc = sbc
        print({"bus": bus, "address": address, "flags": flags})
        self._fd = self._sbc.i2c_open(bus, address, flags)
        self.SHTC_SOFT_RESET()

    def SHTC3_CheckCrc(self, data, len, checksum):
        crc = 0xFF
        for byteCtr in range(len):
            crc = crc ^ data[byteCtr]
            for _ in range(8):
                if crc & 0x80:
                    crc = (crc << 1) ^ CRC_POLYNOMIAL
                else:
                    crc = crc << 1

        return crc == checksum

    def SHTC3_WriteCommand(self, cmd):
        self._sbc.i2c_write_byte_data(self._fd, cmd >> 8, cmd & 0xFF)

    def SHTC3_WAKEUP(self):
        self.SHTC3_WriteCommand(SHTC3_WakeUp)  # write wake_up command
        time.sleep(0.01)  # Prevent the system from crashing

    def SHTC3_SLEEP(self):
        self.SHTC3_WriteCommand(SHTC3_Sleep)  # Write sleep command
        time.sleep(0.01)

    def SHTC_SOFT_RESET(self):
        self.SHTC3_WriteCommand(SHTC3_Software_RES)  # Write reset command
        time.sleep(0.01)

    @property
    def temperature(self):
        self.SHTC3_WAKEUP()
        self.SHTC3_WriteCommand(SHTC3_NM_CD_ReadTH)
        time.sleep(0.02)
        (_, buf) = self._sbc.i2c_read_device(self._fd, 3)
        if self.SHTC3_CheckCrc(buf, 2, buf[2]):
            return (buf[0] << 8 | buf[1]) * 175 / 65536 - 45.0
        else:
            return 0  # Error

    @property
    def humidity(self):
        self.SHTC3_WAKEUP()
        self.SHTC3_WriteCommand(SHTC3_NM_CD_ReadRH)
        time.sleep(0.02)
        (_, buf) = self._sbc.i2c_read_device(self._fd, 3)

        if self.SHTC3_CheckCrc(buf, 2, buf[2]):
            return 100 * (buf[0] << 8 | buf[1]) / 65536
        else:
            return 0  # Error


if __name__ == "__main__":
    shtc3 = SHTC3()
    while True:
        try:
            print(
                f"Temperature = {shtc3.temperature:6.2f}°C, Humidity = {shtc3.humidity:6.2f}%"
            )
        except KeyboardInterrupt:
            print("\nProgram end")
            break
