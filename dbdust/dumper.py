# -*- coding: utf-8 -*-
#
# (c) 2019 3sLab
#
# This file is part of the dbdust application
#
# MIT License :
# https://raw.githubusercontent.com/3slab/dbdust/master/LICENSE

""" Cli and config for all supported source systems """

import functools


class DbDustDumpException(Exception):
    """ Base exception for all dump exception """
    pass


def mongo_cli_builder(bin_path, zip_path, dump_dir_path, dump_file_path, uri=None, password=None):
    """ dbust cli for mongodump """
    pass


def mysql_cli_builder(bin_path, zip_path, dump_dir_path, dump_file_path, host=None, port=None, username=None,
                      password=None, database=None, all_databases=None, zipped=None):
    """ dbust cli for mysqldump """
    if all([database, all_databases]):
        raise DbDustDumpException('mysql dump : you must not set both database and all_databases')
    cmd = [bin_path]
    if host is not None:
        cmd.extend(['-h', host])
    if port is not None:
        cmd.extend(['-P', port])
    if username is not None:
        cmd.extend(['-u', username])
    if password is not None:
        cmd.append('-p{}'.format(password))
    if database is not None:
        cmd.append(database)
    if all_databases is not None:
        cmd.append('--all-databases')
    if zipped:
        cmd.extend(['|', zip_path])
    cmd.extend(['>', dump_file_path])
    return cmd


def zipped_mysql_cli_builder(zipped=None):
    @functools.wraps(mysql_cli_builder)
    def wrapper(*args, **kwargs):
        return mysql_cli_builder(*args, zipped=zipped, **kwargs)
    return wrapper


def dbdust_tester_cli_builder(bin_path, zip_path, dump_dir_path, dump_file_path, loop='default', sleep=0, exit_code=0):
    """ dbust cli tester script included in this package """
    return [bin_path, dump_file_path, loop, sleep, exit_code]


#: dict off all items mandatory for dbdust main process
dumper_config = {
    "dbdust_tester.sh": {
        "bin_name": "dbdust_tester.sh",
        "zip_name": None,
        "file_ext": "txt",
        "cli_builder": dbdust_tester_cli_builder
    },
    "mysql": {
        "bin_name": "mysqldump",
        "zip_name": None,
        "file_ext": "sql",
        "cli_builder": mysql_cli_builder
    },
    "mysql_gz": {
        "bin_name": "mysqldump",
        "zip_name": "gzip",
        "file_ext": "sql.gz",
        "cli_builder": zipped_mysql_cli_builder(zipped=True)
    },
    "mysql_bz2": {
        "bin_name": "mysqldump",
        "zip_name": "bzip2",
        "file_ext": "sql.bz2",
        "cli_builder": zipped_mysql_cli_builder(zipped=True)
    },
    "mongo": {
        "bin_name": "mongodump",
        "zip_name": None,
        "file_ext": "gz",
        "cli_builder": mongo_cli_builder
    }
}
