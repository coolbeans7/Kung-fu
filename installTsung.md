# Install on each Node

$ su

# Perl Templating-Toolkit and the Gnu plotting utility to create HTML and graphical reports with the result data set.
$ apt-get install gnuplot-nox libtemplate-perl libhtml-template-perl libhtml-template-expr-perl

# download Tsung
#http://tsung.erlang-projects.org/dist/

$ tar -xvf tsung-1.3.3.tar.gz
$ cd tsung-1.3.3

# You need erlang-dev and erlang-src to compile tsung on ubuntu
$ apt-get install erlang-dev
$ apt-get install erlang-src

$./configure && make && sudo make install

#directory
/usr/local/share/tsung/

# create the .tsung/ directory in ~/.tsung (/home/huber/.tsung)
$ mkdir ./tsung


# create the configuration file and executed

$ tsung -f huberflores_example.xml start
#Configuration file is below this script

$ cd .tsung/log/20110614-21:58/


# Configure Each Node Communication

Change name to the host
$ nano /etc/hosts

172.17.x.x               tsung1
172.17.x.x               tsung2
172.17.x.x               tsung3


# alternative
$ nano /etc/hostname
$ nano /etc/resolv.conf

local node  
$ cd /root/.ssh

Create keys in each node
$ ssh-keygen -t dsa 
$ chmod 600 .ssh/id_dsa 

install the key in the remote node
$ cat id_dsa.pub >> /root/.ssh/authorized_keys 

connecting ssh without a password
$ ssh-agent sh -c 'ssh-add < /dev/null && bash'

#try each node
$ ssh tsung1
$ ssh tsung2
$ ssh tsung3

# Each connection must be perfomed without password

# If this error emerged, then repeat "#Configure Each Node Communication" section.

Host key verification failed
Host key verification failed Host key verification failed


This is because tsung search by host name (not ip address).
