"""
Create and configure a definition in the current workspace using the provided
template.

Usage:
    mia definition create [--cpu=<cpu>] [--force] [--template=<template>]
                          [<definition>]
    mia definition configure <definition>
    mia definition lock [--force-latest] <definition>
    mia definition dl-apps <definition>
    mia definition dl-os <definition>
    mia definition extract-update <definition>

Command options:
    --template=<template>  The template to use. [default: mia-default]
    --cpu=<cpu>            The device CPU architecture. [default: armeabi]
    --force                Delete existing definition.

    --force-latest         Force using the latest versions.

Notes:
    A valid <definition> name consists of lowercase letters, digits and hyphens.
    And it must start with a letter name.

"""

import re
import shutil
from urllib.request import urlretrieve
from urllib.parse import urljoin
import xml.etree.ElementTree as ElementTree

# Import custom helpers.
from mia.helpers.android import *
from mia.helpers.utils import *


def main():
    # Get the MIA handler singleton.
    handler = MiaHandler()

    # The definition name is optional, this is helpful for new users.
    if handler.args['<definition>'] is None:
        msg = 'Please provide a definition name'
        handler.args['<definition>'] = input_ask(msg)

    if not re.search(r'^[a-z][a-z0-9-]+$', handler.args['<definition>']):
        # raise Exception('Definition "%s" already exists!' % definition)
        print('ERROR: Please provide a valid definition name! '
              'See: mia help definition')
        sys.exit(1)

    # Create the definition.
    if handler.args['create']:
        create_definition()

    # Configure the definition.
    if handler.args['configure']:
        configure_definition()

    # Create the apps lock file.
    if handler.args['lock']:
        create_apps_lock_file()

    # Download the CyanogenMod OS.
    if handler.args['dl-os']:
        download_os()

    # Download apps.
    if handler.args['dl-apps']:
        download_apps()

    # Extract the update-binary from the CyanogenMod zip file.
    if handler.args['extract-update']:
        extract_update_binary()

    return None


def create_definition():
    # Get the MIA handler singleton.
    handler = MiaHandler()

    definition_path = handler.get_definition_path()
    print('Destination directory is:\n - %s\n' % definition_path)

    # Make sure the definition does not exist.
    if os.path.exists(definition_path):
        if handler.args['--force']:
            print('Removing the old definition folder...')
            shutil.rmtree(definition_path)
        else:
            # raise Exception('Definition "%s" already exists!' % definition)
            print('ERROR: Definition "%s" already exists!' %
                  handler.args['<definition>'])
            sys.exit(1)

    template = handler.args['--template']
    template_path = os.path.join(handler.get_root_path(), 'templates', template)
    print('Using template:\n - %s\n' % template_path)

    # Check if the template exists.
    if not os.path.exists(template_path):
        # raise Exception('Template "%s" does not exist!' % template)
        print('ERROR: Template "%s" does not exist!' % template)
        sys.exit(1)

    # Make sure the definitions folder exists.
    os.makedirs(os.path.join(handler.get_workspace_path(), 'definitions'),
                mode=0o755, exist_ok=True)

    # Create the definition using the provided template.
    shutil.copytree(template_path, definition_path)

    # Configure the definition.
    if input_confirm('Configure now?', True):
        print()
        configure_definition()


def configure_definition():
    # Get the MIA handler singleton.
    handler = MiaHandler()

    # Detect the device codename.
    cm_device_codename = get_cyanogenmod_codename()
    print('Using device codename: %s\n' % cm_device_codename)

    # Detect the CyanogenMod release type.
    if input_confirm('Use recommended CyanogenMod release type?', True):
        cm_release_type = get_cyanogenmod_release_type(True)
    else:
        cm_release_type = get_cyanogenmod_release_type(False)
    print('Using release type: %s\n' % cm_release_type)

    # Detect the CyanogenMod release version.
    if input_confirm('Use recommended CyanogenMod release version?', True):
        cm_release_version = get_cyanogenmod_release_version(True)
    else:
        cm_release_version = get_cyanogenmod_release_version(False)
    print('Using release version: %s\n' % cm_release_version)

    # The path to the definition settings.yaml file.
    definition_path = handler.get_definition_path()
    settings_file = os.path.join(definition_path, 'settings.yaml')
    settings_file_backup = os.path.join(definition_path, 'settings.orig.yaml')

    # Create a backup of the settings file.
    shutil.copy(settings_file, settings_file_backup)

    # Update the settings file.
    update_settings(settings_file, {'general': {
        'update': {
            'cm_device_codename': cm_device_codename,
            'cm_release_type': cm_release_type,
            'cm_release_version': cm_release_version,
        },
    }})

    # Create the apps lock file.
    create_apps_lock_file()

    # Download the CyanogenMod OS.
    if input_confirm('Download CyanogenMod OS now?', True):
        download_os()

    # Download apps.
    if input_confirm('Download apps now?', True):
        download_apps()


# TODO: Implement the APK lock functionality.
def create_apps_lock_file():
    # Get the MIA handler singleton.
    handler = MiaHandler()

    # Get the APK lock data.
    lock_data = get_apps_lock_info()

    definition_path = handler.get_definition_path()
    lock_file_path = os.path.join(definition_path, 'apps_lock.yaml')
    print('Creating lock file:\n - %s\n' % lock_file_path)

    import yaml
    fd = open(lock_file_path, 'w')
    try:
        fd.write(yaml.dump(lock_data, default_flow_style=False))
        fd.close()
    except yaml.YAMLError:
        print('ERROR: Could not save the lock file!')
        sys.exit(1)
    finally:
        fd.close()

    # Download apps.
    if handler.args['lock'] and input_confirm('Download apps now?', True):
        download_apps()


def get_apps_lock_info():
    # Get the MIA handler singleton.
    handler = MiaHandler()

    # Read the definition settings.
    settings = handler.get_definition_settings()

    if not settings['defaults']['repository_id']:
        print('Missing default repository id.')
        sys.exit(1)

    # Make sure the resources folder exists.
    os.makedirs(os.path.join(handler.get_workspace_path(), 'resources'),
                mode=0o755, exist_ok=True)

    # Download and read info from the index.xml file of all repositories.
    repositories_data = {}
    for repo_info in settings['repositories']:
        index_path = os.path.join(handler.get_workspace_path(), 'resources',
                                  repo_info['id'] + '.index.xml')

        if not os.path.isfile(index_path):
            index_url = '%s/%s' % (repo_info['url'], 'index.xml')
            print('Downloading the %s repository information from:\n - %s' %
                  (repo_info['name'], index_url))
            urlretrieve(index_url, index_path)

        # Parse the repository index file and return the XML root.
        xml_tree = ElementTree.parse(index_path)
        if not xml_tree:
            print('Error parsing file:\n - %s' % index_path)
        repo_info['tree'] = xml_tree.getroot()

        repositories_data[repo_info['id']] = repo_info

    apps_list = []
    warnings_found = False
    print('Looking for APKs:')
    for key, app_info in enumerate(settings['apps']):
        # Add app to list if download url was provided directly.
        if 'url' in app_info:
            app_info['package_name'] = os.path.basename(app_info['url'])
            app_info['package_url'] = app_info['url']
            del app_info['url']

            if 'name' not in app_info:
                # Use file name for application name.
                app_info['name'] = os.path.splitext(app_info['package_name'])[0]

            print(' - adding `%s`' % app_info['package_name'])
            apps_list.append(app_info)
            continue

        # Lookup the version code in the repository index.xml.
        if 'code' in app_info:
            # Use the default repository if no repo has been provided.
            if 'repo' not in app_info:
                app_info['repo'] = settings['defaults']['repository_id']

            # Get the application info.
            app_info = _xml_get_app_lock_info(repositories_data, app_info)
            if app_info is not None:
                repo_name = repositories_data[app_info['repository_id']]['name']
                msg = ' - found `%s` in the %s repository.'
                print(msg % (app_info['package_name'], repo_name))
                apps_list.append(app_info)
                continue

        warnings_found = True

    # Give the user a chance to fix any possible errors.
    if warnings_found and not input_confirm('Warnings found! Continue?'):
        sys.exit(1)

    return apps_list


def _xml_get_app_lock_info(data, app_info):
    # Get the MIA handler singleton.
    handler = MiaHandler()

    app_name = None
    app_package_name = None
    app_version_code = None

    # Use the latest application version code.
    if handler.args['--force-latest'] or 'code' not in app_info:
        app_info['code'] = 'latest'

    # Prepare a list of repositories to look into.
    repositories = [app_info['repo']]
    if 'fallback' in data[app_info['repo']]:
        repositories.append(data[app_info['repo']]['fallback'])

    for repo in repositories:
        for tag in data[repo]['tree'].findall('application'):
            if tag.get('id') and tag.get('id') == app_info['name']:
                app_name, app_package_name, app_version_code = \
                    _xml_get_app_download_info(tag, app_info['code'])

        # Only try the fallback repository if the application was not found.
        if app_package_name is not None:
            break

    if app_package_name is None and app_info['code'] == 'latest':
        print(' - no such app: %s' % app_info['name'])
        return None
    elif app_package_name is None:
        print(' - no package: %s:%s' % (app_info['name'], app_info['code']))
        return None

    return {
        'name': app_name,
        'repository_id': repo,
        'package_name': app_package_name,
        'package_code': int(app_version_code),
        'package_url': urljoin(data[repo]['url'], app_package_name),
    }


def _xml_get_app_download_info(tag, target_code):
    name = None
    apkname = None
    versioncode = None

    package = None
    if target_code == 'latest':
        package = tag.find('package')
    else:
        for item in tag.findall('package'):
            version_code = item.find('versioncode').text
            if int(version_code) == int(target_code):
                package = item
                break

    if package is not None:
        name = tag.find('name').text
        apkname = package.find('apkname').text
        versioncode = package.find('versioncode').text

    return name, apkname, versioncode


def download_apps():
    # Get the MIA handler singleton.
    handler = MiaHandler()

    # Read the definition settings.
    settings = handler.get_definition_settings()

    # Read the definition apps lock data.
    lock_data = handler.get_definition_apps_lock_data()

    for repo_group in lock_data:
        print('Downloading %s...' % repo_group)
        for apk_info in lock_data[repo_group]:
            print(' - downloading: %s' % apk_info['package_url'])
            download_dir = apk_info.get('path', 'user-apps')
            download_path = os.path.join(handler.get_definition_path(), download_dir)
            if not os.path.isdir(download_path):
                os.makedirs(download_path, mode=0o755)
            apk_path = os.path.join(download_path, apk_info['package_name'])
            path, http_message = urlretrieve(apk_info['package_url'], apk_path)
            print('   - downloaded %s' %
                  format_file_size(http_message['Content-Length']))


def download_os():
    print('\nNOTE: Command not finished yet; See instructions!\n')

    # Get the MIA handler singleton.
    handler = MiaHandler()

    # Read the definition settings.
    settings = handler.get_definition_settings()

    # Create the resources folder.
    resources_path = os.path.join(handler.get_workspace_path(), 'resources')
    if not os.path.isdir(resources_path):
        os.makedirs(resources_path, mode=0o755)

    url = 'https://download.cyanogenmod.org/?device=%s&type=%s' % (
        settings['general']['cm_device_codename'],
        settings['general']['cm_release_type']
    )

    file_name = handler.get_os_zip_filename()

    print('Download CyanogenMod for and save the file as\n - %s\n'
          'into the resources folder, then verify the file checksum.\n - %s\n'
          % (file_name, url))

    input_pause('Please follow the instructions before continuing!')

    # Download the CyanogenMod OS.
    if input_confirm('Extract update binary from the CM zip?', True):
        extract_update_binary()


def extract_update_binary():
    # Get the MIA handler singleton.
    handler = MiaHandler()

    # Get the resources folder.
    resources_path = os.path.join(handler.get_workspace_path(), 'resources')

    definition_path = handler.get_definition_path()

    # Get file path.
    zip_file_path = os.path.join(resources_path, handler.get_os_zip_filename())

    # The path to the update-binary file inside the zip.
    update_relative_path = 'META-INF/com/google/android/update-binary'

    print('Extracting the update-binary from:\n - %s' % zip_file_path)

    import zipfile

    if os.path.isfile(zip_file_path) and zipfile.is_zipfile(zip_file_path):
        # Extract the update-binary in the definition.
        fd = zipfile.ZipFile(zip_file_path)

        # Save the file; taken from ZipFile.extract
        source = fd.open(update_relative_path)
        destination = os.path.join(definition_path, 'other', 'update-binary')
        target = open(destination, 'wb')
        with source, target:
            shutil.copyfileobj(source, target)

        print('Saved the update-binary to the definition!')
    else:
        print('File does not exist or is not a zip file.')

