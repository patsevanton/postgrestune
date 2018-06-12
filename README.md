# postgrestune
Python script to analyse your PostgreSQL database configuration, and give tuning advice
This project is fork https://github.com/jfcoz/postgresqltuner rewrite to Python

### Install requirements: ###
```
apt-get install python-psutil or yum install python2-psutil
apt-get install python-pip or yum install python2-pip
apt-get install python-psycopg2 or yum install python-psycopg2
apt-get install python-packaging or yum install python-packaging
apt-get install python-colorama or yum install python-colorama
```
Add permissions:
```
chmod +x ./postgrestune.py
```
Run:
```
sudo -u postgres ./postgrestune.py
```

# For Russian:
Большую часть (думаю что 90%) оригинального скрипта переписал на Python.
Но малоиспользуемые опции я не написал в Python скрипте (например: .pgpass, ssh и другие).
Если кто-нибудь хочет попрактиковаться: проверить код, переписать в более правильном виде, добавить функциональность из Perl или из общих практик проверки PostgreSQL - милости прошу.
Присылайте Pull request.
Попробуйте проверить PostgreSQL на своих DEV, TEST базах данных.

# For English
Most (I think 90%) of the original script was rewritten in Python.
But little-used options I have not written in a Python script (eg:.pgpass, ssh and others).
If anyone wants to practice: check the code, rewrite it in a more correct form, add functionality from Perl or from General practices of PostgreSQL check-you are welcome.
Send a Pull request.
Try to test PostgreSQL on your DEV, TEST databases.
