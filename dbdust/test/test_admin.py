import pytest

import dbdust.admin as admin


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
