from app import cli
from app.models.user import UserModel


def configure_cli(monkeypatch, database_session, email):
    monkeypatch.setattr(cli, "SessionLocal", lambda: database_session)
    monkeypatch.setattr(cli.getpass, "getpass", lambda prompt: "StrongPassword123!")
    monkeypatch.setattr(
        "sys.argv",
        [
            "cli",
            "create-admin",
            "--email",
            email,
            "--first-name",
            "Admin",
            "--last-name",
            "User",
            "--phone",
            "123456789",
        ],
    )


def test_cli_creates_first_admin_without_exposing_password(
    monkeypatch, database_session, capsys
):
    configure_cli(monkeypatch, database_session, "new-admin@example.com")
    assert cli.main() == 0
    output = capsys.readouterr()
    assert "StrongPassword123!" not in output.out + output.err
    user = (
        database_session.query(UserModel).filter_by(email="new-admin@example.com").one()
    )
    assert user.role == "ADMIN"


def test_cli_does_not_promote_existing_client(monkeypatch, database_session, capsys):
    configure_cli(monkeypatch, database_session, "jan@example.com")
    assert cli.main() == 1
    assert database_session.get(UserModel, 2).role == "CLIENT"
    assert "already registered" in capsys.readouterr().err
