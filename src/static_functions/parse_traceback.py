import os
import logging
import traceback


def parse_traceback():
    """
    Find Script in Traceback where last Error occurred
    """
    tb = traceback.format_exc()
    logging.critical(tb)

    traceback_lines = tb.split('\n')
    file = "<File not found>"
    line = "<Line not found>"
    line_number = "<Line Number not found>"
    for i, line in enumerate(traceback_lines):
        if line.startswith("  File ") and "scripts" in line:
            file, line_number, _ = line.split(', ')
            file = file[8:-1]
            file_path = file.split(os.sep)
            file = ''
            for e in file_path[file_path.index("scripts")+1:]:
                file += e + os.sep
            file = file[:-1]
            line_number = line_number[5:]
            line = traceback_lines[i+1][4:]
            break
        else:
            continue

    return file, line, line_number
