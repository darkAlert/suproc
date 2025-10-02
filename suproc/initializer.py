"""
AVA Single Unique Process Uninstaller
© AVA, 2025
"""
import argparse
import subprocess

from suproc.utils.logger import AvaLogger
from suproc.utils.utils import ask_user_yes_no
from suproc.suproc import PID_DIR, LOG_DIR, CONF_FILE, __NAME__ as PACKAGE_NAME

__NAME__ = 'initializer'


def initialize(pid_dir=PID_DIR, log_dir=LOG_DIR, conf_file=CONF_FILE, yes=False, logger=None):
    if logger is None:
        logger = AvaLogger.get_logger(__NAME__)

    # Get username and user main group:
    import getpass, grp, pwd
    username = getpass.getuser()
    try:
        user_info = pwd.getpwnam(username)
        primary_gid = user_info.pw_gid
        group_name = grp.getgrgid(primary_gid).gr_name
    except KeyError:
        logger.error(f"User '{username}' not found!")
        return -1

    # Ask user:
    question = f"Create and configure '{conf_file}', '{pid_dir}', '{log_dir} for '{username}:{group_name}'? (yes/no): "
    if not yes and not ask_user_yes_no(question, logger=logger):
        return -5

    # Commands:
    cmd1 = f'echo "d {pid_dir} 0755 {username} {group_name}" | sudo tee {conf_file}'
    cmd2 = f'sudo mkdir -p {pid_dir} {log_dir}'
    cmd3 = f'sudo chown {username}:{group_name} {pid_dir} {log_dir}'

    # Execute:
    try:
        for cmd in [cmd1, cmd2, cmd3]:
            process = subprocess.Popen(cmd, text=True, shell=True, executable="/bin/bash",
                                       stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            _, stderr = process.communicate()
            if process.returncode != 0:
                logger.error(f"Command failed: '{cmd}'")
                logger.error(stderr)
                return -4

        if process.returncode == 0:
            logger.info(f"Successfully created")
        else:
            logger.info(f"Failed to create!")

    except Exception as e:
        logger.error(e)
        return -2

    return 0


def deinitialize(pid_dir=PID_DIR, log_dir=LOG_DIR, conf_file=CONF_FILE, yes=False, logger=None):
    if logger is None:
        logger = AvaLogger.get_logger(__NAME__)

    # 1. Ask user to remove directories and conf file:
    question = f"Remove '{conf_file}', '{pid_dir}' and '{log_dir}'? (yes/no): "
    if not yes and not ask_user_yes_no(question, logger=logger):
        return -5

    # Commands:
    cmd1 = (f'sudo rm {conf_file}', conf_file)
    cmd2 = (f'sudo rm -r {pid_dir}', pid_dir)
    cmd3 = (f'sudo rm -r {log_dir}', log_dir)

    # Execute:
    try:
        for (cmd, path) in [cmd1, cmd2, cmd3]:
            process = subprocess.Popen(cmd, text=True, shell=True, executable="/bin/bash",
                                       stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            _, stderr = process.communicate()
            if process.returncode != 0:
                logger.info(f"Failed to remove: '{path}'")
                logger.error(stderr)
            else:
                logger.info(f"Removed: '{path}'")

    except Exception as e:
        logger.error(e)
        return -2

    return 0


def main():
    parser = argparse.ArgumentParser('ava-suproc-initializer',
                        description=f"Managing the PID, LOGS, and CONFIG directories of '{PACKAGE_NAME}' package")
    parser.add_argument('-pd', '--pdir', type=str, default=PID_DIR,
                        help='PIDLockFile directory')
    parser.add_argument('-ld', '--ldir', type=str, default=LOG_DIR,
                        help='Logs directory')
    parser.add_argument('-cf', '--conf', type=str, default=CONF_FILE,
                        help='Config file path')
    parser.add_argument('-y', '--yes', action='store_true', default=False,
                        help="Answer 'yes' to each question of the initializer")
    parser.add_argument('-de', '--deinit', action='store_true', default=False,
                        help="Deinitialize package and remove all its files")

    args = parser.parse_args()

    if args.deinit:
        deinitialize(
            pid_dir=args.pdir,
            log_dir=args.ldir,
            conf_file=args.conf,
            yes=args.yes
        )
    else:
        initialize(
            pid_dir=args.pdir,
            log_dir=args.ldir,
            conf_file=args.conf,
            yes=args.yes
        )
