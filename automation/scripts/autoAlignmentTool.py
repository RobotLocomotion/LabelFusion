import os
import yaml
import csv
import re
import sys

# Instructions:
# Run this script from anywhere

# ------------------------------
path_to_labelfusion  = os.environ['LABELFUSION_SOURCE_DIR']
path_to_data     = os.path.join(path_to_labelfusion, 'data')

# folders in /data to track
folders = ["logs_test"]

progress_file_fullpath = ""

path_to_job_folder = ""

for folder in folders:
    path_to_folder = path_to_data + "/" + folder 
    progress_file_fullpath = os.path.join(path_to_folder, "auto_alignment_tool_in_progress.txt")

    if os.path.isfile(progress_file_fullpath):               # check wip condition
    	break

    for subdir, dirs, files in os.walk(path_to_folder):
        for dir in sorted(dirs):
          
            fullpath = os.path.join(subdir, dir)

            if not os.path.isfile(os.path.join(fullpath,"reconstructed_pointcloud.vtp")):	 # check pre condition
            	continue

            if os.path.isfile(os.path.join(fullpath, "registration_result.yaml")):      # check post condition
            	continue

            path_to_job_folder = fullpath
            break
            
        break # don't want recursive walk


if path_to_job_folder == "":
	quit()						# didn't find any jobs

print "Found a job! in ", path_to_job_folder

os.system("touch " + progress_file_fullpath)              # mark as wip
os.system("cd " + path_to_job_folder + " && run_alignment_tool")
os.system("rm " + progress_file_fullpath)                 # delete wip
