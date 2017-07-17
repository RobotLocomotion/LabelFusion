import getpass
import yaml
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
path_to_automation = os.path.join(path_to_labelfusion, 'automation')


config_file = path_to_automation + "/configuration.yaml"

with open(config_file, 'r') as stream:
    try:
        config = yaml.load(stream)
    except yaml.YAMLError as exc:
        print(exc)

print config

if 'leader' in config:
	leader = config['leader'] 
	print "leader: ", leader
else:
	print "Need a leader!  Add one to configuration.yaml"
	quit()

if 'followers' in config:
	print "followers:"
	followers = config['followers']
	for i, v in enumerate(followers):
		print " (", i, ") ", v
else:
	print "Somebody has to do some work!  Add >=1 followers to configuration.yaml"
	quit()


me = getpass.getuser()

if me == leader:
	print "I,", me, "am leader!"
	print "Assigning jobs..."
else:
	print "I, ", me, "am not leader... quit()"
	quit()


###



# folders in /data to track
folders = ["logs_test"]

paths_to_job_folders = ""

for folder in folders:
    path_to_folder = path_to_data + "/" + folder 

    for subdir, dirs, files in os.walk(path_to_folder):
        for dir in sorted(dirs):
          
            fullpath = os.path.join(subdir, dir)

            if not os.path.isfile(os.path.join(fullpath, "registration_result.yaml")):	       # check pre condition
            	print "exit pre"
                print fullpath
                continue

            if os.path.isfile(os.path.join(fullpath, "resized_images/0000000001_labels.png")): # check post condition
                print "exit post"
            	continue

            path_to_job_folder = fullpath
            break
            
        break # don't want recursive walk


if path_to_job_folder == "":
	quit()						# didn't find any jobs

print "Found a job! in ", path_to_job_folder



### 

# os.system("touch " + progress_file_fullpath)              # mark as wip
# os.system("cd " + path_to_job_folder + " && run_create_data")
# os.system("cd " + path_to_job_folder + " && run_resize")
# os.system("rm " + progress_file_fullpath)                 # delete wip
