import os
import yaml

# Instructions:
# Run this script from the log folder from which you want to process data

# ------------------------------


######################
# Run Elastic Fusion #
######################

# later, I want to try automatically install ElasticFusion
# or at least check for it
# for now, just need to specify ElasticFusion executable location
path_to_ElasticFusion_executable = "/home/peteflo/ElasticFusion/GUI/build/ElasticFusion"

path = os.getcwd()
yaml_path = path + "/info.yaml"
f = open(yaml_path)
dataMap = yaml.safe_load(f)
lcmlog_filename = dataMap["lcmlog"]

os.system(path_to_ElasticFusion_executable + " -l ./" + lcmlog_filename + " -f")


###################################################
# Convert from binary to ascii .ply, then to .vtp #
###################################################


#os.system("../src/ply/ply2ascii <" + path + filename + "> " + path + "converted.ply")
