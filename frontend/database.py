from sqlalchemy import create_engine, Column, String, MetaData, Table
from sqlalchemy.orm import declarative_base, sessionmaker

DATABASE_URL = "sqlite:///./test.db"  # SQLite database URL
engine = create_engine(DATABASE_URL)
metadata = MetaData()

file_info_table = Table(
    "file_info",
    metadata,
    Column("id", String, primary_key=True),
    Column("filename", String),
    Column("hash", String),
)

Base = declarative_base()

class FileInfo(Base):
    __tablename__ = "file_info"
    id = Column(String, primary_key=True)
    filename = Column(String)
    hash = Column(String)

Base.metadata.create_all(bind=engine)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def save_file_info(filename: str, hash_value: str):
    db = SessionLocal()
    db_file_info = FileInfo(id=hash_value, filename=filename, hash=hash_value)
    db.add(db_file_info)
    db.commit()
    db.refresh(db_file_info)
    db.close()

def get_filename_for_hash(hash: str):
    db = SessionLocal()
    db_file_info = db.query(FileInfo).filter(FileInfo.hash == hash).first()
    db.close()
    return db_file_info.filename if db_file_info else None