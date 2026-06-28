import os
import subprocess
import sys


def test_cli_agent_test_runs():
    env = os.environ.copy()
    existing_pythonpath = env.get("PYTHONPATH")
    env["PYTHONPATH"] = (
        f"src{os.pathsep}{existing_pythonpath}" if existing_pythonpath else "src"
    )

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "gym_trainer.main",
            "agent-test",
            "--message",
            "que toca hoy?",
        ],
        check=True,
        capture_output=True,
        env=env,
        text=True,
    )

    assert "Hoy toca" in result.stdout
    assert "workspace/current_plan.md" in result.stdout
