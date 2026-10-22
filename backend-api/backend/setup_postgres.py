"""Move a consistent SQLite snapshot into a NEW PostgreSQL schema.

Run locally in CMD. Password input stays on this machine. Existing schemas and
the SQLite database are never overwritten. API configuration changes last.
"""
import argparse
from datetime import datetime,timezone
from getpass import getpass
import json
import os
from pathlib import Path
import re
import sqlite3
import socket
import tempfile
from urllib.parse import quote,urlencode

from sqlalchemy import create_engine,inspect,MetaData,Table,select,func,text,Integer,DateTime
from sqlalchemy.engine import URL

ROOT=Path(__file__).resolve().parent


class SetupError(Exception):pass


def schema_name(value):
    if not re.fullmatch(r'[a-z][a-z0-9_]{0,47}',value) or value in ('public','information_schema') or value.startswith('pg_'):
        raise SetupError('Ten schema phai la ten rieng, vi du fake_review_app.')
    return value


def database_url(host,port,database,user,password,schema):
    schema_name(schema)
    if host not in ('localhost','127.0.0.1','::1'):raise SetupError('Cong cu nay chi ket noi PostgreSQL tren may local.')
    address='['+host+']' if ':' in host else host
    return 'postgresql+psycopg2://'+quote(user,safe='')+':'+quote(password,safe='')+'@'+address+':'+str(port)+'/'+quote(database,safe='')+'?'+urlencode({'options':'-csearch_path='+schema})


def update_env(path,url):
    """Preserve existing settings and store the URL without printing it."""
    original=path.read_text(encoding='utf-8') if path.exists() else ''
    lines=[line for line in original.splitlines() if not re.match(r'^\s*(?:export\s+)?DATABASE_URL\s*=',line)]
    lines.append('DATABASE_URL='+json.dumps(url,ensure_ascii=True))
    if original:
        stamp=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
        path.with_name('.env.before-postgres.'+stamp).write_text(original,encoding='utf-8')
    with tempfile.NamedTemporaryFile(mode='w',encoding='utf-8',dir=path.parent,prefix='.env.tmp.',delete=False) as file:
        file.write('\n'.join(lines)+'\n');temporary=Path(file.name)
    os.replace(temporary,path)


def sqlite_backup(source,destination):
    if not source.is_file():raise SetupError('Khong tim thay database SQLite nguon.')
    with sqlite3.connect('file:'+source.as_posix()+'?mode=ro',uri=True) as read:
        with sqlite3.connect(destination) as write:read.backup(write)


def copy_to_new_schema(pg_engine,source_engine,metadata,schema):
    """Transactional DDL/data, preserving IDs and resetting serial sequences."""
    schema_name(schema);counts={}
    with pg_engine.begin() as target:
        exists=target.scalar(text('SELECT EXISTS (SELECT 1 FROM pg_namespace WHERE nspname=:schema)'),{'schema':schema})
        if exists:raise SetupError('Schema '+schema+' da ton tai. Dung lai de khong ghi de. Chon --schema ten_moi neu can chuyen lai.')
        target.exec_driver_sql('CREATE SCHEMA "'+schema+'"')
        target.exec_driver_sql('SET LOCAL search_path TO "'+schema+'"')
        metadata.create_all(bind=target)
        source_names=set(inspect(source_engine).get_table_names())
        with source_engine.connect() as source:
            for table in metadata.sorted_tables:
                copied=0
                if table.name in source_names:
                    raw=Table(table.name,MetaData(),autoload_with=source_engine)
                    names=[column.name for column in table.columns if column.name in raw.c]
                    batches=source.execute(select(*(raw.c[name] for name in names))).mappings().partitions(500)
                    for batch in batches:
                        rows=[dict(row) for row in batch]
                        for row in rows:
                            for column in table.columns:
                                value=row.get(column.name)
                                if isinstance(column.type,DateTime) and column.type.timezone and isinstance(value,datetime) and value.tzinfo is None:
                                    row[column.name]=value.replace(tzinfo=timezone.utc)
                        if rows:target.execute(table.insert(),rows);copied+=len(rows)
                actual=target.scalar(select(func.count()).select_from(table))
                if actual!=copied:raise SetupError('So dong khong khop o bang '+table.name)
                counts[table.name]=copied
                for column in table.primary_key.columns:
                    if not isinstance(column.type,Integer):continue
                    sequence=target.scalar(text('SELECT pg_get_serial_sequence(:table,:column)'),
                        {'table':'"'+schema+'"."'+table.name+'"','column':column.name})
                    if sequence:
                        highest=target.scalar(select(func.max(column)))
                        target.execute(text('SELECT setval(CAST(:sequence AS regclass),:value,:used)'),
                            {'sequence':sequence,'value':max(1,highest or 0),'used':bool(highest and highest>0)})
    return counts


def main():
    parser=argparse.ArgumentParser(description='Chuyen SQLite sang PostgreSQL local, khong ghi de du lieu hien co.')
    parser.add_argument('--host',default='localhost',choices=['localhost','127.0.0.1','::1'])
    parser.add_argument('--port',type=int,default=5432)
    parser.add_argument('--database',default='fake_review_db')
    parser.add_argument('--user',default='postgres')
    parser.add_argument('--schema',type=schema_name,default='fake_review_app')
    args=parser.parse_args()
    try:
        connection=socket.create_connection(('127.0.0.1',8001),timeout=1)
    except ConnectionRefusedError:pass
    except TimeoutError:pass
    except OSError:raise SetupError('Khong kiem tra duoc backend. Hay dung backend truoc khi chuyen database.')
    else:
        connection.close()
        raise SetupError('Backend 8001 dang chay. Nhan Ctrl+C o terminal backend, sau do chay lai cong cu nay.')
    print('Dich: '+args.host+':'+str(args.port)+' / '+args.database+' / schema moi '+args.schema)
    print('Nhap mat khau PostgreSQL tren may nay. Ky tu se khong hien thi.')
    password=getpass('Mat khau PostgreSQL: ')
    if not password:raise SetupError('Chua nhap mat khau. Chua thay doi cau hinh.')
    url=database_url(args.host,args.port,args.database,args.user,password,args.schema)
    pg=create_engine(url,connect_args={'connect_timeout':5},hide_parameters=True)
    with pg.connect() as connection:connection.execute(text('SELECT 1'))
    # Load ORM metadata against SQLite, without touching the active app config.
    source_path=ROOT/'fake_review.db'
    previous=os.environ.get('DATABASE_URL')
    os.environ['DATABASE_URL']='sqlite:///'+source_path.as_posix()
    import models,extended_models
    from database import Base
    backup_dir=ROOT.parents[2]/'db_backups';backup_dir.mkdir(parents=True,exist_ok=True)
    stamp=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    backup=backup_dir/('fake_review-before-postgres-'+stamp+'.db')
    sqlite_backup(source_path,backup)
    source=create_engine('sqlite:///'+backup.as_posix())
    counts=copy_to_new_schema(pg,source,Base.metadata,args.schema)
    report={'host':args.host,'port':args.port,'database':args.database,'schema':args.schema,
        'sqlite_backup':str(backup),'tables':counts,'status':'copied'}
    report_path=backup_dir/('postgres-migration-'+stamp+'.json')
    report_path.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    update_env(ROOT/'.env',url)
    if previous is None:os.environ.pop('DATABASE_URL',None)
    else:os.environ['DATABASE_URL']=previous
    source.dispose();pg.dispose()
    print('DA CHUYEN '+str(sum(counts.values()))+' dong / '+str(len(counts))+' bang.')
    print('Da cap nhat .env. Hay dung va mo lai backend de su dung PostgreSQL.')
    print('pgAdmin: fake_review_db > Schemas > '+args.schema+' > Tables (Refresh).')
    print('Bao cao: '+str(report_path))


if __name__=='__main__':
    try:main()
    except SetupError as exc:print('DUNG: '+str(exc));raise SystemExit(1)
    except KeyboardInterrupt:print('\nDa huy.');raise SystemExit(1)
    except Exception as exc:
        print('CHUA HOAN TAT: '+type(exc).__name__+'. Khong in SQL, du lieu hay mat khau ra terminal.')
        print('Neu chua thay dong DA CHUYEN, khong coi ket noi/chuyen du lieu la thanh cong.')
        raise SystemExit(1)
