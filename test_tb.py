import logging.handlers
import time
import os

from dotenv import load_dotenv
from tb_device_client import ThingsBoardDevice

load_dotenv()

logging.basicConfig(format="%(asctime)s - %(message)s", level=logging.INFO)


def get_pi_data():
    cpu_usage = round(
        float(
            os.popen(
                """grep 'cpu ' /proc/stat | awk '{usage=($2+$4)*100/($2+$4+$5)} END {print usage }' """
            )
            .readline()
            .replace("\n", "")
            .replace(",", ".")
        ),
        2,
    )
    ip_address = (
        os.popen("""hostname -I""").readline().replace("\n", "").replace(",", ".")[:-1]
    )
    mac_address = (
        os.popen("""cat /sys/class/net/*/address""")
        .readline()
        .replace("\n", "")
        .replace(",", ".")
    )
    processes_count = (
        os.popen("""ps -Al | grep -c bash""")
        .readline()
        .replace("\n", "")
        .replace(",", ".")[:-1]
    )
    swap_memory_usage = (
        os.popen("free -m | grep Swap | awk '{print ($3/$2)*100}'")
        .readline()
        .replace("\n", "")
        .replace(",", ".")[:-1]
    )
    ram_usage = float(
        os.popen("free -m | grep Mem | awk '{print ($3/$2) * 100}'")
        .readline()
        .replace("\n", "")
        .replace(",", ".")[:-1]
    )
    st = os.statvfs("/")
    used = (st.f_blocks - st.f_bfree) * st.f_frsize
    boot_time = os.popen("uptime -p").read()[:-1]
    avg_load = (cpu_usage + ram_usage) / 2
    cpu_temp = float(os.popen("cat /sys/class/thermal/thermal_zone0/temp | awk '{print $1/1000}'")
    .readline()
        .replace("\n", "")
        .replace(",", "."))
    
    gpu_temp = float(os.popen("vcgencmd measure_temp | grep  -o -E '[[:digit:]].*'")
    .readline()
        .replace("\n", "")
        .replace("'C", "")
        .replace(",", "."))

    attributes = {"ip_address": ip_address, "macaddress": mac_address}
    telemetry = {
        "cpu_usage": cpu_usage,
        "processes_count": processes_count,
        "disk_usage": used,
        "RAM_usage": ram_usage,
        "swap_memory_usage": swap_memory_usage,
        "boot_time": boot_time,
        "avg_load": avg_load,
        "cpu_temp": cpu_temp,
        "gpu_temp": gpu_temp
    }
    # print(attributes, telemetry)
    return attributes, telemetry


def main():
    pi = ThingsBoardDevice(
        os.getenv("THINGSBOARD_PI_ACCESS_TOKEN"),
        states={"blinkingPeriod": 1.0},
        rpc_callbacks={"getTelemetry": "publish"},
    )
    # led = digitalio.DigitalInOut(board.D14)
    # led.direction = digitalio.Direction.OUTPUT
    # now rpc_callback will process rpc requests from server
    pi.get_data = get_pi_data

    try:
        while True:
            pi.publish()
            time.sleep(60)
    except KeyboardInterrupt:
        print("KeyboardInterrupt")

    # Blink the LED
    # led.value = True
    # time.sleep(period)
    # led.value = False
    # time.sleep(period)


if __name__ == "__main__":
    main()
