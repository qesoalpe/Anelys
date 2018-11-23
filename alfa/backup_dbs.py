import subprocess
from pathlib import Path
import os
from katherine import d6


date = '20181111'

dir = Path('/root/dump')

xz_args = ['-9e']

if not dir.exists():
    os.makedirs(dir)

pathsdump = dict()

logfile = open(dir / ('log-dump-' + date + '.log'), 'at', encoding='utf8')


ps = subprocess.Popen(['/var/lib/picazo/8757-1/bin/mongodump', '--archive'],
                      stderr=logfile, stdout=subprocess.PIPE)

filepath = dir / ('8757_1-dump-' + date + '.xz')

f = open(filepath, 'wb')

subprocess.run(['xz'] + xz_args, stdin=ps.stdout, stdout=f, stderr=logfile)

f.close()

pathsdump['8757-1'] = filepath


subprocess.run(['systemctl', 'stop', '8757-5'], stderr=logfile, stdout=logfile)

filepath = dir / ('8757_5-dump-' + date + '.mab')

subprocess.run(['/var/lib/picazo/8757-5/bin/neo4j-admin', 'dump', '--to=' + str(filepath)],
               stderr=logfile, stdout=logfile)

subprocess.run(['systemctl',  'start', '8757-5'], stderr=logfile, stdout=logfile)

filepath_in = filepath
filepath_out = dir / ('8757_5-dump-' + date + '.xz')
f_in = open(filepath, 'rb')
f_out = open(filepath_out, 'wb')

subprocess.run(['xz'] + xz_args, stderr=logfile, stdin=f_in, stdout=f_out)


f_in.close()
f_out.close()

os.remove(filepath_in)

pathsdump['8757-5'] = filepath_out


d6_not_databases = ['information_schema', 'mysql', 'performance_schema']

d6.ping(True)
d6_cursor = d6.cursor()

d6_cursor.execute('show databases;')
dbs_to_backup = [db for db, in d6_cursor if db not in d6_not_databases]

args = ['mysqldump', '--defaults-file=/var/lib/picazo/8757-6/mariad.conf', '--add-drop-table', '--databases'] \
       + dbs_to_backup

ps = subprocess.Popen(args, stderr=logfile, stdout=subprocess.PIPE)

filepath = dir / ('8757_6-dump-' + date + '.xz')

f = open(filepath, 'wb')

subprocess.run(['xz'] + xz_args, stdin=ps.stdout, stdout=f, stderr=logfile)

f.close()

pathsdump['8757-6'] = filepath

logfile.close()
