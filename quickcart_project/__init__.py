import pymysql

pymysql.version_info = (2, 2, 1, "final", 0)
pymysql.install_as_MySQLdb()

from django.db.backends.mysql.base import DatabaseWrapper
from django.db.backends.mysql.features import DatabaseFeatures

# Allow XAMPP MariaDB 10.4 without MariaDB 10.11+ RETURNING syntax
DatabaseWrapper.check_database_version_supported = lambda self: None
DatabaseFeatures.can_return_columns_from_insert = False
DatabaseFeatures.can_return_rows_from_bulk_insert = False
DatabaseFeatures.supports_returning = False
