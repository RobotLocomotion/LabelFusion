import os
import yaml
import csv

# Instructions:
# Run this script from anywhere

# ------------------------------
path_to_spartan  = os.environ['SPARTAN_SOURCE_DIR']
path_to_data     = path_to_spartan + "/src/CorlDev/data"
path_to_output   = path_to_spartan + "/src/CorlDev/data/dataset_status.csv"

# folders in /data/logs to track

folders = ["logs", "logs_test", "logs_labeled"]

rows = []

rows.append(["Name", "run_trim", "run_prep", "run_alignment_tool", "run_create_data"])

def checkIfExistsAndAppend(row, fullpath, file_to_check):
    if file_to_check == "images":
        if os.path.isfile(os.path.join(fullpath, "images/0000000001_color_labels.png")):
            row.append("x")
        else:
            row.append("_")
        return row
            
    if os.path.isfile(os.path.join(fullpath, file_to_check)):
        row.append("x")
    else:
        row.append("_")
    return row

for folder in folders:
    print "Now scanning folder: data/" + folder
    path_to_folder = path_to_data + "/" + folder 
    rows.append([path_to_folder])

    for subdir, dirs, files in os.walk(path_to_folder):
        for dir in dirs:
            fullpath = os.path.join(subdir, dir)
            path_after_data =  os.path.relpath(fullpath, path_to_data)
            print path_after_data
            
            row = []
            row.append(path_after_data) # name

            checkIfExistsAndAppend(row, fullpath, "trimmed_log.lcmlog")
            checkIfExistsAndAppend(row, fullpath, "reconstructed_pointcloud.vtp")
            checkIfExistsAndAppend(row, fullpath, "registration_result.yaml")
            checkIfExistsAndAppend(row, fullpath, "images")
            rows.append(row)


        break # don't want recursive walk


with open(path_to_output, 'wb') as csvfile:
    spamwriter = csv.writer(csvfile, delimiter=' ',
                            quotechar='|', quoting=csv.QUOTE_MINIMAL)
    for row in rows:
        spamwriter.writerow(row)

