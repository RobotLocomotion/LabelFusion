import getpass
import yaml

with open("configuration.yaml", 'r') as stream:
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