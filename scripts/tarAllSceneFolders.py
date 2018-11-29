#
# Usage: python /path/to/tarAllSceneFolders.py
#
# Iterates (non-recursively) over all scene folders and packages 
# them into .tar.gz compressed files

import os

for item in sorted(os.listdir(os.getcwd())):
    if os.path.isdir(os.path.join(os.getcwd(), item)):
        print item
        try:
            os.system("cd " + os.path.join(os.getcwd(),item) + " && ls")
            os.system("cd " + os.path.join(os.getcwd(),item) + " && tar_derived_data")
            #os.system("cd " + os.path.join(os.getcwd(),item) + " && tar_raw_log")
        except (KeyboardInterrupt, SystemExit):
            raise
