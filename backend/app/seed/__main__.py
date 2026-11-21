from app.core.db import SessionLocal, init_db
from app.seed import seed_parameters

if __name__ == "__main__":
    init_db()
    with SessionLocal() as db:
        changed = seed_parameters(db)
    print(f"Seed finished, rows changed: {changed}")
