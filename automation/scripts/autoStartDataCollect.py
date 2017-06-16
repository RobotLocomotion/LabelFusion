import os

# Instructions:
# Run this script from anywhere

# set the amount of time you want to collect data
collection_time_seconds = 135

# ------------------------------

import datetime
from time import sleep
import copy

now = datetime.datetime.now()

YYYY = str(now.year).zfill(4)
MM   = str(now.month).zfill(2)
DD   = str(now.day).zfill(2)

basename = YYYY + "-" + MM + "-" + DD
print basename

# debug mkdir 
# for i in range(10):
#     NN = str(i).zfill(2)
#     os.system("mkdir " + basename + "-" + NN)

highest_scene_number = 0

for subdir, dirs, files in os.walk("./"):
    for dir in sorted(dirs):
        num_string_position = 11
        if len(dir) >= num_string_position+2:
            scene_number = int(dir[num_string_position:num_string_position+2])
            if scene_number > highest_scene_number:
                highest_scene_number = scene_number

new_scene_number = highest_scene_number + 1
new_dir = basename + "-" + str(new_scene_number).zfill(2)


def printAndSay(something):
    os.system("say " + something)
    print something

##############################
# -- starting gun

printAndSay('beginning data collection in')
seconds_to_count = 5
for i in range(seconds_to_count, 0, -1):
    printAndSay(str(i))
    sleep(1)
printAndSay("begin")

##############################
# -- collect data

os.system("mkdir " + new_dir)
os.system("cd " + new_dir + " && timeout " + str(collection_time_seconds) + "s lcm-logger " + new_dir + ".lcmlog &")

###############################
# -- this just gives warnings on how much time left

start = datetime.datetime.now()

warnings_for_seconds_left = [20, 10, 5, 4, 3, 2, 1]
for i in warnings_for_seconds_left:
    if i > collection_time_seconds:
        print "Need to adjust warnings_for_seconds_left"
        quit()

sleep_periods = copy.copy(warnings_for_seconds_left)
sleep_periods[0] = collection_time_seconds - warnings_for_seconds_left[0]
for i in range(1,len(warnings_for_seconds_left)):
    sleep_periods[i] = warnings_for_seconds_left[i-1] - warnings_for_seconds_left[i]

print "warning_seconds", warnings_for_seconds_left
print "sleep_periods", sleep_periods

for index, val in enumerate(sleep_periods):
    sleep(val)
    warn = str(warnings_for_seconds_left[index])
    print warn
    if val > 5:
        printAndSay(warn)
        printAndSay('seconds left')
    else:
        printAndSay(str(warnings_for_seconds_left[index]))

sleep(warnings_for_seconds_left[-1])
printAndSay('finished data collection')