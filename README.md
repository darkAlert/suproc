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
sudo pip3 install git+https://github.com/darkAlert/suproc.git#egg=suproc  --break-system-packages
suproc-init
```
Before using the package, you have to run `suproc-init` to initialize it and create directories for the PID and LOG files.

#### Troubleshooting
Update pip if the package is installed with the name UNKNOWN:
```
python3 -m pip install --upgrade pip
```
If the package is not found in the terminal after installation, try running:
```
source ~/.profile
```

### Uninstalling
```
suproc-init --deinit
pip3 uninstall suproc -y  --break-system-packages
```

## Available commands
### suproc
#### run
Create and run a single instance process:
- `name`                       Process name to run
- `-c CMDS, --cmds CMDS`       List of command strings
- `-f, --force`                Kill the process if it is running
- `-d, --daemon`               Create a daemon process
- `-pd PDIR, --pdir PDIR`      PIDLockFile directory (`/var/run/ava/` by default)
- `-ld LDIR, --ldir LDIR`      Logs directory (`/var/log/ava/` by default)
- `-p PARENT, --parent PARENT` The parent process ID
- `-o STDOUT, --stdout STDOUT` Where to direct the process's stdout: `pipe`, `devnull`
- `-e STDERR, --stderr STDERR` Where to direct the process's stderr: `pipe`, `stdout`, `devnull`

#### stop
Stop a single instance process by its name:
- `name`                  Process name to stop
- `-nk, --no-killer-proc` Create a killer process and try to stop the target process in it
- `-f, --force`           If set, the current process may also be stopped!
- `-k, --kill`            Send SIGTERM instead of SIGINT
- `--purge`               Remove the pid and log files of the stopped process
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

### suproc-init
Managing the PID, LOGS, and CONFIG directories of 'suproc' package:
- `-pd PDIR, --pdir PDIR`       PIDLockFile directory
- `-ld LDIR, --ldir LDIR`       Logs directory
- `-cf CONF, --conf CONF`       Config file path 
- `-y YES, --yes YES`           Answer 'yes' to each question of the initializer
- `-de DEINIT, --deinit DEINIT` Deinitialize the package and remove all its files


### Terminal examples
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

### Python examples
TO DO...