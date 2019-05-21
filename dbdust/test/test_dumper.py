import pytest

import dbdust.dumper as dumper


@pytest.mark.parametrize(
    "host,port,database,username,password,"
    "authentication_database,authentication_mechanism",
    [
        ("hostname", None, None, None, None, None, None),
        (None, 123, None, None, None, None, None),
        (None, None, "database", None, None, None, None),
        (None, None, None, "username", None, None, None),
        (None, None, None, None, "password", None, None),
        (None, None, None, None, None, True, None),
        (None, None, None, None, None, None, True),
    ]
)
def test_mongo_cli_builder_too_many_params_with_uri(host, port, database, username,
                                                    password, authentication_database,
                                                    authentication_mechanism):
    with pytest.raises(Exception) as excinfo:
        dumper.mongo_cli_builder(None, None, None, None, uri="uri", host=host,
                                 port=port, database=database, username=username,
                                 password=password, authentication_database=authentication_database,
                                 authentication_mechanism=authentication_mechanism)
    assert 'mongo dump : when specifying uri, don\'t set other connection settings' == str(excinfo.value)


@pytest.mark.parametrize(
    "uri,host,port,database,username,password,"
    "authentication_database,authentication_mechanism,collection,result",
    [
        ("uristr", None, None, None, None, None, None, None, "mycol",
         "mongodump --uri uristr --collection mycol --gzip --archive=mydumpfile"),

        ("uristr", None, None, None, None, None, None, None, None,
         "mongodump --uri uristr --gzip --archive=mydumpfile"),

        (None, "myhost", "123", "mydb", "myuser", "mypass", "authdb", "authmec", "mycol",
         "mongodump --host myhost --port 123 --username myuser --password mypass --authenticationDatabase authdb"
         " --authenticationMechanism authmec --db mydb --collection mycol --gzip --archive=mydumpfile"),

        (None, "myhost", None, "mydb", None, None, None, None, "mycol",
         "mongodump --host myhost --db mydb --collection mycol --gzip --archive=mydumpfile"),

        (None, None, None, None, "myuser", "mypass", None, None, None,
         "mongodump --username myuser --password mypass --gzip --archive=mydumpfile"),
    ]
)
def test_mongo_cli_builder_results(uri, host, port, database, username,
                                   password, authentication_database,
                                   authentication_mechanism, collection, result):
    exec_result = dumper.mongo_cli_builder("mongodump", None, None, "mydumpfile", uri=uri, host=host,
                                           port=port, database=database, username=username,
                                           password=password, authentication_database=authentication_database,
                                           authentication_mechanism=authentication_mechanism, collection=collection)
    assert ' '.join(exec_result) == result


def test_mysql_cli_builder_too_many_params():
    with pytest.raises(Exception) as excinfo:
        dumper.mysql_cli_builder(None, None, None, None, database="mydb", all_databases=True)
    assert 'mysql dump : you must not set both database and all_databases' == str(excinfo.value)


@pytest.mark.parametrize(
    "host,port,username,password,database,all_databases,result",
    [
        ("myhost", None, None, None, None, None,
         "mysqldump -h myhost > mydumpfile"),

        ("myhost", "123", None, None, None, None,
         "mysqldump -h myhost -P 123 > mydumpfile"),

        ("myhost", "123", "myuser", "mypass", None, None,
         "mysqldump -h myhost -P 123 -u myuser -pmypass > mydumpfile"),

        (None, None, "myuser", "mypass", "mydb", None,
         "mysqldump -u myuser -pmypass mydb > mydumpfile"),

        (None, None, "myuser", "mypass", None, True,
         "mysqldump -u myuser -pmypass --all-databases > mydumpfile"),
    ]
)
def test_mysql_cli_builder_results(host, port, username, password, database, all_databases, result):
    exec_result = dumper.mysql_cli_builder("mysqldump", "gzip", None, "mydumpfile", host=host,
                                           port=port, database=database, username=username,
                                           password=password, all_databases=all_databases)
    assert ' '.join(exec_result) == result


@pytest.mark.parametrize(
    "host,port,username,password,database,all_databases,result",
    [
        ("myhost", None, None, None, None, None,
         "mysqldump -h myhost | gzip > mydumpfile"),

        ("myhost", "123", None, None, None, None,
         "mysqldump -h myhost -P 123 | gzip > mydumpfile"),

        ("myhost", "123", "myuser", "mypass", None, None,
         "mysqldump -h myhost -P 123 -u myuser -pmypass | gzip > mydumpfile"),

        (None, None, "myuser", "mypass", "mydb", None,
         "mysqldump -u myuser -pmypass mydb | gzip > mydumpfile"),

        (None, None, "myuser", "mypass", None, True,
         "mysqldump -u myuser -pmypass --all-databases | gzip > mydumpfile"),
    ]
)
def test_zipped_mysql_cli_builder_results(host, port, username, password, database, all_databases, result):
    exec_result = dumper.zipped_mysql_cli_builder()("mysqldump", "gzip", None, "mydumpfile", host=host,
                                                    port=port, database=database, username=username,
                                                    password=password, all_databases=all_databases)
    assert ' '.join(exec_result) == result
