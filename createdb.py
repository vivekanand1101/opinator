import pkg_resources

import config
import app.lib
from app import app

app.lib.init(
    config['SQLALCHEMY_DB_URI'],
    None,
    debug=True,
    create=True)
