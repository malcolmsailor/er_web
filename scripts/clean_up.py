import os
import time

TEMP_DIR = os.path.join(
    os.path.dirname((os.path.realpath(__file__))), "../er_web/static/temp_files"
)

ONE_DAY = 60 * 60 * 24


def clean_up():
    now = time.time()
    with os.scandir(TEMP_DIR) as it:
        for entry in it:
            if not entry.is_file():
                continue
            mtime = entry.stat().st_mtime
            if now - mtime > ONE_DAY:
                print(entry.path)
                os.remove(entry.path)


if __name__ == "__main__":
    clean_up()
