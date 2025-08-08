import math
import argparse
import logging
import sys
import signal

from sensors import LPS22HB, SHTC3, ICM20948, TCS34725
from prometheus_client import start_http_server, Summary
from prometheus_client.core import GaugeMetricFamily, REGISTRY

try:
    import smbus, lgpio
except ImportError:
    smbus = lgpio = None

log = logging.getLogger("sensehat-b-exporter")
log.setLevel(logging.INFO)
ch = logging.StreamHandler(sys.stdout)
ch.setLevel(logging.INFO)
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
ch.setFormatter(formatter)
log.addHandler(ch)

# Create a metric to track time spent and requests made.
REQUEST_TIME = Summary("request_processing_seconds", "Time spent processing request")


class SenseHatB(object):
    def __init__(self, bus=1):
        if smbus and lgpio:
            self.shtc3 = SHTC3.SHTC3(bus=bus)
            self.icm20948 = ICM20948.ICM20948()
            self.tcs34725 = TCS34725.TCS34725()
            self.lps22hb = LPS22HB.LPS22HB()

    @property
    def pressure(self):
        return self.lps22hb.pressure

    @property
    def lux(self):
        return self.tcs34725.lux

    @property
    def color_temp(self):
        return self.tcs34725.color_temp

    @property
    def gyroscope(self):
        return self.icm20948.gyroscope

    @property
    def orientation(self):
        return self.icm20948.orientation

    @property
    def acceleration(self):
        return self.icm20948.acceleration

    @property
    def magnetic(self):
        return self.icm20948.magnetic

    @property
    def temperature(self):
        return self.shtc3.temperature

    @property
    def humidity(self):
        return self.shtc3.humidity


class SenseHatBCollector(object):
    def __init__(self, sense):
        self.sense = sense

    def orientation_metric(self):
        roll, pitch, yaw = self.sense.orientation

        family = GaugeMetricFamily(
            name="sense_hat_b_orientation",
            documentation="° as measured by Waveshare Sense HAT (B)",
            labels=["axis"],
        )

        family.add_metric(["roll"], roll)
        family.add_metric(["pitch"], pitch)
        family.add_metric(["yaw"], yaw)
        return family

    def gyroscope_metric(self):
        gyro_x, gyro_y, gyro_z = self.sense.gyroscope
        family = GaugeMetricFamily(
            name="sense_hat_b_gyroscope",
            documentation="°/sec as measured by Waveshare Sense HAT (B)",
            labels=["axis"],
        )
        family.add_metric(["x"], gyro_x)
        family.add_metric(["y"], gyro_y)
        family.add_metric(["z"], gyro_z)
        return family

    def accelerometer_metric(self):
        accel_x, accel_y, accel_z = self.sense.acceleration

        family = GaugeMetricFamily(
            name="sense_hat_b_acceleration",
            documentation="G as measured by Waveshare Sense HAT (B)",
            labels=["axis"],
        )
        family.add_metric(["x"], accel_x)
        family.add_metric(["y"], accel_y)
        family.add_metric(["z"], accel_z)
        return family

    def magnetometer_metric(self):
        mag_x, mag_y, mag_z = self.sense.magnetic

        family = GaugeMetricFamily(
            name="sense_hat_b_magnetic_field",
            documentation="μT as measured by Waveshare Sense HAT (B)",
            labels=["axis"],
        )
        family.add_metric(["x"], mag_x)
        family.add_metric(["y"], mag_y)
        family.add_metric(["z"], mag_z)
        return family

    @REQUEST_TIME.time()
    def collect(self):
        yield GaugeMetricFamily(
            name="sense_hat_b_temperature_celsius",
            documentation="°C as measured by Waveshare Sense HAT (B)",
            value=self.sense.temperature,
        )

        yield GaugeMetricFamily(
            name="sense_hat_b_pressure_h_pascals",
            documentation="hPa as measured by Waveshare Sense HAT (B)",
            value=self.sense.pressure,
        )

        yield GaugeMetricFamily(
            name="sense_hat_b_humidity",
            documentation="Percent as measured by Waveshare Sense HAT (B)",
            value=self.sense.humidity,
        )

        yield GaugeMetricFamily(
            name="sense_hat_b_lux",
            documentation="Lux as measured by Waveshare Sense HAT (B)",
            value=self.sense.lux,
        )

        yield GaugeMetricFamily(
            name="sense_hat_b_color_temp",
            documentation="Kelvin as measured by Waveshare Sense HAT (B)",
            value=self.sense.color_temp,
        )

        yield GaugeMetricFamily(
            name="sense_hat_b_tilt",
            documentation="° as measured by Waveshare Sense HAT (B)",
            value=math.sqrt(sum(axis**2 for axis in self.sense.orientation[:2])),
        )

        yield GaugeMetricFamily(
            name="sense_hat_b_total_magnetic_field",
            documentation="μT as measured by Waveshare Sense HAT (B)",
            value=math.sqrt(sum(axis**2 for axis in self.sense.magnetic)),
        )

        # yield GaugeMetricFamily(
        #     name="sense_hat_b_total_acceleration",
        #     documentation="G as measured by Waveshare Sense HAT (B)",
        #     value=math.sqrt(sum(axis**2 for axis in self.sense.acceleration)),
        # )

        # yield GaugeMetricFamily(
        #     name="sense_hat_b_angular_velocity",
        #     documentation="°/sec as measured by Waveshare Sense HAT (B)",
        #     value=math.sqrt(sum(axis**2 for axis in self.sense.gyroscope)),
        # )

        yield self.orientation_metric()
        # yield self.accelerometer_metric()
        # yield self.gyroscope_metric()
        # yield self.magnetometer_metric()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    parser.add_argument(
        "--port", nargs="?", const=9111, help="The TCP port to listen on", default=9111
    )
    parser.add_argument(
        "--bind",
        nargs="?",
        const="0.0.0.0",
        help="The interface/IP to bind to",
        default="0.0.0.0",
    )
    parser.add_argument("--bus", help="The I2C bus to read", type=int, default=1)

    if smbus and lgpio:
        args = parser.parse_args()

        sense = SenseHatB(bus=args.bus)
        REGISTRY.register(SenseHatBCollector(sense))
        log.info("listening on http://%s:%d/metrics", args.bind, int(args.port))
        start_http_server(int(args.port), addr=args.bind)

        while True:
            signal.pause()
    else:
        log.error(
            "smbus or lgpio not available, please install the required libraries."
        )
        sys.exit(1)
