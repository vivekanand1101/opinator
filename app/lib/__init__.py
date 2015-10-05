import pkg_resources
import sqlalchemy as sa
from sqlalchemy import create_engine
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm import scoped_session

import app.lib
import app.lib.models

def init(db_url, debug=False, create=False):
    """ Create the tables in the database using the information from the
    url obtained.
    :arg db_url, URL used to connect to the database. The URL contains
        information with regards to the database engine, the host to
        connect to, the user and password and the database name.
          ie: <engine>://<user>:<password>@<host>/<dbname>
    :kwarg alembic_ini, path to the alembic ini file. This is necessary
        to be able to use alembic correctly, but not for the unit-tests.
    :kwarg debug, a boolean specifying whether we should have the verbose
        output of sqlalchemy or not.
    :return a session that can be used to query the database.
    """
    engine = create_engine(db_url, echo=debug)

    if create:
        app.lib.model.BASE.metadata.create_all(engine)

    scopedsession = scoped_session(sessionmaker(bind=engine))
    return scopedsession
