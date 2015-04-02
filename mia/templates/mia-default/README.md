
TODO: Add description of how things work.

## Folders for the generated update.zip

`init.d`:
  This folder will be copied to `/system/etc/init.d` in the generated
  mia-update.zip and it will end up in the phone at the same location.

`META-INF`:
  This folder will be copied to the root of the generated mia-update.zip.

`misc`:
  This folder will be copied to `/sdcard`

`system-lib`:
  The contents of this folder will be copied to `/system/lib` in the generated
  mia-update.zip and it will end up in the phone at the same location.

`user-data`:
  The contents of this folder will be copied to `/data/data` in the generated
  mia-update.zip and it will end up in the phone at the same location.


## Files for the generated update.zip
`other/updater-script`:
  This script will be copied to `META-INF/com/google/android/updater-script` in
  the generated mia-update.zip.

`other/update-binary`:
  This file is going to be extracted out of the CyanogenMod zip from
  `META-INF/com/google/android/update-binary` and it will be copied in the same
  place inside the generated mia-update.zip.


## Other Files

`other/firstboot.sh`:
  The [OpenRecoveryScript](http://www.teamw.in/OpenRecoveryScript) used to install CM and the Mission Impossible
  mia-update.zip and it will be copied into the phone at
  `/data/.firstboot.sh`

`other/openrecoveryscript`:
  The [OpenRecoveryScript](http://www.teamw.in/OpenRecoveryScript) used to install CM and the Mission Impossible
  mia-update.zip and it will be copied into the phone at
  `/cache/recovery/openrecoveryscript`

`settings.yaml`:
  This file contains a list of settings for the current definition.

`settings.orig.yaml`:
  This is the original file from the template.
