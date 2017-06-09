import os
import yaml



##################################################################################
# scp options

print "scp out..."

source = "/home/peteflo/hey_folder"
destination_user = "lucas"

# execute scp

scp_config_file = "scp_config.yaml"

with open(scp_config_file, 'r') as stream:
    try:
        config = yaml.load(stream)
    except yaml.YAMLError as exc:
        print(exc)

for i in config:
	print i
	if i == destination_user:
		print "found", i, "credentials"
		destination = config[i]['destination']
		address     = config[i]['address']
		port        = config[i]['port']
		pw			= config[i]['pw']

os.system("sshpass -p '" + pw + "' scp -r -P " + port + " " + source + " " + address+":"+destination)

