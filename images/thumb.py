
import os, sys

for img in os.listdir("."):
  if not img.endswith(".jpg"):
    continue

  os.system("convert -thumbnail 80x112 %s %s" % (img, img))


