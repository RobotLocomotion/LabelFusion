import os
import yaml
import csv
import re
import sys

# Instructions:
# Run this script from anywhere
# Use "-o" as an arg to record objects in each dataset

# ------------------------------
path_to_labelfusion  = os.environ['LABELFUSION_SOURCE_DIR']
path_to_data     = os.path.join(path_to_labelfusion, "data")
path_to_output   = os.path.join(path_to_labelfusion, "data/dataset_status.csv")

# folders in /data/logs to track
folders = ["logs_test", "logs_stable", "logs_arch"]

# record objects?
record_objects = False
if len(sys.argv) > 1:
    if sys.argv[1] == "-o":
        record_objects = True


rows = []
rows.append(["Name", "run_trim", "run_prep", "run_alignment_tool", "run_create_data", "run_reszie"])
total_labeled_imgs = 0
color_labels_pattern = re.compile("_labels.png")

def countNumberColorLabels(fullpath):
    global total_labeled_imgs
    counter = 0
    for filename in sorted(os.listdir(fullpath)):
        if color_labels_pattern.search(filename) is not None:
            counter += 1
            total_labeled_imgs += 1
    return counter

def readComment(fullpath):
    yaml_path = fullpath + "/info.yaml"
    if not os.path.isfile(os.path.join(yaml_path)):
        comment = " "
    else:
        f = open(yaml_path)
        dataMap = yaml.safe_load(f)
        if "comment" in dataMap:
            comment = dataMap["comment"]
        else:
            comment = " "
    return comment.ljust(25)[:25]

def recordObjects(fullpath):
    list_of_objects = []
    if os.path.isfile(fullpath):
        f = open(fullpath)
        dataMap = yaml.safe_load(f)
        for k in sorted(dataMap):
            list_of_objects.append(k)
    return list_of_objects

def checkIfExistsAndAppend(row, fullpath, file_to_check):
    if file_to_check == "images":
        if os.path.isfile(os.path.join(fullpath, "images/0000000001_rgb.png")):
            row.append("x")
        else:
            row.append("_")
        return
    if file_to_check == "resized_images":
        if os.path.isfile(os.path.join(fullpath, "resized_images/0000000001_labels.png")):
            row.append("x")
            row.append("imgs")
            n = countNumberColorLabels(os.path.join(fullpath, "resized_images"))
            nstr = '%05d' % n
            row.append(nstr)
        else:
            row.append("_")
            row.append("imgs")
            row.append("-----")
        return
            
    if os.path.isfile(os.path.join(fullpath, file_to_check)):
        row.append("x")
    else:
        row.append("_")

for folder in folders:
    path_to_folder = path_to_data + "/" + folder 
    rows.append([path_to_folder])

    for subdir, dirs, files in os.walk(path_to_folder):
        for dir in sorted(dirs):
            fullpath = os.path.join(subdir, dir)
            path_after_data =  os.path.relpath(fullpath, path_to_data)
            
            row = []
            print_name_length = 23
            row.append(path_after_data.ljust(print_name_length, "_")[:print_name_length]) # name

            checkIfExistsAndAppend(row, fullpath, "info.yaml")
            checkIfExistsAndAppend(row, fullpath, "reconstructed_pointcloud.vtp")
            checkIfExistsAndAppend(row, fullpath, "registration_result.yaml")
            checkIfExistsAndAppend(row, fullpath, "images")
            checkIfExistsAndAppend(row, fullpath, "resized_images")
            
            row.append(readComment(fullpath))

            if record_objects:
                row.append(recordObjects(os.path.join(fullpath, "registration_result.yaml")))

            rows.append(row)


        break # don't want recursive walk


with open(path_to_output, 'wb') as csvfile:
    spamwriter = csv.writer(csvfile, delimiter=' ',
                            quotechar='|', quoting=csv.QUOTE_MINIMAL)
    for row in rows:
        spamwriter.writerow(row)

    spamwriter.writerow(["You have " + str(total_labeled_imgs) + " total labeled imgs ready for training"])

os.system("cat " + path_to_output)
