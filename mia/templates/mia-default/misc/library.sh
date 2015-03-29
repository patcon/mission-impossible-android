#!/system/xbin/bash

# Programs needed
ECHO="busybox echo"
GREP="busybox grep"
EGREP="busybox egrep"
CAT="busybox cat"
CHOWN="busybox chown"
CHMOD="busybox chmod"
CUT="busybox cut"
FIND="busybox find"
SED="busybox sed"

get_app_uid()
# Usage get_app_uid <app name> [ <path/to/packages.xml> ]
{
  if [ -z "$1" ]
  then
    echo "Error: You did not pass an app name."
    exit 1
  fi

  local APP_NAME="$1"
  local APP_UID=$(
    $CAT /data/system/packages.xml \
      | $EGREP "^[ ]*<package.*serId" \
      | $GREP -v framework-res.apk \
      | $GREP -v com.htc.resources.apk \
      | $GREP -i "\"$APP_NAME\"" \
      | $SED 's%.*serId="\(.*\)".*%\1%' \
      |  $CUT -d '"' -f1 \
  )
  echo "$APP_UID"
}

