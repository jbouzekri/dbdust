import datetime
import logging
import os
from unittest.mock import Mock

import pytest
from freezegun import freeze_time

from dbdust import storage


@freeze_time("2012-01-14")
def test_storage_handler_build_day_to_keep():
    handler = storage.StorageHandler(None, None, None, 1, 1, 1, None)
    assert handler.days_to_keep == {datetime.date(2012, 1, 1): 0,
                                    datetime.date(2012, 1, 9): 0,
                                    datetime.date(2012, 1, 14): 0}

    handler = storage.StorageHandler(None, None, None, 2, 1, 1, None)
    assert handler.days_to_keep == {datetime.date(2012, 1, 1): 0,
                                    datetime.date(2012, 1, 9): 0,
                                    datetime.date(2012, 1, 13): 0,
                                    datetime.date(2012, 1, 14): 0}

    handler = storage.StorageHandler(None, None, None, 1, 2, 1, None)
    assert handler.days_to_keep == {datetime.date(2012, 1, 1): 0,
                                    datetime.date(2012, 1, 2): 0,
                                    datetime.date(2012, 1, 9): 0,
                                    datetime.date(2012, 1, 14): 0}

    handler = storage.StorageHandler(None, None, None, 1, 1, 2, None)
    assert handler.days_to_keep == {datetime.date(2011, 12, 1): 0,
                                    datetime.date(2012, 1, 1): 0,
                                    datetime.date(2012, 1, 9): 0,
                                    datetime.date(2012, 1, 14): 0}

    handler = storage.StorageHandler(None, None, None, 6, 6, 6, None)
    assert handler.days_to_keep == {datetime.date(2011, 8, 1): 0,
                                    datetime.date(2011, 9, 1): 0,
                                    datetime.date(2011, 10, 1): 0,
                                    datetime.date(2011, 11, 1): 0,
                                    datetime.date(2011, 12, 1): 0,
                                    datetime.date(2011, 12, 5): 0,
                                    datetime.date(2011, 12, 12): 0,
                                    datetime.date(2011, 12, 19): 0,
                                    datetime.date(2011, 12, 26): 0,
                                    datetime.date(2012, 1, 1): 0,
                                    datetime.date(2012, 1, 2): 0,
                                    datetime.date(2012, 1, 9): 0,
                                    datetime.date(2012, 1, 10): 0,
                                    datetime.date(2012, 1, 11): 0,
                                    datetime.date(2012, 1, 12): 0,
                                    datetime.date(2012, 1, 13): 0,
                                    datetime.date(2012, 1, 14): 0}


def test_storage_handler_extract_date_from_file_name_success():
    handler = storage.StorageHandler(None, 'backup_', "%Y%m%d%H%M%S", 1, 1, 1, None)
    result = handler.extract_date_from_file_name('backup_20190506110952.sql')
    assert result == datetime.datetime(2019, 5, 6, 11, 9, 52)


def test_storage_handler_extract_date_from_file_name_error():
    handler = storage.StorageHandler(None, 'backup_', "%Y%m%d%H%M%S", 1, 1, 1, None)
    with pytest.raises(ValueError) as excinfo:
        handler.extract_date_from_file_name('backup_2019.sql')
    assert 'time data \'2019\' does not match format \'%Y%m%d%H%M%S\'' == str(excinfo.value)


def test_storage_handler_get_sorted_backup_files_list():
    mock_storage_impl = Mock()
    mock_storage_impl.list = Mock(return_value=[])

    handler = storage.StorageHandler(mock_storage_impl, 'backup_', "%Y%m%d%H%M%S", 1, 1, 1, None)
    result = handler._get_sorted_backup_files_list()
    assert result == []

    mock_storage_impl.list = Mock(return_value=[{'file_name': 'backup_20190506110952.gz'},
                                                {'file_name': 'backup_20180416095643.sql'},
                                                {'file_name': 'backup_20181223184234.txt'}])
    result = handler._get_sorted_backup_files_list()
    assert result == [{'date': datetime.datetime(2019, 5, 6, 11, 9, 52), 'file_name': 'backup_20190506110952.gz'},
                      {'date': datetime.datetime(2018, 12, 23, 18, 42, 34), 'file_name': 'backup_20181223184234.txt'},
                      {'date': datetime.datetime(2018, 4, 16, 9, 56, 43), 'file_name': 'backup_20180416095643.sql'}]


def test_storage_handler_save():
    mock_storage_impl = Mock()
    handler = storage.StorageHandler(mock_storage_impl, 'backup_', "%Y%m%d%H%M%S", 1, 1, 1, None)
    handler.save('mypath')

    assert mock_storage_impl.store.call_count == 1
    dump_call_args = mock_storage_impl.store.call_args
    assert dump_call_args[0] == ('mypath',)
    assert dump_call_args[1] == {}


@freeze_time("2012-01-14")
def test_storage_handler_rotate(monkeypatch):
    mock_storage_impl = Mock()
    handler = storage.StorageHandler(mock_storage_impl, 'backup_', "%Y%m%d%H%M%S", 1, 1, 1, 1)

    def mockreturn():
        return [{'id': 10, 'date': datetime.datetime(2012, 1, 14, 18, 9, 52)},
                {'id': 20, 'date': datetime.datetime(2012, 1, 14, 11, 42, 34)},
                {'id': 30, 'date': datetime.datetime(2012, 1, 9, 18, 42, 34)},
                {'id': 40, 'date': datetime.datetime(2012, 1, 2, 18, 42, 34)},
                {'id': 50, 'date': datetime.datetime(2012, 1, 1, 18, 42, 34)},
                {'id': 60, 'date': datetime.datetime(2012, 1, 1, 17, 42, 34)}]
    monkeypatch.setattr(handler, '_get_sorted_backup_files_list', mockreturn)

    handler.rotate()

    assert mock_storage_impl.delete.call_count == 3
    assert mock_storage_impl.delete.call_args_list == [((20,),), ((40,),), ((60,),)]


def test_local_storage__init__folder_does_not_exists():
    with pytest.raises(storage.DbDustStorageException) as excinfo:
        storage.LocalStorage(logging.getLogger(), 'dbdust_pathdoesnotexists')
    assert 'local storage : dbdust_pathdoesnotexists folder does not exist' == str(excinfo.value)


def test_local_storage_store(tmpdir):
    local_path = tmpdir.mkdir("dbdust_localpath")
    src_path = tmpdir.mkdir("dbdust_srcpath")
    file_path = src_path.join('myfile.txt')
    file_path.write('content')

    local_storage = storage.LocalStorage(logging.getLogger(), str(local_path))
    local_storage.store(str(file_path))

    assert len(local_path.listdir()) == 1
    assert str(local_path.listdir()[0]).endswith('myfile.txt') is True
    assert len(src_path.listdir()) == 0


def test_local_storage_list(tmpdir):
    local_path = tmpdir.mkdir("dbdust_localpath")

    file_path1 = local_path.join('myfile1.txt')
    file_path1.write('content')
    file_path2 = local_path.join('myfile2.txt')
    file_path2.write('content')

    local_storage = storage.LocalStorage(logging.getLogger(), str(local_path))
    result = local_storage.list()

    assert result == [{'path': os.path.join(str(local_path), 'myfile2.txt'),
                       'file_name': 'myfile2.txt', 'id': 'myfile2.txt'},
                      {'path': os.path.join(str(local_path), 'myfile1.txt'),
                       'file_name': 'myfile1.txt', 'id': 'myfile1.txt'}]


def test_local_storage_delete(tmpdir):
    local_path = tmpdir.mkdir("dbdust_localpath")
    file_path1 = local_path.join('myfile1.txt')
    file_path1.write('content')

    assert len(local_path.listdir()) == 1
    local_storage = storage.LocalStorage(logging.getLogger(), str(local_path))
    local_storage.delete('myfile1.txt')
    assert len(local_path.listdir()) == 0
