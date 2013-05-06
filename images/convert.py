
import os, sys

for dds in os.listdir("."):
  if not dds.endswith(".dds"):
    continue

  os.system("convert %s %s" % (dds, dds.replace(".dds", ".png")))


