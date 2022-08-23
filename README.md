# Social Group Sever 
## Installation

For most servers we provide and recommend using Ubuntu
20.04 (or newer), or Debian 11 (or newer).

# Installation Instructions

## Step 0: Do Not Run BSGS (social group server) as root

Do not run bsgs (social group server) as root.  Some inexperienced system administrators think it is easier to just run everything as root, without realizing that it is a significant security issue.  Just don't do it.

Instead, use an existing regular user or, even better, create a new regular user just for BSGS.

Use Python 3.7 or Python 3.8



## Step 1: Clone the Social group server repo

```bash
git clone https://github.com/Beldex-Coin/social-group-server 
cd social-group-server
```
## Step 2 : Run the shell to install dependencies
```
chmod +x packages.sh
./packages.sh
```

## Step 3: Edit bsgs.ini 

Edit it to change settings as desired.  At a minimum you must uncomment and set the `base_url`
setting to your Social Group URL; this can be a domain name or a public ip address.  Using a domain name is
recommended over a bare IP as it can later be moved to a new host or new ISP, while while a bare IP
cannot.

For example:

```ini
base_url = http://social.example.com
```
## Step 4: Edit uwsgi-bsgs.ini
### uwsgi.ini

Edit `uwsgi-bsgs.ini`, change relevant config settings including chdir, uid, gid.  Other settings
such as http port can also be altered if required.

```ini
chdir = LOCATION_OF_CLONED_DIRECTORY
uid = USER_RUNNING_BSGS
gid = USER_RUNNING_BSGS
http = :UNUSED_PORT
```

Do *not* change the `mount`, `enable-threads`, or `mule` configuration lines.

## Step 5: Run BSGS - (Bchat Social Group Server)

Once configured you can temporarily run Social group server by running the following command while inside the git
repository base directory:

```
uwsgi uwsgi-bsgs.ini
```
## To Run the Bchat Social Group Server (bsgs) Permentantly 

#### Run the command Inside Tmux 

## Step 6: Adding rooms, admins

In order to do anything useful you will want to add a room and admins to your BSGS installation
(unless upgrading: see below).

To interact with the BSGS database you want to run `python3 -mbsgs --help` from the bchat_social_group
directory which will give you a description of the available commands to control your BSGS
installation.

See [BSGS Administration](administration.md) for details, but note that where that document
indicates using the `bsgs` command you should instead use `python3 -mbsgs`  from the `social-group-server`
directory.

### Step 7: Check web viewer functionality

Navigating to your BSGS URL should display a web viewer of your social group, including any configured
rooms.  Navigating to the listed rooms will give you the full BSGS URL (and QR code) that is used to
have a Bchat client connect to the social group.


### Backing up

It is recommended that you make automatic, regular backups of your PyBSGS data files.  In particular
you want to regularly back up `bsgs.db` (which contains all the rooms and posts) and the `uploads`
directory (which contains uploaded files and room images).  You also want to make a one-time backup
of `key_x25519` (your BSGS private key needed to process BSGS requests).


## Administration

For how to administer a running PyBSGS Look into [BSGS Administration](administration.md).


## Credits
Copyright (c) 2021 The Oxen Project.
