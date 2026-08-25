from app.db.session import normalize_database_url


def test_normalize_render_postgresql_url() -> None:
    assert (
        normalize_database_url(
            "postgresql://user:password@example.com:5432/openea"
        )
        == "postgresql+psycopg://user:password@example.com:5432/openea"
    )


def test_normalize_psycopg_url_is_unchanged() -> None:
    url = "postgresql+psycopg://user:password@example.com:5432/openea"

    assert normalize_database_url(url) == url


def test_normalize_sqlite_url_is_unchanged() -> None:
    url = "sqlite+pysqlite:///test.db"

    assert normalize_database_url(url) == url