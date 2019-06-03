import datetime

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
