import json
from datetime import date
from pathlib import Path

from typer.testing import CliRunner

from papito_core.cli import app, paths


def test_blog_command_saves_file(cli_paths):
    runner = CliRunner()
    result = runner.invoke(
        app,
        ["blog", "--title", "Daily Glow", "--gratitude-theme", "Joy", "--save"],
    )
    assert result.exit_code == 0
    files = list(cli_paths.blogs.glob("*.md"))
    assert files, "Blog command should create a markdown file."


def test_analytics_command(cli_paths, tmp_path):
    data = {
        "snapshots": [
            {
                "platform": "Spotify",
                "streams": 1000,
                "listeners": 400,
                "saves": 120,
                "timestamp": "2025-10-20T12:00:00Z",
            },
            {
                "platform": "Apple Music",
                "streams": 600,
                "listeners": 250,
                "saves": 70,
                "timestamp": "2025-10-21T12:00:00Z",
            },
        ]
    }
    analytics_path = tmp_path / "analytics.json"
    analytics_path.write_text(json.dumps(data), encoding="utf-8")

    runner = CliRunner()
    result = runner.invoke(app, ["analytics", str(analytics_path)])

    assert result.exit_code == 0
    assert "Total streams" in result.stdout
    assert "spotify" in result.stdout.lower()


def test_analytics_command_csv_sample(cli_paths):
    data_path = Path(__file__).resolve().parents[1] / "data" / "analytics" / "2025-10-22_streaming_snapshot.csv"
    runner = CliRunner()
    result = runner.invoke(app, ["analytics", str(data_path)])
    assert result.exit_code == 0
    assert "Total streams" in result.stdout


def test_schedule_command(cli_paths, sample_release_plan):
    runner = CliRunner()
    result = runner.invoke(
        app,
        [
            "schedule",
            str(sample_release_plan),
            "--start-date",
            date(2025, 11, 25).isoformat(),
            "--drip-interval-days",
            "1",
        ],
    )
    assert result.exit_code == 0
    assert "Test Vibes Schedule" in result.stdout


def test_song_command_with_audio_missing_key(cli_paths):
    runner = CliRunner()
    result = runner.invoke(app, ["song", "--audio"])
    assert result.exit_code == 0
    assert "SUNO_API_KEY" in result.stdout


def test_analytics_command_save(cli_paths, tmp_path):
    data = {
        "snapshots": [
            {
                "platform": "Spotify",
                "streams": 100,
                "listeners": 40,
                "saves": 10,
                "timestamp": "2025-10-20T12:00:00Z",
            }
        ]
    }
    analytics_path = tmp_path / "analytics.json"
    analytics_path.write_text(json.dumps(data), encoding="utf-8")

    runner = CliRunner()
    result = runner.invoke(app, ["analytics", str(analytics_path), "--save"])
    assert result.exit_code == 0
    saved_files = list(cli_paths.analytics_reports.glob("*.json"))
    assert saved_files
    log_path = cli_paths.analytics_reports / "log.csv"
    assert log_path.exists()


def test_schedule_command_save(cli_paths, sample_release_plan):
    runner = CliRunner()
    result = runner.invoke(
        app,
        [
            "schedule",
            str(sample_release_plan),
            "--start-date",
            date(2025, 11, 25).isoformat(),
            "--drip-interval-days",
            "1",
            "--save",
        ],
    )
    assert result.exit_code == 0
    saved_files = list(cli_paths.schedule_reports.glob("*.json"))
    assert saved_files


def test_release_package_command(cli_paths, sample_release_plan, tmp_path):
    output_path = tmp_path / "package.json"
    runner = CliRunner()
    result = runner.invoke(
        app,
        [
            "release-package",
            "--plan-path",
            str(sample_release_plan),
            "--output",
            str(output_path),
        ],
    )
    assert result.exit_code == 0
    assert output_path.exists()


def test_fan_add_and_list(cli_paths):
    runner = CliRunner()
    result_add = runner.invoke(
        app,
        [
            "fan",
            "add",
            "--name",
            "Test Fan",
            "--location",
            "Nairobi",
            "--support-level",
            "core",
            "--favorite-track",
            "We Rise!",
        ],
    )
    assert result_add.exit_code == 0
    result_list = runner.invoke(app, ["fan", "list"])
    assert result_list.exit_code == 0
    assert "Test Fan" in result_list.stdout


def test_merch_add_and_list(cli_paths):
    runner = CliRunner()
    result_add = runner.invoke(
        app,
        [
            "merch",
            "add",
            "--sku",
            "SKU1",
            "--name",
            "Papito Tee",
            "--description",
            "Limited edition tee",
            "--price",
            "25",
        ],
    )
    assert result_add.exit_code == 0
    result_list = runner.invoke(app, ["merch", "list"])
    assert result_list.exit_code == 0
    assert "Papito Tee" in result_list.stdout


def test_doctor_command(cli_paths):
    runner = CliRunner()
    result = runner.invoke(app, ["doctor"])
    assert result.exit_code == 0
    assert "Suno API key" in result.stdout
