#
# Usage: python /path/to/cleanAllSceneFolders.py
#
# Iterates (non-recursively) over all scene folders and does 
# a couple cleaning operations.

import os

for item in os.listdir(os.getcwd()):
    if os.path.isdir(os.path.join(os.getcwd(), item)):
        print item
        os.system("cd " + os.path.join(os.getcwd(),item) + " && ls")
        os.system("cd " + os.path.join(os.getcwd(),item) + " && rm -f *.jlp *.freiburg && find . -name *lcmlog.ply | xargs -I '{}' mv {} binary.ply")
