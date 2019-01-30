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

