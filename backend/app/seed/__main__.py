from app.core.db import SessionLocal, init_db
from app.mocks.seed_personas import seed_personas
from app.seed import seed_parameters, seed_rules

if __name__ == "__main__":
    init_db()
    with SessionLocal() as db:
        changed = seed_parameters(db) + seed_rules(db) + seed_personas(db)
    print(f"Seed finished, rows changed: {changed}")
