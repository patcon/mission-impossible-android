#!/system/bin/sh
# One time fixup script to fix installed APP permissions

# Based on:
# https://raw.githubusercontent.com/CyanogenMod/android_vendor_cyanogen/a013434bb46bb06bf0b7c83817cbcfaf040c5874/prebuilt/common/bin/fix_permissions
# and http://forum.xda-developers.com/showthread.php?t=1441378

APPS=( \
com.android.inputmethod.latin \
com.android.nfc \
com.android.settings \
com.xabber.androiddev \
org.ethack.orwall \
org.torproject.android \
)

SIP_APP=com.csipsimple
BROWSER_APP=org.mozilla.fennec_fdroid
ORWALL_APP=org.ethack.orwall

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

MISC_DIR=/sdcard/misc
source $MISC_DIR/library.sh

# Get important UIDs for later
BROWSER_UID=$(get_app_uid $BROWSER_APP)
SIP_UID=$(get_app_uid $SIP_APP)
ORWALL_UID=$(get_app_uid $ORWALL_APP)

# Fix orwall's config UIDs
$SED -i /data/data/org.ethack.orwall/shared_prefs/org.ethack.orwall_preferences.xml -e "s/REPLACE_WITH_BROWSER_UID/$BROWSER_UID/"
$SED -i /data/data/org.ethack.orwall/shared_prefs/org.ethack.orwall_preferences.xml -e "s/REPLACE_WITH_SIP_UID/$SIP_UID/"

# Give OrWall full, permanent root access
echo "Importing Superuser database with orWall uid $APP_UID pre-authorized." >> /sdcard/init.log
mkdir -p /data/data/com.android.settings/databases
$SED -i $MISC_DIR/com.android.settings_su.sql -e "s/REPLACE_WITH_ORWALL_UID/$ORWALL_UID/"
/system/xbin/sqlite3 /data/data/com.android.settings/databases/su.sqlite < $MISC_DIR/com.android.settings_su.sql

# Generate SQL to create orWall app DB
SQL_FRAGMENT=""
while read APP_DATA; do
  APP_NAME=$(echo $APP_DATA | $CUT -f'1' -d':')
  APP_UID=$(get_app_uid $APP_NAME)
  APP_PORT_TYPE=$(echo $APP_DATA | $CUT -f'2' -d':')
  APP_PORT_TYPE=${APP_PORT_TYPE:-TransProxy} # Default port type
  SQL_LINE="INSERT INTO rules VALUES($APP_UID,'$APP_NAME','Tor',9040,'$APP_PORT_TYPE');"
  SQL_FRAGMENT="$SQL_LINE\n$SQL_FRAGMENT"
done < $MISC_DIR/app-list-orwall.txt
$SED -i $MISC_DIR/org.ethack.orwall_nat.sql -e "s/{{REPLACE_WITH_GENERATED_SQL}}/$SQL_FRAGMENT/"
mkdir -p /data/data/org.ethack.orwall/databases
/system/xbin/sqlite3 /data/data/org.ethack.orwall/databases/nat.s3db < $MISC_DIR/org.ethack.orwall_nat.sql


# Fix permissions for all apps
for APP in ${APPS[@]}
do
  PKG_LINE=$( $CAT /data/system/packages.xml | $EGREP "^[ ]*<package.*serId" | $GREP -v framework-res.apk | $GREP -v com.htc.resources.apk | $GREP -i $APP )
  APP_UID=$( $ECHO $PKG_LINE | $SED 's%.*serId="\(.*\)".*%\1%' |  $CUT -d '"' -f1)
  echo "Fixup for app $APP uid $APP_UID: " >> /sdcard/init.log
  $FIND /data/data/$APP -type d -exec $CHOWN $APP_UID:$APP_UID {} \;
  $FIND /data/data/$APP -type d -exec $CHMOD 0771 {} \;
  $FIND /data/data/$APP -type f -exec $CHOWN $APP_UID:$APP_UID {} \;
  $FIND /data/data/$APP -type f -exec $CHMOD 0660 {} \;
done

# For some reason, these settings are ignored if run from the updater-script,
# so we set them here:
/system/bin/settings put global adb_enabled 0
/system/bin/settings put secure location_providers_allowed ""
/system/bin/settings put global auto_time 0
/system/bin/settings put global airplane_mode_on 1 # XXX: Set, but not displayed in UI :/

# Change hostname for subsequent reboots
/system/bin/settings put secure device_hostname "localhost"

# Change hostname for current boot
setprop net.hostname localhost
echo localhost > /proc/sys/kernel/hostname

# The Tor binary does not start until RECEIVE_BOOT_COMPLETED is broadcast. We
# need the supporting data files created in the org.torproject.android
# directory prior to that.  Starting this service happens to check for these
# directories and generate them if missing (which they are on first boot).
#
# This is a hack, and race conditions might occur if the .firstboot.sh script gets to long.
am startservice org.torproject.android/org.torproject.android.service.TorService

# Fake BOOT_COMPLETE to force orwall to apply rules in background.
# TODO: Investigate why this doesn't happen on its own.
am broadcast -a android.intent.action.BOOT_COMPLETED -n org.ethack.orwall/.BootBroadcast

# Start time settings app so the user can set the clock.
# FIXME: This could be done better with our own wizard, or maybe even if we
# call into only specific activities of the CM one.
am start -a android.intent.action.MAIN -n 'com.android.settings/.Settings$DateTimeSettingsActivity'

rm $0 >> /sdcard/init.log

# XXX: Seems to fail? causes a reboot loop when enabled, and will mess with
# the settings wizard anyway :/.
#/system/bin/vdc cryptfs enablecrypto inplace thisisapassword
