"""
AVA Single Unique Process
© AVA, 2025
"""
import os
import pidlockfile
import shlex
import subprocess
import argparse
import signal
import time
from suproc.utils.logger import AvaLogger
from suproc.utils.printer import TablePrinter
from suproc.utils.utils import ask_user_yes_no
from suproc import __version__

PKJ_NAME = 'suproc'
CMD_RUN  = 'run'
CMD_KILL = 'kill'
CMD_LOG  = 'log'
CMD_RUNS  = 'runs'
CMD_LOGS  = 'logs'
CMD_INIT = f'{PKJ_NAME}-init'
PID_HEADER = '=== PID:'
LOCK_PROC = '__lock'
KILLER_PROC = '__killer'
PID_DIR = '/var/run/ava/'
LOG_DIR = '/var/log/ava/'
CONF_FILE ='/usr/lib/tmpfiles.d/ava.conf'


def _print_proc_output(process, logger, read_f):
    # Print stdout / stderr:
    while True:
        try:
            output = read_f.readline()
            #output = process.stdout.readline()
        except KeyboardInterrupt:
            logger.info(KeyboardInterrupt)
            break
        if output == '' and process.poll() is not None:
            break
        if output:
            logger.debug(output.strip())  # Print and remove trailing newline

    # Handle any remaining output after the process finishes
    for line in process.stdout.readlines():
        logger.debug(line.strip())

    # Check for errors
    if process.returncode != 0:
        for line in process.stderr.readlines():
            logger.error(f"{line.strip()}")


def _clear_global_lockfile(lockfile, returncode=0):
    with open(lockfile, "r+") as lf:
        lf.write("0\n")
        lf.flush()
    return returncode


def read_pid_from_pidfile(pidfile_path, logger : AvaLogger or None=None):
    """
    Reads the PID from a given PID lock file.

    Args:
        pidfile_path (str): The path to the PID lock file.
        logger (AvaLogger): Logger

    Returns:
        int or None: The PID as an integer if successfully read, otherwise None.
    """
    try:
        with open(pidfile_path, 'r') as f:
            pid_str = f.readline().strip()
            return int(pid_str)
    except FileNotFoundError:
        if logger is not None:
            logger.error(f"PID file not found: '{pidfile_path}'")
        return None
    except ValueError:
        if logger is not None:
            logger.error(f"Invalid PID found: '{pidfile_path}'")
        return None
    except Exception as e:
        if logger is not None:
            logger.error(f"An unexpected error occurred while reading: '{pidfile_path}'")
            logger.error(e)
        return None


def run_single_instance_proc(name, cmds: list or None=None, force=False, daemon=False,
                             pid_dir=PID_DIR, log_dir=LOG_DIR, parent=None, logger=None, shell=False):
    if cmds is None:
        cmds = ['true']            # dummy command for NONE

    # Check directories:
    try:
        if not os.path.exists(pid_dir):
            os.makedirs(pid_dir)
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)
    except PermissionError:
        if logger is None:
            logger = AvaLogger.get_logger(PKJ_NAME)
        logger.error(f"Permission denied: '{pid_dir}' or '{log_dir}'. Try running '{CMD_INIT}' first")
        return -8

    # If the process is not a daemon, then write the log to stdout/stderr, otherwise - to a file:
    if logger is None:
        if parent is None:
            logger = AvaLogger.get_logger(PKJ_NAME)
        else:
            logger = AvaLogger.get_logger(f'{PKJ_NAME}.{name}', os.path.join(log_dir, name + '.log'))

    # Path to PIDLockFile:
    _lockfile = str(os.path.join(pid_dir, LOCK_PROC + '.pid'))
    pidfile = str(os.path.join(pid_dir, name + '.pid'))

    # Kill the process if it is running:
    if force:
        kill_proc(name, pid_dir=pid_dir)

    # Create a daemon:
    if daemon:
        cmd_list = '" "'.join(cmd for cmd in cmds)
        cmd = f'{PKJ_NAME} {CMD_RUN} {name} --pdir={pid_dir} --ldir={log_dir} --parent={os.getpid()} --cmds "{cmd_list}"'
        if shell:
            cmd += ' --shell'

        try:
            with pidlockfile.PIDLockFile(_lockfile, timeout=0.1):       # global lock

                # Check the PIDLockFile of the created process:
                if os.path.exists(pidfile) and pidlockfile.PIDLockFile(pidfile).is_locked():
                    logger.error(f"Could not acquire lock on {pidfile}. Another instance might be running!")
                    return _clear_global_lockfile(_lockfile, -1)

                # Run detached process:
                process = subprocess.Popen(shlex.split(cmd), start_new_session=True,
                                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                                           stdin=subprocess.DEVNULL)

                # Check that the process started successfully and created a lock file:
                for i in range(20):
                    pid = read_pid_from_pidfile(pidfile)
                    if pid is not None and abs(pid) == process.pid:
                        logger.info(f'Daemon with PID:{process.pid} successfully created!')
                        return _clear_global_lockfile(_lockfile, process.pid)
                    time.sleep(0.05)

                logger.error(f'Cannot create a daemon with pidfile={pidfile}!')
                return _clear_global_lockfile(_lockfile, -2)

        except pidlockfile.LockTimeout:
            logger.error(f"Could not acquire lock on {_lockfile}")
            return -3
        except Exception as e:
            logger.error(e)
            return -4

    # Run a sequence of commands:
    try:
        with pidlockfile.PIDLockFile(pidfile, timeout=0.1):
            returncode = None
            stdin = subprocess.DEVNULL

            # If the parent process is None, then the current process is not detached (not a daemon):
            if parent is None:
                stdin = subprocess.PIPE
                with open(pidfile, "r+") as pf:
                    pf.write("-{0}\n".format(os.getpid()))      # invert PID in pidfile for a non-daemon process
                    pf.flush()
            else:
                logger.info(f'{PID_HEADER}{os.getpid()}, commands:{len(cmds)} ===')

            # Run the attached process and execute a sequence of commands:
            for i, cmd in enumerate(cmds):
                if parent is not None or len(cmds) > 1:
                    logger.info(f'= Executing cmd #{i+1}: "{cmd}"')
                try:
                    with open(f'/home/darkalert/{name}.out', 'w') as stdout_f:
                        cmd = cmd if shell else shlex.split(cmd)
                        my_env = os.environ.copy() | {'PYTHONUNBUFFERED': '1'}       # to flush python output buffer
                        process = subprocess.Popen(cmd, env=my_env, bufsize=1, text=True, shell=shell,
                                                   stdout=stdout_f, stderr=stdout_f, stdin=stdin)     # subprocess.PIPE
                        try:
                            with open(f'/home/darkalert/{name}.out', 'r') as read_f:
                                _print_proc_output(process, logger, read_f)
                        except Exception as e:
                            logger.error(f'EXEPTION!!! {e}')
                        returncode = process.returncode
                        if parent is not None:
                            logger.info(f'= cmd #{i+1} finished with exit code: {returncode}')

                except KeyboardInterrupt:
                    logger.warning(f'KeyboardInterrupt')
                    return -9
                except Exception as e:
                    logger.error(f'{e}')
                    return -4

                if returncode != 0:
                    if i+1 < len(cmds):
                        logger.info(f'= Aborted! The last command completed with a non-zero returncode!')
                    break
        return returncode

    except pidlockfile.LockTimeout:
        logger.error(f"Could not acquire lock on {pidfile}. Another instance might be running.")
        return -1
    except Exception as e:
        logger.error(f"An error occurred: {e}")
        return -4


def kill_proc(name, force=False, pid_dir=PID_DIR, log_dir=LOG_DIR,
              killer_proc: None | str=KILLER_PROC, purge=False):
    logger = AvaLogger.get_logger(PKJ_NAME)

    pidfile = str(os.path.join(pid_dir, name + '.pid'))

    if killer_proc is not None and len(killer_proc) != 0:
        # Create a killer process and try to kill the target process in it:
        if killer_proc == name:
            logger.error(f"Unable to kill the killer process: '{killer_proc}'!")
            return -1

        cmd = f'{PKJ_NAME} {CMD_KILL} {name} -pd={pid_dir} -ld={log_dir} --no-killer-proc'
        if force:
            cmd += ' --force'
        if purge:
            cmd += ' --purge'

        if run_single_instance_proc(name=killer_proc, pid_dir=pid_dir, cmds=[cmd]) < 0:
            return

        # Remove the PID file of the killed process:
        if (os.path.exists(pidfile) and purge
                and ask_user_yes_no(f"Delete '{name}' PID file {pidfile}? (yes/no): ", logger)):
            _lockfile = str(os.path.join(pid_dir, LOCK_PROC + '.pid'))
            with pidlockfile.PIDLockFile(_lockfile, timeout=1):          # global lock
                if os.path.exists(pidfile) and not pidlockfile.PIDLockFile(pidfile).is_locked():
                    try:
                        os.remove(pidfile)
                        logger.info(f'PID file deleted: {pidfile}')
                    except Exception as e:
                        logger.error(e)
                _clear_global_lockfile(_lockfile)

        # Remove the LOG file of the killed process:
        log_file = os.path.join(log_dir, name + '.log')
        if (os.path.exists(log_file) and purge
                and ask_user_yes_no(f"Delete '{name}' LOG file {log_file}? (yes/no): ", logger)):
            _lockfile = str(os.path.join(pid_dir, LOCK_PROC + '.pid'))
            with pidlockfile.PIDLockFile(_lockfile, timeout=1):  # global lock
                try:
                    os.remove(log_file)
                    logger.info(f'LOG file deleted: {log_file}')
                except Exception as e:
                    logger.error(e)
                _clear_global_lockfile(_lockfile)
    else:
        # Kill process via os.kill:
        pid = read_pid_from_pidfile(pidfile, logger=logger)

        if pid is None:
            return -2

        try:
            os.kill(abs(pid), 0)        # check if process alive
            cur_pid = os.getpid()
            if not force and (cur_pid == pid or pid < 0):
                logger.error(f"Unable to kill the current process:{cur_pid}! Use --force to force kill")
                return -3
            os.kill(abs(pid), signal.SIGTERM)
            logger.info(f"Process killed: PID:{pid}")
        except ProcessLookupError:
            if not purge:
                logger.error(f'No alive process with PID:{pid}! Use --purge to delete its PID file')
                return -4

    return 0


def print_log(name,  log_dir=LOG_DIR, follow=False, last_n=10, session=None, remove=False, clear=False):
    """
    Prints logs of running processes.

    Args:
        name (str): The name of the process to print its log.
        log_dir (str): Logs directory.
        follow (bool): Monitors new lines and prints them as they appear.
        last_n (int): The number of lines to print from the end of the file. Defaults to 10.
        session (int): Prints the full log of the specified process session. A negative value reverses the order.
                       A value of zero prints the full log.
        remove (bool): Remove the log file.
        clear (bool): Clear the log file according to the session number. If the session is None, the entire log
                      will be cleared. Otherwise, the log will be cleared up to the session number.

    """
    logger = AvaLogger.get_logger(PKJ_NAME)

    # Log file path:
    path = os.path.join(log_dir, name + '.log')

    # Remove the log file and exit:
    if remove:
        if not os.path.exists(path):
            logger.error(f"No such file: '{path}'")
        else:
            if ask_user_yes_no(f"Remove log file {path}? (yes/no): ", logger):
                try:
                    os.remove(path)
                except Exception as e:
                    logger.error(e)
        return

    try:
        mode = 'r+' if clear else 'r'
        with open(path, mode) as file:

            # Print a full log starting from the specified process session and exit:
            if session is not None:
                lines = file.readlines()
                counter = 0
                # Find in reverse order:
                if session < 0:
                    found_line_i = 0
                    for i, line in enumerate(reversed(lines)):
                        if PID_HEADER in line:
                            counter += 1
                            if counter + session == 0:
                                found_line_i = len(lines) - i - 1
                                break

                # Find in straight order:
                elif session > 0:
                    found_line_i = None
                    for i, line in enumerate(lines):
                        if PID_HEADER in line:
                            if session - counter == 0:
                                found_line_i = i
                                break
                            counter += 1
                # Print a full log if session == 0:
                else:
                    found_line_i = 0

                if found_line_i is not None:
                    # Clear the log file:
                    if clear:
                        file.seek(0)
                        file.writelines(lines[found_line_i:])
                        file.truncate()

                    # Print lines starting from found line:
                    else:
                        for line in lines[found_line_i:]:
                            logger.debug(line.strip())
                return

            # Clear the log file:
            if clear:
                file.seek(0)
                file.truncate()
                return

            # Print the last n lines:
            lines = file.readlines()
            last_n_lines = lines[-last_n:]
            for line in last_n_lines:
                logger.debug(line.strip())

            # Go to the end of the file and follow it:
            if follow:
                file.seek(0, os.SEEK_END)
                while True:
                    line = file.readline()
                    if not line:
                        time.sleep(0.1)  # wait a bit if no new lines
                        continue
                    logger.debug(line if not line.endswith('\n') else line[:-1])

    except FileNotFoundError:
        logger.error(f"File not found: '{path}'")
    except KeyboardInterrupt:
        logger.warning('KeyboardInterrupt')
    except Exception as e:
        logger.error(e)


def logs(pid_dir=PID_DIR, log_dir=LOG_DIR, paths=False, clear=False):
    logger = AvaLogger.get_logger(PKJ_NAME)

    # Check directories:
    if not os.path.exists(log_dir):
        logger.error(f"No such directory: '{log_dir}'. Try running '{CMD_INIT}' first")
        return -8

    if clear:
        removing = []
    else:
        # Create Table printer and print header:
        header = f"|                Name                |   PID exists   |    Running    |"
        table = TablePrinter(header, alignment=['<', '^', '^'], logger=logger)
        table.print_special('outer')
        table.print_special('header')
        table.print_special('inner')

    for file in os.listdir(log_dir):
        if file.endswith('.log'):
            log_path = os.path.join(log_dir, file)
            name = file.split('.log')[0]
            pid_path = os.path.join(pid_dir, name + '.pid')

            # Check states:
            pid_exists = os.path.exists(pid_path)
            pid_locked = False
            if pid_exists:
                pid_locked = pidlockfile.PIDLockFile(pid_path).is_locked() is not None

            # Print row:
            if not clear:
                table.print_row((
                    log_path if paths else name,
                    'yes' if pid_exists else 'no',
                    'yes' if pid_locked else 'no')
                )
            # Add a log file without a PID file to the removing list:
            elif not pid_exists and not pid_locked:
                removing.append(log_path)

    # Print outer separator:
    if not clear:
        table.print_special('outer')
    # Delete log files:
    elif len(removing):
        if ask_user_yes_no(f"Delete {len(removing)} log files without PID? (yes/no): ", logger):
            counter = 0
            for log_path in removing:
                try:
                    os.remove(log_path)
                    counter += 1
                except Exception as e:
                    logger.error(e)
            logger.debug(f'{counter} files deleted!')


def runs(pid_dir=PID_DIR, show_all=False):
    logger = AvaLogger.get_logger(PKJ_NAME)

    # Check directories:
    if not os.path.exists(pid_dir):
        logger.error(f"No such directory: '{pid_dir}'. Try running '{CMD_INIT}' first")
        return -8

    # Create Table printer:
    header = f"|                Name                |     PID     |  Daemon  |    State    |"
    table = TablePrinter(header, alignment=['<', '^', '^', '^'], logger=logger)
    table.print_special('outer')
    table.print_special('header')
    table.print_special('inner')

    for file in os.listdir(pid_dir):
        if file.endswith('.pid'):
            name = file.split('.pid')[0]

            # Get pid:
            pid_path = os.path.join(pid_dir, file)
            pid = read_pid_from_pidfile(pid_path, logger=logger)

            # Check running and daemon:
            daemon = pid > 0
            locked = pidlockfile.PIDLockFile(pid_path).is_locked() is not None

            # Check if process alive:
            running = False
            if pid != 0:
                try:
                    os.kill(abs(pid), 0)
                    running = True
                except ProcessLookupError:
                    pass

            if locked != running:
                logger.warning(f"Process '{name}' (PID:{pid}) may be a zombie "
                               f"because it is locked={locked} but running={running}!")

            if not show_all and (not running or (name == KILLER_PROC or name == LOCK_PROC)):
                continue

            # Determine state:
            if running and locked:
                state = 'running'
            elif running != locked:
                state = f"zombie {'L' if locked else 'N'}:{'R' if running else 'N'}"
            else:
                state = '-'

            # Print:
            table.print_row((name, str(abs(pid)), 'yes' if daemon else 'no', state))
    table.print_special('outer')


def main():
    parser = argparse.ArgumentParser('ava-suproc',
                            description='This package allows to create and manage Single Unique Processes')
    parser.add_argument('-v', '--version', action='store_true', default=False,
                            help=f"Show the package version")
    subparsers = parser.add_subparsers(dest='command', help='Available commands')

    # Create a subparser for the 'RUN' command:
    parser_run = subparsers.add_parser(CMD_RUN, help='Create and run a single instance process')
    parser_run.add_argument( 'name', type=str, default=None,
                             help='Process name to run')
    parser_run.add_argument('-c', '--cmds', nargs='+', default=None,
                            help='List of command strings')
    parser_run.add_argument('-f', '--force', action='store_true', default=False,
                            help='Kill the running process and restart it')
    parser_run.add_argument('-d', '--daemon', action='store_true', default=False,
                            help='Create a daemon process')
    parser_run.add_argument('-pd', '--pdir', type=str, default=PID_DIR,
                            help='PIDLockFile directory')
    parser_run.add_argument('-ld', '--ldir', type=str, default=LOG_DIR,
                            help='Logs directory')
    parser_run.add_argument('-p', '--parent', type=int, default=None,
                            help='The parent process ID.')
    parser_run.add_argument('-sh', '--shell', action='store_true', default=False,
                            help='If true, the command will be executed through the shell')

    # Create a subparser for the 'KILL' command:
    parser_kill = subparsers.add_parser(CMD_KILL, help='Kill a single instance process by its name')
    parser_kill.add_argument('name', type=str, default=None,
                             help='Process name to kill')
    parser_kill.add_argument('-nk', '--no-killer-proc', action='store_true', default=False,
                             help='Create a killer process and try to kill the target process in it')
    parser_kill.add_argument('-f', '--force', action='store_true', default=False,
                             help='If set, the current process may also be killed!')
    parser_kill.add_argument('-p', '--purge', action='store_true', default=False,
                             help='Remove the pid file and log file of the killed process')
    parser_kill.add_argument('-pd', '--pdir', type=str, default=PID_DIR,
                             help='PIDLockFile directory')
    parser_kill.add_argument('-ld', '--ldir', type=str, default=LOG_DIR,
                             help='Logs directory')

    # Create a subparser for the 'LOG' command:
    parser_log = subparsers.add_parser(CMD_LOG, help='Print logs of a single instance process by its name')
    parser_log.add_argument('name', type=str, default=None,
                            help='Process name to print its log')
    parser_log.add_argument('-ld', '--ldir', type=str, default=LOG_DIR,
                            help='Logs directory')
    parser_log.add_argument('-f', '--follow', action='store_true', default=False,
                             help='Follow new lines and print them as they appear')
    parser_log.add_argument('-n', '--last-n', type=int, default=20,
                             help='The number of lines to print from the end of the file')
    parser_log.add_argument('-s', '--session', nargs='?', type=int, default=None, const=-1,
                            help=' Print the full log of the specified process session')
    parser_log.add_argument('-rm', '--remove', action='store_true', default=False,
                            help='Remove a log file by process name')
    parser_log.add_argument('-c', '--clear', action='store_true', default=False,
                            help='Clear the log file according to the session number.')

    # Create a subparser for the 'RUNS' command:
    parser_runs = subparsers.add_parser(CMD_RUNS, help='Print a list of processes')
    parser_runs.add_argument('-pd', '--pdir', type=str, default=PID_DIR,
                             help='PIDLockFile directory')
    parser_runs.add_argument('-a', '--all', action='store_true', default=False,
                             help='Print processes with any state')

    # Create a subparser for the 'LOGS' command:
    parser_logs = subparsers.add_parser(CMD_LOGS, help='Print a list of logs of processes')
    parser_logs.add_argument('-pd', '--pdir', type=str, default=PID_DIR,
                             help='PIDLockFile directory')
    parser_logs.add_argument('-ld', '--ldir', type=str, default=LOG_DIR,
                            help='Logs directory')
    parser_logs.add_argument('-c', '--clear', action='store_true', default=False,
                             help='Delete all logs without processes')
    parser_logs.add_argument('-p', '--paths', action='store_true', default=False,
                             help='Print log file paths instead of log names')

    args = parser.parse_args()

    # Run commands:
    if args.version:
        logger = AvaLogger.get_logger(PKJ_NAME)
        logger.info(__version__)
    elif args.command == CMD_RUN:
        run_single_instance_proc(
            name=args.name,
            cmds=args.cmds,
            force=args.force,
            daemon=args.daemon,
            pid_dir=args.pdir,
            log_dir=args.ldir,
            parent=args.parent,
            shell=args.shell
        )
    elif args.command == CMD_KILL:
        if args.no_killer_proc:
            kill_proc(name=args.name, force=args.force, pid_dir=args.pdir, log_dir=args.ldir, purge=args.purge,
                      killer_proc=None)
        else:
            kill_proc(name=args.name, force=args.force, pid_dir=args.pdir, log_dir=args.ldir, purge=args.purge)
    elif args.command == CMD_LOG:
        print_log(
            name=args.name,
            log_dir=args.ldir,
            follow=args.follow,
            last_n=args.last_n,
            session=args.session,
            remove=args.remove,
            clear=args.clear
        )
    elif args.command == CMD_RUNS:
        runs(
            pid_dir=args.pdir,
            show_all=args.all
        )
    elif args.command == CMD_LOGS:
        logs(
            pid_dir=args.pdir,
            log_dir=args.ldir,
            paths=args.paths,
            clear=args.clear
        )
    else:
        parser.print_help()
