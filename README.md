grid-jobs
=========

List tools running on Open Grid Engine exec nodes.

Install
-------

Clone repo and create basic files:
```
bastion$ become grid-jobs
tools.grid-jobs@bastion:~$ mkdir -p ~/www/python
tools.grid-jobs@bastion:~$ git clone https://phabricator.wikimedia.org/source/tool-grid-jobs.git ~/www/python/src
tools.grid-jobs@bastion:~$ touch ~/redis-prefix.conf
tools.grid-jobs@bastion:~$ chmod 600 ~/redis-prefix.conf
```
And edit `~/redis-prefix.conf` with a text editor.

Create virtualenv inside kubernetes:
```
tools.grid-jobs@bastion:~$ webservice --backend=kubernetes python2 shell
tools.grid-jobs@interactive:~$ virtualenv ~/www/python/venv
tools.grid-jobs@interactive:~$ source ~/www/python/venv/bin/activate
(venv)tools.grid-jobs@interactive:~$ pip install -U pip
(venv)tools.grid-jobs@interactive:~$ pip install -r ~/www/python/src/requirements.txt
```

Back to bastion, start the webservice:
```
tools.grid-jobs@bastion:~$ webservice --backend=kubernetes python2 start
```

License
-------
[GNU GPLv3+](//www.gnu.org/copyleft/gpl.html "GNU GPLv3+")

Forked from
[precise-tools](https://phabricator.wikimedia.org/source/tool-precise-tools/)
