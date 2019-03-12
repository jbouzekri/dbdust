# -*- coding: utf-8 -*-
#
# (c) 2019 3sLab
#
# This file is part of the dbdust application
#
# MIT License :
# https://raw.githubusercontent.com/3slab/dbdust/master/LICENSE

""" Cli and config for all supported source systems """


def mongo_cli_builder(bin_path, dump_path, uri=None, password=None):
    """ dbust cli for mongodump """
    pass


def dbdust_tester_cli_builder(bin_path, dump_path, loop='default', sleep=0, exit_code=0):
    """ dbust cli tester script included in this package """
    return [bin_path, dump_path, loop, sleep, exit_code]


#: dict off all items mandatory for dbdust main process
dumper_config = {
    "dbdust_tester.sh": {
        "bin_name": "dbdust_tester.sh",
        "file_ext": "txt",
        "cli_builder": dbdust_tester_cli_builder
    },
    "mongo": {
        "bin_name": "mongodump",
        "file_ext": "gz",
        "cli_builder": mongo_cli_builder
    }
}
