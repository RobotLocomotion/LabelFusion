import os

if not (os.path.isdir(os.getcwd() + "/../src/ply")):
	os.system("cd .. && mkdir src && cd src && git clone https://github.com/peteflorence/ply.git")
	os.system("cd ../src/ply && make")

path = os.getcwd() + "/../data/logs/pipeline-test/"
filename = "trimmed-log.lcmlog.ply"
#print path

os.system("../src/ply/ply2ascii <" + path + filename + "> " + path + "converted.ply")
