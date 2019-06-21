# DBdust

What is it ? It is the swiss knife to backup your database. It is a Python CLI tool that runs the standard dump command for the database in a subprocess and stores the resulting file to a storage.

For now, are supported :

* database source :
  * mysql
  * mongodb

* storage destination :
  * local filesystem
  * azure blob storage

## Installation

```sh
$ sudo pip install dbdust
```

It should install `dbdust` globally and provide the `dbdust` executable in your PATH.

## Usage

```sh
$ dbdust [-c <path to config file>] [-v]
```

When launching this command, it will :

1. load the provided configuration
2. starts a dump
3. stores the dump
4. Rotate dump by removing the old ones

**!!! WARNING !!! The dump is first locally before behind sent to storage. You need to have enough local disk space. The tmp folder is configurable.**

**The "standard" dump tool is used in a python subprocess, so tools mysqldump or the like needs to be available in the PATH of the user running the command**

## Configuration

Configuration can be provided in 2 ways :

* INI file through the `-c` parameter in the command line
* environment variable (it overwrites anything in the config file) : it loads all environment variables which match the pattern : `DBDUST___<SECTION_NAME>__<VARIABLE_NAME>`

| INI section | INI variable | ENV variable | Required | Type | Default | Usage |
| --- | --- | --- | --- | --- | --- | --- |
| `general` | `database` | `DBDUST___GENERAL__DATABASE` | Yes | string | | Set the source database to dump |
| `general` | `storage` | `DBDUST___GENERAL__STORAGE` | Yes | string | | Set the storage to store dumps |
| `general` | `daily` | `DBDUST___GENERAL__DAILY` | False | integer | `7` | Set the number of days we keep storage |
| `general` | `weekly` | `DBDUST___GENERAL__WEEKLY` | False | integer | `4` | Set if we keep the dump done on the first day in the last X weeks |
| `general` | `monthly` | `DBDUST___GENERAL__MONTHLY` | False | integer | `2` | Set if we keep the dump done on the first day in the last X months |
| `general` | `max` | `DBDUST___GENERAL__MAX` | False | integer | `1` | Set the max number of dump to keep in any single day |
| `general` | `file_prefix` | `DBDUST___GENERAL__FILE_PREFIX` | False | string | `backup-` | Set filename prefix of the dump |
| `general` | `date_format` | `DBDUST___GENERAL__DATE_FORMAT` | False | string | `%Y%m%d%H%M%S` | timestamp format as a suffix of the dump filename (needs to be in [strftime format](https://docs.python.org/3/library/datetime.html#strftime-strptime-behavior)) |

Whatever solution is used, for the value of `general/database` and `general/storage`, you will have an additional section to configure the source and the destination storage.

### Source

#### mysql, mysql_gz, mysql_bz2

These 3 sources share the same settings. They can be use for any mysql compatible database (mariadb, percona, mysql) and needs the `mysqldump` executable available in the `PATH` of the user running the dbdust command.

* `mysql` : dump in txt format
* `mysql_gz` : dump and compress in gzip format
* `mysql_bz2` : dump and compress in bzip2 format

In the following table, the INI section and env variable use `mysql`. Change it to `mysql_gz` or `mysql_bz2` according to the configuration in the `general/database` variable.

| INI section | INI variable | ENV variable | Required | Type | Default | Usage |
| --- | --- | --- | --- | --- | --- | --- |
| `mysql` | `host` | `DBDUST___MYSQL__HOST` | False | string | | Set the hostname of the mysql server |
| `mysql` | `port` | `DBDUST___MYSQL__PORT` | False | integer | | Set the port number of the mysql server |
| `mysql` | `username` | `DBDUST___MYSQL__USERNAME` | False | string | | Set the username to connect to the mysql server |
| `mysql` | `password` | `DBDUST___MYSQL__PASSWORD` | False | string | | Set the password to connect to the mysql server |
| `mysql` | `database` | `DBDUST___MYSQL__DATABASE` | False | string | | Set the database name to dump (exclusive with `all_databases`) |
| `mysql` | `all_databases` | `DBDUST___MYSQL__ALL_DATABASES` | False | boolean | | Dump all databases (exclusive with `database`) |

#### mongo

It needs the `mongodump` executable available in the `PATH` of the user running the command

| INI section | INI variable | ENV variable | Required | Type | Default | Usage |
| --- | --- | --- | --- | --- | --- | --- |
| `mongo` | `uri` | `DBDUST___MONGO__URI` | False | string | | Set the full uri of the mongo server (exclusive with `host`, `port`, `database`, `username`, `password`, `authentication_database` or `authentication_mechanism`) |
| `mongo` | `host` | `DBDUST___MONGO__HOST` | False | string | | Set the hostname of the mongo server (exclusive with `uri`) |
| `mongo` | `port` | `DBDUST___MONGO__PORT` | False | integer | | Set the port of the mongo server (exclusive with `uri`) |
| `mongo` | `database` | `DBDUST___MONGO__DATABASE` | False | string | | Set the database to dump (exclusive with `uri`) |
| `mongo` | `username` | `DBDUST___MONGO__USERNAME` | False | string | | Set the username to connect to the mongo server (exclusive with `uri`) |
| `mongo` | `password` | `DBDUST___MONGO__PASSWORD` | False | string | | Set the password to connect to the mongo server (exclusive with `uri`) |
| `mongo` | `authentication_database` | `DBDUST___MONGO__AUTHENTICATION_DATABASE` | False | string | | Set the `authentication_database` to connect to the mongo server (exclusive with `uri`) |
| `mongo` | `authentication_mechanism` | `DBDUST___MONGO__AUTHENTICATION_MECHANISM` | False | string | | Set the `authentication_mechanism` to connect to the mongo server (exclusive with `uri`) |
| `mongo` | `collection` | `DBDUST___MONGO__COLLECTION` | False | string | | Set the collection to dump |

### Storage

#### local

To be used to move the resulting dump file to a local folder on the same server the command is running *(note : it does not prevent to move the file to another server if the target folder is a mounted network filesystem)*

| INI section | INI variable | ENV variable | Required | Type | Default | Usage |
| --- | --- | --- | --- | --- | --- | --- |
| `local` | `path` | `DBDUST___LOCAL__PATH` | True | string | | Set the directory to move the dumped file to |

#### azure_blob

To be used to move the resulting dump file to an azure blob storage container

| INI section | INI variable | ENV variable | Required | Type | Default | Usage |
| --- | --- | --- | --- | --- | --- | --- |
| `azure_blob` | `account_name` | `DBDUST___AZURE_BLOB__ACCOUNT_NAME` | True | string | | The name of the target blob storage account |
| `azure_blob` | `container` | `DBDUST___AZURE_BLOB__CONTAINER` | True | string | | The name of the target blob storage container |
| `azure_blob` | `account_key` | `DBDUST___AZURE_BLOB__ACCOUNT_KEY` | False | string | | an account key to authenticate with the storage account (exclusive with `sas_token`) |
| `azure_blob` | `sas_token` | `DBDUST___AZURE_BLOB__SAS_TOKEN` | False | string | | a shared access signature to authenticate with the storage account or container (exclusive with `account_key`) |