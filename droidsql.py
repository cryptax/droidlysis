"""
__author__ = "Axelle Apvrille"
__status__ = "Alpha"
__license__ = "MIT License"
"""

import sqlalchemy
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, Boolean
import droidconfig


Base = declarative_base()


class Sample(Base):
    __tablename__ = 'samples'

    sha256 = Column(String(64), primary_key=True)
    sanitized_basename = Column(String())
    file_nb_classes = Column(Integer())
    file_nb_dir = Column(Integer())
    file_size = Column(Integer())
    file_small = Column(Boolean())
    filetype = Column(Integer())
    file_innerzips = Column(Boolean())
    manifest_properties = Column(String())
    smali_properties = Column(String())
    wide_properties = Column(String())
    arm_properties = Column(String())
    dex_properties = Column(String())
    kits = Column(String())

    def __repr__(self):
        return "<Sample(sha256=%s)>" % self.sha256


class DroidSql:
    def __init__(self, verbose=False):
        self.verbose = verbose  # to get SQL ALCHEMY requests
        self.engine = sqlalchemy.create_engine(droidconfig.SQLALCHEMY, echo=self.verbose)
        Base.metadata.create_all(self.engine)

    
