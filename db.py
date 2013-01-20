from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String
from settings import DB_URL
engine = create_engine(DB_URL, convert_unicode=True, encoding='UTF-8')

db_session = scoped_session(sessionmaker(autocommit=False,
                                         autoflush=False,
                                         bind=engine))
Base = declarative_base()
Base.query = db_session.query_property()

class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    foursquare_id = Column(String(50), unique=True)
    name = Column(String(100))
    access_token = Column(String(120), unique=True)

    def __init__(self, foursquare_id=None, access_token=None, name=None):
        self.foursquare_id = foursquare_id
        self.access_token = access_token
        self.name = name

    def __repr__(self):
        return '<User %r>' % (self.foursquare_id)



### make model here:

def init_db():
    # import all modules here that might define models so that
    # they will be registered properly on the metadata.  Otherwise
    # you will have to import them first before calling init_db()
    #import yourapplication.models
    Base.metadata.create_all(bind=engine)
