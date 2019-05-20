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
