from app import db


def drop_users_table():
    db.session.execute("DROP TABLE users CASCADE")


if __name__ == "__main__":
    drop_users_table()
