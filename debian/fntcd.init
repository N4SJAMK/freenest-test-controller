#! /bin/bash
#
#
# /etc/init.d/fntcd
#
### BEGIN INIT INFO
# Provides: fntcd
# Required-Start: $local_fs $named
# Should-Start: 
# Required-Stop:  $local_fs
# Should-Stop:
# Default-Start:  3 5
# Default-Stop:   0 1 2 6
# Short-Description: FreeNest Test Client daemon process
# Description:    Runs up the FreeNest test client daemon process
### END INIT INFO

# Activate the python virtual environment ?
#    . /path_to_virtualenv/activate

case "$1" in
  start)
    echo "Starting fntcservice"
    # Start the daemon 
    twistd  --chroot=/ --rundir=/usr/bin/ --pidfile=/var/run/fntcservice/fntcservice.pid --logfile=/var/log/fntcservice.log -y /usr/bin/fntcd.py
    ;;
  stop)
    echo "Stopping fntcservice"
    # Stop the daemon
    kill `cat /var/run/fntcservice/fntcservice.pid`
    ;;
  restart)
    echo "Restarting fntcservice"
    kill `cat /var/run/fntcservice/fntcservice.pid`
    twistd  --chroot=/ --rundir=/usr/bin/ --pidfile=/var/run/fntcservice/fntcservice.pid --logfile=/var/log/fntcservice -y /usr/bin/fntcd.py
    ;;
  *)
    echo "Usage: /etc/init.d/fntcd.sh {start|stop|restart}"
    exit 1
    ;;
esac

exit 0

