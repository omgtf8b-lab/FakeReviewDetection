import sqlite3
import pytest
from dotenv import dotenv_values
from sqlalchemy.engine import make_url
from sqlalchemy.schema import CreateTable
from sqlalchemy.dialects import postgresql
from setup_postgres import database_url,update_env,sqlite_backup,schema_name,SetupError


def test_password_special_characters_survive_env_and_sqlalchemy(tmp_path):
    password="fixture@:#/%$ {x}'\\\"việt"
    url=database_url('localhost',5432,'fake_review_db','postgres',password,'fake_review_app')
    path=tmp_path/'.env'
    path.write_text('SECRET_KEY=fixture-secret\nDATABASE_URL=sqlite:///old.db\nAPP_ENV=development\n',encoding='utf-8')
    update_env(path,url)
    values=dotenv_values(path)
    assert values['SECRET_KEY']=='fixture-secret' and values['APP_ENV']=='development'
    parsed=make_url(values['DATABASE_URL'])
    assert parsed.password==password
    assert parsed.database=='fake_review_db'
    assert parsed.query['options']=='-csearch_path=fake_review_app'
    assert len(list(tmp_path.glob('.env.before-postgres.*')))==1


def test_source_backup_is_consistent_and_does_not_modify_source(tmp_path):
    source=tmp_path/'source.db';target=tmp_path/'backup.db'
    with sqlite3.connect(source) as db:
        db.execute('create table sample (id integer primary key, content text)')
        db.execute('insert into sample values (1,?)',('Dữ liệu review',))
    sqlite_backup(source,target)
    with sqlite3.connect(source) as db:assert db.execute('select count(*) from sample').fetchone()[0]==1
    with sqlite3.connect(target) as db:assert db.execute('select content from sample').fetchone()[0]=='Dữ liệu review'


@pytest.mark.parametrize('value',['public','pg_catalog','information_schema','x;drop schema public','x"','../x',''])
def test_schema_cannot_target_system_or_inject_sql(value):
    with pytest.raises(SetupError):schema_name(value)


def test_application_schema_compiles_for_postgresql():
    import models,extended_models
    from database import Base
    statements=[str(CreateTable(table).compile(dialect=postgresql.dialect())) for table in Base.metadata.sorted_tables]
    assert any('collected_reviews' in s for s in statements)
    assert any('collection_snapshots' in s for s in statements)
