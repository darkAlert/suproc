# suproc
This package allows to create and manage Single Unique Processes

## Installation
### Manual installation
```
git clone https://github.com/darkAlert/suproc.git
cd suproc
bash install.sh
```

### Installation via pip
```
pip3 install git+https://github.com/darkAlert/suproc.git#egg=suproc
```

#### Troubleshooting
Update pip if the package is installed with the name UNKNOWN:
```
python3 -m pip install --upgrade pip
```

### Uninstalling
```
pip3 uninstall suproc -y
```

### Initialization
Before use, initialize and create directories for PID and LOG files:
```
suproc init
```

## Usage
Available commands:

#### run
Create and run a single instance process:
- `name`                       Process name to run
- `-c CMDS, --cmds CMDS`       List of command strings
- `-f, --force`                Kill the running process and restart it
- `-d, --daemon`               Create a daemon process
- `-pd PDIR, --pdir PDIR`      PIDLockFile directory (`/var/run/ava/` by default)
- `-ld LDIR, --ldir LDIR`      Logs directory (`/var/log/ava/` by default)
- `-p PARENT, --parent PARENT` The parent process ID.
- `-sh SHELL, --shell SHELL`   If true, the command will be executed through the shell.

#### kill
Kill a single instance process by its name:
- `name`                  Process name to kill
- `-nk, --no-killer-proc` Create a killer process and try to kill the target process in it
- `-f, --force`           If set, the current process may also be killed!
- `-p, --purge`           Remove the pid and log files of the killed process
- `-pd PDIR, --pdir PDIR` PIDLockFile directory
- `-ld LDIR, --ldir LDIR` Logs directory

#### log
Print logs of a single instance process by its name (NOTE: the log is created only for processes running in daemon mode):
- `name`                          Process name to print its log
- `-f, --follow`                  Follow new lines and print them as they appear
- `-n LAST_N, --last-n LAST_N`    The number of lines to print from the end of the file
- `-s SESSION, --session SESSION` Print the full log of the specified process session
- `-rm, --remove`                 Remove a log file by process name
- `-c, --clear`                   Clear the log file according to the session number
- `-ld LDIR, --ldir LDIR`         Logs directory   

#### runs
Print a list of processes:
- `-a, --all`             Print processes with any state
- `-pd PDIR, --pdir PDIR` PIDLockFile directory

#### logs
Print a list of logs of processes:
- `-c, --clear`           Delete all logs without processes
- `-p, --paths`           Print log file paths instead of log names
- `-pd PDIR, --pdir PDIR` PIDLockFile directory
- `-ld LDIR, --ldir LDIR` Logs directory 

#### init
Initialize and create directories for PID and LOG files:
- `-pd PDIR, --pdir PDIR` PIDLockFile directory
- `-ld LDIR, --ldir LDIR` Logs directory 


### Terminal
Create and start a process named `test` that will execute the bash command: `ls / -l`:
```
suproc run test -c='ls / -l'
```

Same thing, but the process will be run in daemon mode:
```
suproc run test -d -c='ls / -l'
```

Show the log of the running process:
```
suproc log test
```

Kill process:
```
suproc kill test
```

### Python
TO DO...