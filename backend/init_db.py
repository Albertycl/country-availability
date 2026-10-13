import os

from main_testing_jenny_excel import app
from model import db, a01_probe_list

SEED_FILE = os.path.join(os.path.dirname(__file__), "demo", "seed_demo_data.sql")


def load_seed():
    lines = [l for l in open(SEED_FILE, encoding="utf-8") if not l.lstrip().startswith("--")]
    statements = [s.strip() for s in "".join(lines).split(";\n") if s.strip().rstrip(";")]
    with db.engine.begin() as conn:  # one connection, because the seed uses the session variable @now
        for statement in statements:
            conn.exec_driver_sql(statement.rstrip(";"))


with app.app_context():
    db.create_all()
    print("tables created")
    if os.environ.get("SEED_DEMO") == "1" and a01_probe_list.query.count() == 0:
        load_seed()
        print("demo data loaded")
