# models.py

import sqlalchemy
from sqlalchemy.dialects.postgresql import JSONB

DATABASE_URL = "postgresql://pe_user:strongpassword@localhost:5432/cim_db"

metadata = sqlalchemy.MetaData()

deals = sqlalchemy.Table(
    "deals",
    metadata,
    sqlalchemy.Column("id", sqlalchemy.Integer, primary_key=True),
    sqlalchemy.Column("file_name", sqlalchemy.String),
    sqlalchemy.Column("analysis_data", JSONB),
)

engine = sqlalchemy.create_engine(DATABASE_URL)