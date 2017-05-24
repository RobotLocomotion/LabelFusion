import os
import yaml

# Instructions:
# Run this script from the log folder from which you want to process data

# ------------------------------
path_to_spartan = os.environ['SPARTAN_SOURCE_DIR']

######################
# Run Elastic Fusion #
######################

# later, I want to try automatically install ElasticFusion
# or at least check for it
# for now, just need to specify ElasticFusion executable location
path_to_ElasticFusion_executable = "/home/peteflo/ElasticFusion/GUI/build/ElasticFusion"
if not (os.path.isfile(path_to_ElasticFusion_executable)):
	print "You need to install ElasticFusion and change the path to the executable in scripts/prepareForObjectAlignment.py"
	quit()


path = os.getcwd()
yaml_path = path + "/info.yaml"
f = open(yaml_path)
dataMap = yaml.safe_load(f)
lcmlog_filename = dataMap["lcmlog"]

# call ElasticFusion
os.system(path_to_ElasticFusion_executable + " -l ./" + lcmlog_filename + " -f")

# rename posegraph
# TODO: give error if multiple posegraph files
os.system("mv " + lcmlog_filename + ".posegraph posegraph.posegraph")


###################################################
# Convert from binary to ascii .ply, then to .vtp #
###################################################

# install ply if do not already have it
path_to_ply = path_to_spartan + "/src/CorlDev/src/ply"
if not (os.path.isdir(path_to_ply)):
 	os.system("cd " + path_to_ply + "../ && mkdir src && cd src && git clone https://github.com/peteflorence/ply.git")	
 	os.system("cd " + path_to_ply + " && make")	

ply_binary_filename = lcmlog_filename + ".ply"

# call ply2ascii
os.system(path_to_ply + "/ply2ascii <./" + ply_binary_filename + "> ./converted_to_ascii.ply")

# change header to be compatible with Director
# TODO: make so Director accepts other header?
with open("./converted_to_ascii_modified_header.ply", 'w') as outfile:
    with open(path_to_spartan + "/src/CorlDev/scripts/correct_ply_header.txt") as infile:
        for line in infile:
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
os.system("directorPython " + path_to_spartan + "/src/CorlDev/scripts/convertPlyToVtp.py " +  "/home/peteflo/spartan/src/CorlDev/data/logs/pipeline-test/converted_to_ascii_modified_header.ply")

# clean up and rename
os.system("rm *.ply")
os.system("mv converted_to_ascii_modified_header.vtp reconstructed_pointcloud.vtp")