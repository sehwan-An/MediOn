"""DB 접속 설정: .env 의 DB_* 값으로 접속 주소를 만든다."""

from sqlalchemy.engine import make_url

from app.core.config import Settings


def test_url_from_db_fields_handles_special_characters():
    s = Settings(_env_file=None, db_password="p@ss:w/rd%#1", db_port=3307, db_name="medion")
    url = make_url(s.sqlalchemy_url)
    assert url.password == "p@ss:w/rd%#1"
    assert url.port == 3307
    assert url.database == "medion"
    assert url.query["charset"] == "utf8mb4"


def test_database_url_overrides_db_fields():
    s = Settings(_env_file=None, database_url="mysql+pymysql://u:p@db.example.com:3306/prod", db_host="localhost")
    assert make_url(s.sqlalchemy_url).host == "db.example.com"
