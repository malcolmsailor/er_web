import os
import sys
import traceback

sys.path.insert(
    0, os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
)

import er_web.validators as validators

# TODO update this test
def process_er_constants():
    items = ("OCTAVE0 * A", "-FIFTH", "MAJOR_SCALE+7")
    try:
        for s in items:
            validators.process_er_constants(s)
    except:  # pylint: disable=bare-except
        import sys
        import traceback

        exc_type, exc_value, exc_traceback = sys.exc_info()
        traceback.print_exception(
            exc_type, exc_value, exc_traceback, file=sys.stdout
        )
        breakpoint()


if __name__ == "__main__":
    process_er_constants()
