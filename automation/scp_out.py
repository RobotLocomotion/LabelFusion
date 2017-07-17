import os
import yaml
import sys

source = sys.argv[1]
destination_user = sys.argv[2]

path_to_labelfusion  = os.environ['LABELFUSION_SOURCE_DIR']
scp_config_file = os.path.join(path_to_labelfusion, 'automation/scp_config.yaml')

with open(scp_config_file, 'r') as stream:
    try:
        config = yaml.load(stream)
    except yaml.YAMLError as exc:
        print(exc)

for i in config:
	if i == destination_user:
		print "found", i, "credentials"
		destination = config[i]['destination']
		address     = config[i]['address']
		port        = config[i]['port']
		pw			= config[i]['pw']

print "sending to ", destination_user
os.system("sshpass -p '" + pw + "' scp -r -P " + port + " " + source + " " + address+":"+destination)
print "sent", source
