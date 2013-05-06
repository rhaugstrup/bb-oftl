
import msvcrt, traceback, urllib, os, sys


if __name__ == '__main__':
  try:
    print
    print "Checking for latest submitter version...",
    fetch = urllib.urlopen(
        "http://localhost:8080/submitter/OFTL-submitter-local.py").read()
    print "success."

    exec fetch in {'__name__': '__main__'}

  except SystemExit, return_code:
    sys.exit(return_code)

  except:
    print
    print "Received a fatal exception!"
    print
    print traceback.format_exc()
    print
    print ("If you believe the application is in error, "
        "please report to masher in the OFL forums.")
    print
    print "Press any key to close this window."
    msvcrt.getch()
    sys.exit(-1)

