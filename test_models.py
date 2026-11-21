from app.db.base import Base
import app.models

print("Kady models loaded successfully!")

for table_name in Base.metadata.tables:
    print(f"Table registered: {table_name}")