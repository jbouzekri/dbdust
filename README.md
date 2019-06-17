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

```
sudo pip install dbdust
```

It should install `dbdust` globally and provide the `dbdust` executable in your PATH.

## Usage
