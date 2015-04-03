"""
Utilities for the mia script.
"""

import os
import sys


class Singleton(type):
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            super_class = super(Singleton, cls)
            cls._instances[cls] = super_class.__call__(*args, **kwargs)
        return cls._instances[cls]


class MiaHandler(metaclass=Singleton):
    args = {}
    global_args = {}
    __root_path = None
    __definition_path = None
    __definition_settings = {}
    __definition_apps_lock_data = {}

    def __init__(self, root_path=None, workspace_path=None, global_args=None):
        if root_path:
            self.__root_path = root_path

        if global_args:
            self.global_args = global_args

        if workspace_path:
            self.__workspace_path = workspace_path

    # Save and display a log message.
    def log(self, msg, log_type='info'):
        # Display the message to the user.
        if self.global_args['--verbose']:
            print(msg)

        # Log the message.
        import logging

        if log_type == 'info':
            logging.info(msg)
        elif log_type == 'warning':
            logging.error(msg)
        elif log_type == 'debug':
            logging.debug(msg)
        else:
            logging.error(msg)

    def get_root_path(self):
        return self.__root_path

    def get_workspace_path(self):
        return self.__workspace_path

    def get_definition_path(self):
        if not self.__definition_path and self.args['<definition>']:
            self.__definition_path = os.path.join(
                self.__workspace_path, 'definitions',
                self.args['<definition>']
            )

        return self.__definition_path

    def get_os_zip_filename(self):
        # Read the definition settings.
        settings = self.get_definition_settings()

        return 'cm-11-%s.%s-%s.zip' % (
            settings['general']['cm_device_codename'],
            settings['general']['cm_release_type'],
            settings['general']['cm_release_version']
        )

    def get_definition_settings(self, force_update=False):
        if (not self.__definition_settings and self.args['<definition>']) or \
                force_update:
            definition_path = self.get_definition_path()
            settings_file = os.path.join(definition_path, 'settings.yaml')
            if not force_update:
                print('Using definition settings file:\n - %s\n' %
                      settings_file)

            import yaml
            try:
                fd = open(settings_file, 'r')

                # Load the yaml and sort the top level entries.
                settings = yaml.load(fd)

                fd.close()
            except yaml.YAMLError:
                print('ERROR: Could not read configuration file!')
                return None

            if settings:
                self.__definition_settings = settings

        return self.__definition_settings

    def get_definition_apps_lock_data(self):
        if not self.__definition_apps_lock_data and self.args['<definition>']:
            definition_path = self.get_definition_path()
            lock_file_path = os.path.join(definition_path, 'apps_lock.yaml')
            print('Using lock file:\n - %s\n' % lock_file_path)

            if not os.path.isfile(lock_file_path):
                # raise Exception('Definition "%s" already exists!' % definition)
                print('ERROR: Apps lock file is missing! '
                      'See: mia help definition')
                sys.exit(1)

            import yaml
            try:
                fd = open(lock_file_path, 'r')

                # Load the yaml and sort the top level entries.
                lock_data = yaml.load(fd)

                fd.close()
            except yaml.YAMLError:
                print('ERROR: Could not read configuration file!')
                return None

            if lock_data:
                self.__definition_apps_lock_data = lock_data

        return self.__definition_apps_lock_data


def input_pause(display_text='Paused.'):
    input("%s\nPress enter to continue!\n" % display_text)


def input_confirm(display_text='Confirm', default_value=False):
    """
    Ask the user to confirm an action.
    :param display_text:
    :param default_value:
    :return: boolean
    """

    # Update the text depending on the default return value.
    if default_value:
        display_text = '%s [%s/%s]: ' % (display_text, 'Y', 'n')
    else:
        display_text = '%s [%s/%s]: ' % (display_text, 'y', 'N')

    while True:
        value = input(display_text)
        value = value.lower()

        # Return the default value.
        if not value:
            return default_value

        if value not in ['y', 'yes', 'n', 'no']:
            print('This is a yes and no question!')
            continue

        if value == 'y' or value == 'yes':
            return True
        if value == 'n' or value == 'no':
            return False


def input_ask(display_text, default_value=None, free_text=False):
    """
    Ask the user to provide a string.
    :param display_text:
    :param default_value:
    :return: string
    """

    # Update the text depending on the default return value.
    if default_value:
        display_text = '%s [%s]: ' % (display_text, default_value)
    else:
        display_text = '%s: ' % display_text

    while True:
        value = input(display_text)

        # Return the default value, if any.
        if not value and default_value is not None:
            return default_value
        elif not value:
            continue

        # Limit the allowed characters.
        if not free_text:
            import re
            if not re.search(r'^[a-z][a-z0-9-]+$', value):
                print('A sting containing letters, numbers, hyphens.')
                print('The string must start with a letter.')
                continue

        return value


# TODO: Find a way to keep comments in the setting files.
def update_settings(settings_file, changes):
    import yaml

    # Make sure the settings file exists.
    if not os.path.isfile(settings_file):
        print('Settings file "%s" not found' % settings_file)
        return None

    try:
        fd = open(settings_file, 'r')

        # Load the yaml and sort the top level entries.
        settings = yaml.load(fd)

        fd.close()
    except yaml.YAMLError:
        print('ERROR: Could not read configuration file!')
        return None

    for section in changes:
        # Update entries.
        if hasattr(changes[section], 'update'):
            for key in changes[section]['update']:
                settings[section][key] = changes[section]['update'][key]

        # Remove entries.
        if hasattr(changes[section], 'remove'):
            for key in changes[section]['remove']:
                del settings[section][key]

    # Save the changes.
    print("Updating settings file:\n - %s\n" % settings_file)

    try:
        # Define a custom order of the sections
        order = ['general', 'apps']
        for section in settings.keys():
            if section not in order:
                order.append(section)

        # Open the file.
        fd = open(settings_file, 'w')

        # Save all the settings in oder.
        for section in order:
            if section in settings.keys():
                data = {section: settings[section]}
                fd.write(yaml.dump(data, default_flow_style=False))

        fd.close()
    except yaml.YAMLError:
        fd.close()
        print('ERROR: Could not save configuration file!')
        return None

    # Get the MIA handler singleton.
    handler = MiaHandler()

    # Load the settings in the main handler file.
    handler.get_definition_settings(True)


def format_file_size(file_size, precision=2):
    import math
    file_size = int(file_size)

    if file_size is 0:
        return '0 bytes'

    log = math.floor(math.log(file_size, 1024))

    return "%.*f %s" % (
        precision,
        file_size / math.pow(1024, log),
        ['bytes', 'Kb', 'Mb'][int(log)]
    )


def version_compare(version1, version2, func='eq'):
    """
    Compare two Semantic Versions.
    @see http://semver.org/spec/v2.0.0.html
    """
    # @see https://docs.python.org/3.4/library/operator.html
    import operator

    from distutils.version import StrictVersion
    return getattr(operator, func)(
        StrictVersion(version1),
        StrictVersion(version2)
    )
