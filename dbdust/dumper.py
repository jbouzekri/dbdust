def mongo_cli_builder(bin_path, dump_path, uri=None, password=None):
    pass


def dbdust_tester_cli_builder(bin_path, dump_path, loop='default', sleep=0, exit_code=0):
    return [bin_path, dump_path, loop, sleep, exit_code]


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

