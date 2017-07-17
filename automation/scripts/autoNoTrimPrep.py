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

lcmlog_pattern = re.compile("lcmlog")

progress_file_fullpath = ""

def findLcmLog(dirpath):
	# returns lcmlog_file name if only finds 1
	# returns "" if found 0 or more than 1
	counter = 0
	lcmlog_file = ""
	for filename in sorted(os.listdir(fullpath)):
		if lcmlog_pattern.search(filename) is not None:
			lcmlog_file = filename
			counter += 1
	if counter == 1:
		return lcmlog_file
	else:
		return ""

path_to_job_folder = ""

for folder in folders:
    path_to_folder = path_to_data + "/" + folder 
    progress_file_fullpath = os.path.join(path_to_folder, "auto_no_trim_prep_in_progress.txt")

    if os.path.isfile(progress_file_fullpath):               # check wip condition
    	break

    for subdir, dirs, files in os.walk(path_to_folder):
        for dir in sorted(dirs):
          
            fullpath = os.path.join(subdir, dir)
            lcmlog_file = findLcmLog(fullpath)               
            if lcmlog_file == "":							 # check pre condition
            	continue

            if lcmlog_file.endswith("original_log.lcmlog"):  # check post condition
            	continue

            path_to_job_folder = fullpath
            break
            
        break # don't want recursive walk


if path_to_job_folder == "":
	quit()						# didn't find any jobs

print "Found a job! in ", path_to_job_folder

os.system("touch " + progress_file_fullpath)              # mark as wip
os.system("cd " + path_to_job_folder + " && run_no_trim")
os.system("cd " + path_to_job_folder + " && run_prep")
os.system("rm " + progress_file_fullpath)                 # delete wip
