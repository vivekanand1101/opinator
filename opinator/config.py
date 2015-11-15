import os

basedir = os.path.abspath(os.path.dirname(__file__))

# The number of days for which the sentiment is valid
LIFESPAN = 60

# Mapping of website_name to spider name
WEBSITE_TO_SPIDER = {'amazonIN': 'amazonin'}

SQLALCHEMY_DATABASE_URI = 'mysql+pymysql://root:@localhost/opinator'
SQLALCHEMY_MIGRATE_REPO = os.path.join(basedir, 'db_repository')
