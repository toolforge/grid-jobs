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
```

Create virtualenv inside kubernetes:
```
tools.grid-jobs@bastion:~$ webservice --backend=kubernetes python shell
tools.grid-jobs@interactive:~$ python3 -m venv ~/www/python/venv
tools.grid-jobs@interactive:~$ source ~/www/python/venv/bin/activate
(venv)tools.grid-jobs@interactive:~$ pip install -U pip
(venv)tools.grid-jobs@interactive:~$ pip install -r ~/www/python/src/requirements.txt
```

Back to bastion, start the webservice:
```
tools.grid-jobs@bastion:~$ webservice --backend=kubernetes python start
```

Creating the list is pretty expensive and we don't need it to be a real time
display, so a nice thing to do is setup a cron job to collect new data once an
hour:
```
21 * * * * jstart -N update-cache curl 'https://tools.wmflabs.org/grid-jobs/?purge'
```

License
-------
[GNU GPLv3+](//www.gnu.org/copyleft/gpl.html "GNU GPLv3+")

Forked from
[precise-tools](https://phabricator.wikimedia.org/source/tool-precise-tools/)
