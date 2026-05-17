import time
import board
import busio
import digitalio
import sdcardio
import storage

MOUNT_POINT = "/sd"
TEST_PATH = MOUNT_POINT + "/spi_probe.txt"

# Probe both candidate pins so we can quickly rule out a CS mapping issue.
CS_CANDIDATES = [
    ("D12", board.D12),
    ("D5", board.D5),
    ("D11", board.D11),
    ("D25", board.D25),
]


def _looks_like_jedec_id(jedec_bytes):
    # 00/FF patterns usually mean floating bus or no device response.
    return jedec_bytes not in (b"\x00\x00\x00", b"\xff\xff\xff")


def probe_raw_spi_flash_id(cs_name, cs_pin):
    print("\n--- Raw SPI JEDEC probe on CS {} ---".format(cs_name))

    spi = None
    cs = None
    try:
        spi = busio.SPI(board.SCK, board.MOSI, board.MISO)
        cs = digitalio.DigitalInOut(cs_pin)
        cs.direction = digitalio.Direction.OUTPUT
        cs.value = True

        if not spi.try_lock():
            print("SPI lock failed")
            return False

        try:
            spi.configure(baudrate=1000000, phase=0, polarity=0)
            tx = bytearray([0x9F, 0x00, 0x00, 0x00])
            rx = bytearray(4)

            cs.value = False
            spi.write_readinto(tx, rx)
            cs.value = True

            jedec = bytes(rx[1:4])
            print(
                "JEDEC bytes on {}: {:02X} {:02X} {:02X}".format(
                    cs_name, jedec[0], jedec[1], jedec[2]
                )
            )

            if _looks_like_jedec_id(jedec):
                print("Raw SPI response detected on {}".format(cs_name))
                return True

            print("No useful raw SPI response on {}".format(cs_name))
            return False
        finally:
            spi.unlock()
    except Exception as exc:
        print("Raw SPI probe failed on {}: {}".format(cs_name, exc))
        return False
    finally:
        try:
            if cs is not None:
                cs.deinit()
        except Exception as exc:
            print("CS deinit warning: {}".format(exc))
        try:
            if spi is not None:
                spi.deinit()
        except Exception as exc:
            print("SPI deinit warning: {}".format(exc))


def probe_sd_emulation(cs_name, cs_pin):
    print("\n=== Probe start: CS {} ===".format(cs_name))

    spi = None
    try:
        spi = busio.SPI(board.SCK, board.MOSI, board.MISO)
        print("SPI object created on SCK/MOSI/MISO")
    except Exception as exc:
        print("SPI create failed: {}".format(exc))
        return False

    mounted = False
    for attempt in range(1, 4):
        print("Attempt {} on CS {}".format(attempt, cs_name))
        try:
            sd = sdcardio.SDCard(spi, cs_pin)
            print("sdcardio.SDCard created")

            vfs = storage.VfsFat(sd)
            print("VfsFat created")

            storage.mount(vfs, MOUNT_POINT)
            print("Mounted {}".format(MOUNT_POINT))
            mounted = True
            break
        except Exception as exc:
            print("Mount path failed: {}".format(exc))
            time.sleep(0.2)

    if not mounted:
        print("Result on {}: FAIL (no SD-style response)".format(cs_name))
        try:
            spi.deinit()
            print("SPI deinitialized")
        except Exception as exc:
            print("SPI deinit warning: {}".format(exc))
        return False

    try:
        with open(TEST_PATH, "w") as handle:
            handle.write("SPI storage probe OK on {}\n".format(cs_name))
        with open(TEST_PATH, "r") as handle:
            payload = handle.read().strip()
        print("Readback OK: {}".format(payload))
        print("Result on {}: PASS".format(cs_name))
        return True
    except Exception as exc:
        print("File IO failed after mount: {}".format(exc))
        print("Result on {}: PARTIAL (mounted, but IO failed)".format(cs_name))
        return False
    finally:
        try:
            storage.umount(MOUNT_POINT)
            print("Unmounted {}".format(MOUNT_POINT))
        except Exception as exc:
            print("Unmount warning: {}".format(exc))
        try:
            spi.deinit()
            print("SPI deinitialized")
        except Exception as exc:
            print("SPI deinit warning: {}".format(exc))


def main():
    print("SPI storage diagnostic starting")
    print("Candidates: {}".format(", ".join(name for name, _ in CS_CANDIDATES)))
    print("Note: D11 is commonly display CS; D25 is commonly SD socket CS on your TFT board.")

    any_sd_success = False
    any_jedec_success = False
    for cs_name, cs_pin in CS_CANDIDATES:
        if probe_raw_spi_flash_id(cs_name, cs_pin):
            any_jedec_success = True
        time.sleep(0.1)

        if probe_sd_emulation(cs_name, cs_pin):
            any_sd_success = True
        # Give CircuitPython a short beat before reopening SPI on next pin.
        time.sleep(0.1)

    print("\n=== Summary ===")
    if any_sd_success:
        print("At least one CS pin worked with sdcardio.")
    elif any_jedec_success:
        print("Raw SPI device answered, but no CS pin behaved like SD media.")
        print("This usually means the module is SPI flash, not SD-emulation for sdcardio.")
    else:
        print("No candidate CS pin responded to SD mount or JEDEC ID.")
        print("Likely causes: CS mismatch, DI/DO swap, or bad module/wiring.")


main()
