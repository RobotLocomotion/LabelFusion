# This script reads all of the files in ./train
# and resizes all .png files to be 480 x 360
#
###  Input:  .png files in ./images
###  Output: creates .png files 480 x 360 in ./resized_images

###  Warning: don't have `images` be a part of the name of your path except the last directory, or rework the pathing! 

import os
from PIL import Image

def resizeImage(filename_full_path, output_full_path):
  # adjust width and height to your needs
  width = 480
  height = 360
  
  try: 
    im_out = Image.open(output_full_path)
    if (im_out.size[0] == 480 and im_out.size[1] == 360):
          print "output already 480 x 360"
          return
  except(KeyboardInterrupt):
      quit()
  except:
    print "resizing..."

  try:
      im_in = Image.open(filename_full_path)
      if (im_in.size[0] == 480 and im_in.size[1] == 360):
          print "input already 480 x 360"
          return
      im_out = im_in.resize((width, height))    # best down-sizing filter
      im_out.save(output_full_path)
      print im_in.size, " --> ", im_out.size
  except(KeyboardInterrupt):
      quit()
  except:
      print "FAILED resizing"
      os.system("mv " + filename_full_path + " " + filename_full_path + "failed_resize")

def resizeDirectory(dir_name):
  cwd = os.getcwd()
  path_to_dir = cwd + "/" + dir_name
  for root, dirs, files in os.walk(path_to_dir):
      for filename in sorted(files):
          filename_full_path = os.path.join(root, filename)
          if filename_full_path.endswith(".png") and not filename_full_path.endswith("color_labels.png"):
              print "found .png match: " + filename_full_path
              output_full_path = filename_full_path.replace("images", "resized_images")
              resizeImage(filename_full_path, output_full_path)

os.system("mkdir resized_images")
resizeDirectory("images")