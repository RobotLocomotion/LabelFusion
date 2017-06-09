import os
import yaml


##################################################################################
# scp options

print "scp out..."

source = "/home/peteflo/hey_folder"
destination_user = "pat"

# execute scp
os.system("python scp_out.py " + source + " " + destination_user)
