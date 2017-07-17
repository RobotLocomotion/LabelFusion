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


while(True):
    try:
        path_to_job_folder = ""
        for folder in folders:
            path_to_folder = path_to_data + "/" + folder 
            # progress_file_fullpath = os.path.join(path_to_folder, "auto_create_data_and_resize_in_progress.txt")

            # if os.path.isfile(progress_file_fullpath):               # check wip condition
            #     print "exit wip"
            # 	break

            for subdir, dirs, files in os.walk(path_to_folder):
                for dir in sorted(dirs):
                  
                    fullpath = os.path.join(subdir, dir)

                    if not os.path.isfile(os.path.join(fullpath, "registration_result.yaml")):	       # check pre condition
                        print "exit pre"
                        print fullpath
                        continue

                    if os.path.isfile(os.path.join(fullpath, "images/0000000001_rgb.png")):            # check wip
                        print "exit in progress"
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

        os.system("cd " + path_to_job_folder + " && run_create_data")
        os.system("cd " + path_to_job_folder + " && run_resize")
    except KeyboardInterrupt:
        quit()
