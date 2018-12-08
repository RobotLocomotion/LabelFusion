import os
import yaml

# Instructions:
# Run this script from the log folder from which you want to process data

# ------------------------------
path_to_labelfusion = os.environ['LABELFUSION_SOURCE_DIR']

# Check if needs to run
if os.path.isfile("./reconstructed_pointcloud.vtp"):
	if os.path.isfile("./posegraph.posegraph"):
		print "Already have outputs of this step, don't need to run again!"
		quit()


######################
# Run Elastic Fusion #
######################

# later, I want to try automatically install ElasticFusion
# or at least check for it
# for now, just need to specify ElasticFusion executable location
path_to_ElasticFusion_executable = os.environ['ELASTIC_FUSION_EXECUTABLE']
if not (os.path.isfile(path_to_ElasticFusion_executable)):
	print "You need to install ElasticFusion and set the path to the executable in setup_environment.sh"
	quit()


path = os.getcwd()
yaml_path = path + "/info.yaml"
f = open(yaml_path)
dataMap = yaml.safe_load(f)
lcmlog_filename = dataMap["lcmlog"]

# call ElasticFusion
cameraConfig_arg = ""
if os.path.isfile("camera.cfg"):
    cameraConfig_arg += " -cal camera.cfg"
os.system(path_to_ElasticFusion_executable + " -l ./" + lcmlog_filename + cameraConfig_arg)

# rename posegraph
# TODO: give error if multiple posegraph files
os.system("mv " + lcmlog_filename + ".posegraph posegraph.posegraph")


###################################################
# Convert from binary to ascii .ply, then to .vtp #
###################################################

# install ply if do not already have it
path_to_ply = path_to_labelfusion + "/src/ply"
if not (os.path.isdir(path_to_ply)):
 	os.system("cd " + path_to_labelfusion + " && mkdir src && cd src && git clone https://github.com/peteflorence/ply.git")	
 	os.system("cd " + path_to_ply + " && make")	

ply_binary_filename = lcmlog_filename + ".ply"

# call ply2ascii
os.system(path_to_ply + "/ply2ascii <./" + ply_binary_filename + "> ./converted_to_ascii.ply")

# change header to be compatible with Director
# TODO: make so Director accepts other header?
line_elements_vertex = ""
with open("./converted_to_ascii_modified_header.ply", 'w') as outfile:
    with open("./converted_to_ascii.ply") as infile:
        counter = 0
        for line in infile:
            counter +=1
            if counter == 3:
                line_elements_vertex = line
                break
    with open(path_to_labelfusion + "/scripts/correct_ply_header.txt") as infile:
        counter = 0
        for line in infile:
            counter += 1
            if counter == 4:
                outfile.write(line_elements_vertex)
                continue
            outfile.write(line)
    with open("./converted_to_ascii.ply") as infile:
    	num_skip = 14
    	counter = 0
    	for line in infile:
    		counter += 1
    		if counter <= 14:
    			continue
    		outfile.write(line)

# convert to vtp
os.system("directorPython " + path_to_labelfusion + "/scripts/convertPlyToVtp.py " +  "./converted_to_ascii_modified_header.ply")

# clean up and rename
# os.system("rm *.ply *.freiburg")
os.system("mv converted_to_ascii_modified_header.vtp reconstructed_pointcloud.vtp")
