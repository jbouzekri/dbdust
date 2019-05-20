import argparse
import datetime

import pytest
from unittest.mock import Mock

import dbdust.admin as admin
import dbdust.dumper as dumper


def test_validate_config_file_unkonwn_file(tmpdir):
    tmp_file = tmpdir.mkdir("dbdust").join("file.cfg")
    with pytest.raises(argparse.ArgumentTypeError) as excinfo:
        admin.validate_config_file(str(tmp_file))
    assert 'Invalid config file {}'.format(str(tmp_file)) in str(excinfo.value)


def test_validate_config_file_valid_file(tmpdir):
    tmp_file = tmpdir.mkdir("dbdust").join("file.cfg")
    tmp_file.write('')
    result = admin.validate_config_file(str(tmp_file))
    assert str(tmp_file) == result


def test_create_cmd_line_parser_unknown_file(capsys):
    parser = admin.create_cmd_line_parser()
    with pytest.raises(SystemExit):
        parser.parse_args(['-c', 'unknown_file.cfg'])
    out, err = capsys.readouterr()
    assert 'argument -c/--config: Invalid config file unknown_file.cfg' in err


def test_create_cmd_line_parser_with_config_file(tmpdir):
    tmp_config_file = tmpdir.mkdir("dbdust").join("config.cfg")
    tmp_config_file.write("")

    parser = admin.create_cmd_line_parser()
    args = parser.parse_args(['-c', '{}'.format(tmp_config_file)])

    assert args.config_file == str(tmp_config_file)


def test_dbdustconfig_get_default_from_env_no_env(monkeypatch):
    dbdust_conf = admin.DbDustConfig()
    assert dbdust_conf._get_default_from_env() == {}


def test_dbdustconfig_get_default_from_env_with_env(monkeypatch):
    monkeypatch.setenv('RANDOM_ENV', 'value1')
    monkeypatch.setenv('DBDUST___GENERAL__MY_VAR1', 'value1')
    monkeypatch.setenv('DBDUST___GENERAL__MY_VAR2', 'value2')
    monkeypatch.setenv('DBDUST___GENERAL__MY_VAR3', 'value3')
    monkeypatch.setenv('DBDUST___SOURCE__OTHER_VAR1', 'test1')
    monkeypatch.setenv('DBDUST___SOURCE__OTHER_VAR2', 'test2')
    dbdust_conf = admin.DbDustConfig()

    assert dbdust_conf._get_default_from_env() == {'general': {'my_var1': 'value1',
                                                               'my_var2': 'value2',
                                                               'my_var3': 'value3'},
                                                   'source': {'other_var1': 'test1',
                                                              'other_var2': 'test2'}}


def test_dbdustconfig_from_file_no_env(tmpdir):
    tmp_config_file = tmpdir.mkdir("dbdust").join("config.cfg")
    tmp_config_file.write("""[general]
    my_var1=value1
    my_var2=value2
    my_var3=value3

    [source]
    other_var1=test1
    other_var2=test2
    """)

    dbdust_conf = admin.DbDustConfig(str(tmp_config_file))
    assert dbdust_conf.to_dict() == {'general': {'my_var1': 'value1',
                                                 'my_var2': 'value2',
                                                 'my_var3': 'value3'},
                                     'source': {'other_var1': 'test1',
                                                'other_var2': 'test2'}}


def test_dbdustconfig_from_file_overwrite_env(monkeypatch, tmpdir):
    monkeypatch.setenv('DBDUST___GENERAL__EXISTING_VAR', 'value')
    monkeypatch.setenv('DBDUST___GENERAL__MY_VAR2', 'overwrite2')

    tmp_config_file = tmpdir.mkdir("dbdust").join("config.cfg")
    tmp_config_file.write("""[general]
    my_var1=value1
    my_var2=value2
    my_var3=value3

    [source]
    other_var1=test1
    other_var2=test2
    """)

    dbdust_conf = admin.DbDustConfig(str(tmp_config_file))
    assert dbdust_conf.to_dict() == {'general': {'existing_var': 'value',
                                                 'my_var1': 'value1',
                                                 'my_var2': 'value2',
                                                 'my_var3': 'value3'},
                                     'source': {'other_var1': 'test1',
                                                'other_var2': 'test2'}}


@pytest.fixture
def dbdust_config_tester(tmpdir):
    tmp_config_file = tmpdir.mkdir("dbdust").join("config.cfg")
    tmp_config_file.write("""[dbdust_tester.sh]
        host=value1
        port=value2

        [dbdust_tester_unknown.sh]
        host=value1
        port=value2

        [local]
        path = value3
        remote = no
        """)
    return admin.DbDustConfig(str(tmp_config_file))


@pytest.fixture
def dbdust_config_full_tester(tmpdir):
    tmp_store_dir = tmpdir.mkdir("dbdust")
    tmp_config_file = tmp_store_dir.join("config.cfg")
    tmp_config_file.write("""[general]
        file_prefix=dump-
        date_format=%%Y%%m
        daily=5
        weekly=6
        monthly=7
        max=8

        [dbdust_tester.sh]
        host=value1
        port=value2

        [local]
        path = {}
        remote = no
        """.format(str(tmp_store_dir)))
    return admin.DbDustConfig(str(tmp_config_file))


def test_get_dump_config(dbdust_config_tester):
    result = admin.get_dump_config('dbdust_tester.sh', dbdust_config_tester)
    assert result.type == 'dbdust_tester.sh'
    assert result.bin_path.endswith('dbdust_tester.sh')
    assert result.file_ext == 'txt'
    assert result.cli_func is dumper.dumper_config.get('dbdust_tester.sh').get('cli_builder')
    assert result.cli_conf == {'host': 'value1', 'port': 'value2'}
    assert result.zip_path is None


def test_get_dump_config_unknown_dumper(monkeypatch, dbdust_config_tester):
    monkeypatch.setattr(dumper, 'dumper_config', {'dbdust_tester_unknown.sh': {'bin_name': 'dbdust_tester_unknown.sh',
                                                                               'file_ext': 'txt',
                                                                               'zip_name': None,
                                                                               'cli_builder': lambda x: x}})
    with pytest.raises(Exception) as excinfo:
        admin.get_dump_config('dbdust_tester_unknown.sh', dbdust_config_tester)
    assert 'dbdust_tester_unknown.sh not found on the system' == str(excinfo.value)


def test_get_dump_config_unknown_zip(monkeypatch, dbdust_config_tester):
    monkeypatch.setattr(dumper, 'dumper_config', {'dbdust_tester.sh': {'bin_name': 'dbdust_tester.sh',
                                                                       'file_ext': 'txt',
                                                                       'zip_name': 'unknown_zip',
                                                                       'cli_builder': lambda x: x}})
    with pytest.raises(Exception) as excinfo:
        admin.get_dump_config('dbdust_tester.sh', dbdust_config_tester)
    assert 'unknown_zip not found on the system' == str(excinfo.value)


def test_get_storage_config_fallback(dbdust_config_tester):
    result = admin.get_storage_config('local', dbdust_config_tester)
    assert result.type == 'local'
    assert result.file_prefix == 'backup-'
    assert result.date_format == '%Y%m%d%H%M%S'
    assert result.retain_conf == {'daily_retain': 7, 'weekly_retain': 4, 'monthly_retain': 2, 'max_per_day': 1}
    assert result.impl_conf == {'path': 'value3', 'remote': 'no'}


def test_get_storage_config_custom(dbdust_config_full_tester):
    result = admin.get_storage_config('local', dbdust_config_full_tester)
    assert result.type == 'local'
    assert result.file_prefix == 'dump-'
    assert result.date_format == '%Y%m'
    assert result.retain_conf == {'daily_retain': 5, 'max_per_day': 8, 'monthly_retain': 7, 'weekly_retain': 6}
    assert result.impl_conf['remote'] == 'no'
    assert result.impl_conf['path'].endswith('/dbdust')


def test_dbdusthandler_process(dbdust_config_full_tester, tmpdir, monkeypatch):
    dbdust_tmp_dir = str(tmpdir.mkdir('dbdust-tmp'))
    now = datetime.datetime.utcnow()
    dump_conf = admin.get_dump_config('dbdust_tester.sh', dbdust_config_full_tester)
    storage_conf = admin.get_storage_config('local', dbdust_config_full_tester)
    handler = admin.DbDustBackupHandler(admin.logger, dump_conf, storage_conf)
    handler._dump = Mock()
    handler._save = Mock()

    handler.process(dbdust_tmp_dir)

    assert handler._dump.call_count == 1
    dump_call_args = handler._dump.call_args
    assert dump_call_args[0][0] == dbdust_tmp_dir
    assert dump_call_args[0][1].endswith('dump-{}.txt'.format(now.strftime('%Y%m')))
    assert handler._save.call_count == 1
    save_call_args = handler._save.call_args
    assert save_call_args[0][0].endswith('dump-{}.txt'.format(now.strftime('%Y%m')))


def test_dbdusthandler_save(dbdust_config_full_tester):
    dump_conf = admin.get_dump_config('dbdust_tester.sh', dbdust_config_full_tester)
    storage_conf = admin.get_storage_config('local', dbdust_config_full_tester)
    handler = admin.DbDustBackupHandler(admin.logger, dump_conf, storage_conf)
    handler.storage_handler = Mock()

    handler._save('tmpfile')

    handler.storage_handler.save.assert_called_once_with('tmpfile')
    handler.storage_handler.rotate.assert_called_once_with()
