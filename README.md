You could add more modules for other sites into the tarch controller.

**What's included** Sublime Text plugin for posting to ｲuﾶ乃ﾚ尺, modules for archiving social media circles to disk. Only ｲuﾶ乃ﾚ尺 and ՇฝٱՇՇﻉɼ included.

## Setup
Python 2.7

* tarch only works on unix as is. It could be easily ported though. Same goes for the python version.
* You need setup API accounts for the sites, and paste your pin numbers into the files at the correct spots.
* tarch.conf is an upstart job. That calls the program whenever the system starts. Put it in `/etc/init/`. It's optional.

## Dependencies:
* rauth
* Beautiful Soup 4 (AFAIK this **barely** gets used, so should get rid of it if possible)
