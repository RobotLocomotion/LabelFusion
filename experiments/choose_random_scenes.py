import random
from random import shuffle
random.seed(1337)


file_all_in = "drill_all_scenes.txt"

NUM_TEST = 11

drill_11_test_scenes     = []
drill_50_train_scenes = []
drill_25_train_scenes = []
drill_10_train_scenes = []
drill_5_train_scenes  = []
drill_2_train_scenes  = []
drill_1_train_scenes  = []


with open(file_all_in) as f:
    content = f.readlines()

content = [x.strip() for x in content]

shuffle(content)

for index, scene in enumerate(content):

	print scene

	## First 11 only in test set
	if index < NUM_TEST:
		drill_11_test_scenes.append(scene)
		continue

	train_index = index - NUM_TEST

	## Rest all in train_50
	if train_index < 50:
		drill_50_train_scenes.append(scene)

	if train_index < 25:
		drill_25_train_scenes.append(scene)

	if train_index < 10:
		drill_10_train_scenes.append(scene)

	if train_index < 5:
		drill_5_train_scenes.append(scene) 

	if train_index < 2:
		drill_2_train_scenes.append(scene)

	if train_index < 1:
		drill_1_train_scenes.append(scene)


def writeToFile(scene_list, name):
	print len(scene_list)
	target = open(name+".txt", 'w')
	for i in scene_list:
		target.write(i)
		target.write("\n")
	target.close()

writeToFile(drill_11_test_scenes, "drill_11_test_scenes")
writeToFile(drill_50_train_scenes, "drill_50_train_scenes")
writeToFile(drill_25_train_scenes, "drill_25_train_scenes")
writeToFile(drill_10_train_scenes, "drill_10_train_scenes")
writeToFile(drill_5_train_scenes, "drill_5_train_scenes")
writeToFile(drill_2_train_scenes, "drill_2_train_scenes")
writeToFile(drill_1_train_scenes, "drill_1_train_scenes")
