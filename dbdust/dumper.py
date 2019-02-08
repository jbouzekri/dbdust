def mongo_cli_builder():
    pass


dumper_config = {
    "mongo": {
        "bin_name": "mongodump",
        "file_ext": "gz",
        "cli_builder": mongo_cli_builder
    }
}

