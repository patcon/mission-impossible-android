"""
MIA - Mission Impossible: Hardening Android for Security and Privacy

This project is a attempting to streamline the process of following Mike Perry's
Android hardening tutorial on the Tor blog:
    https://blog.torproject.org/blog/mission-impossible-hardening-android-security-and-privacy

Please keep in mind that this is experimental, and may not be functional at any
given moment. Also, it will likely wipe your Android device, and this is by
design!

Usage:
    mia [options] <command> [<command_args_and_opts>...]
    mia --help

Global options:
    --debug     Spew out debug information.
    --verbose   Spew out even more information than normal.
    --quiet     Restrict output to warnings and errors.
    -h, --help  Show this screen.
    --version   Show version.

Available commands:
    build       Build an update.zip file.
    clean       Cleanup the current workspace.
    definition  Create and configure a definition for a new update.zip file
                based on existing templates.
    help        Display detailed information about a certain command.
    install     Install the OS and the built update.zip file onto the device.

See 'mia help <command>' for more information on a specific command.

"""

# Get the path of the mission-impossible-android project.
import os
ROOT = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))

# Get the current directory.
WORKSPACE = os.getcwd()

# Add the script root the the PYTHONPATH environment variable.
import sys
sys.path.append(ROOT)

# Import docopt - the command-line interface description language.
# @see https://github.com/docopt/docopt/releases
from docopt import docopt

# Import custom helpers.
from mia import (__version__)
from mia.helpers.utils import *


def delegate_command(command_name, command_args):
    """
    Main command handler.
    """
    # Get the MIA handler singleton.
    handler = MiaHandler()

    # Prepare the the argv parameter for the command specific docopt.
    command_argv = [command_name] + command_args

    command_exists = False
    if command_name == 'build':
        import mia.commands.build
        command_exists = True
    elif command_name == 'clean':
        import mia.commands.clean
        command_exists = True
    elif command_name == 'help':
        import mia.commands.help
        command_exists = True
    elif command_name == 'definition':
        import mia.commands.definition
        command_exists = True
    elif command_name == 'install':
        import mia.commands.install
        command_exists = True

    if command_exists:
        # Get the command handler.
        command_handler = getattr(mia.commands, command_name)

        handler.args = docopt(command_handler.__doc__, argv=command_argv)

        # Remove command from the command arguments list.
        del handler.args[command_name]

        command_handler.main()
    else:
        msg = 'Command "%s" does not exists or has not been implemented yet!'
        print(msg % command_name)


def main():
    # Read the CLI arguments.
    # Use options_first to force reading the global options only.
    global_args = docopt(__doc__, version=__version__, options_first=True)

    # Create the MiaHandler instance. It can be used in other modules in order
    # to retrieve arguments, configuration, a logger...
    MiaHandler(ROOT, WORKSPACE, global_args)

    # Execute the command.
    try:
        delegate_command(
            global_args['<command>'],
            global_args['<command_args_and_opts>']
        )
    except KeyboardInterrupt:
        print('\n' + 'Exiting...')
        pass

    return 0


if __name__ == "__main__":
    sys.exit(main())
