from contextlib import contextmanager
from pathlib import Path
from time import sleep

from invoke import Context, task


class Paths:
    here = Path(__file__).parent
    repo_root = here
    infra = repo_root / "infra"

    @staticmethod
    @contextmanager
    def cd(c: Context, p: Path):
        with c.cd(str(p)):
            yield


@task
def compile_requirements(c, install=False, upgrade=False):
    with Paths.cd(c, Paths.repo_root):
        if upgrade:
            upgrade_flag = "--upgrade "
        else:
            upgrade_flag = ""
        c.run(f"pip-compile {upgrade_flag}-v --strip-extras -o requirements.txt")
        if install:
            c.run("pip install -r requirements.txt")
            c.run("pip install -r requirements.dev.txt")


@task
def setup_local_resources(c: Context):
    with c.cd(Paths.repo_root):
        for file in (Paths.infra / "dynamodb_tables").iterdir():
            c.run(
                f"AWS_REGION=us-west-2 AWS_DEFAULT_REGION=us-west-2 AWS_ACCESS_KEY_ID=unused AWS_SECRET_ACCESS_KEY=unused "
                f"aws dynamodb create-table --cli-input-yaml file://{file} --endpoint-url http://localhost:8000"
            )


@task
def launch_dynamodb_local(c: Context, create_tables=False, clear_data=False):
    """Run local dynamodb, with options to wipe data and create a table with required indices."""
    with c.cd(Paths.repo_root):
        c.run("docker stop dynamodb-local || true", hide="both")
        if clear_data:
            c.run("rm -rf $(pwd)/local/dynamodb")
        c.run(
            "docker run --rm -d --name dynamodb-local -p 8000:8000 -v "
            "$(pwd)/local/dynamodb:/data/ amazon/dynamodb-local -jar DynamoDBLocal.jar -sharedDb -dbPath /data"
        )
        if create_tables:
            sleep(2)
            for file in (Paths.infra / "dynamodb_tables").iterdir():
                c.run(
                    f"AWS_REGION=us-west-2 AWS_DEFAULT_REGION=us-west-2 AWS_ACCESS_KEY_ID=unused AWS_SECRET_ACCESS_KEY=unused "
                    f"aws dynamodb create-table --cli-input-yaml file://{file} --endpoint-url http://localhost:8000"
                )


@task
def halt_dynamodb_local(c: Context):
    """Run local dynamodb, with options to wipe data and create a table with required indices."""
    c.run("docker stop dynamodb-local || true", hide="both")


@task
def run_streamlit(c: Context, local_dynamodb=True):
    cmd = "python -m streamlit run streamlit_app.py"
    with Paths.cd(c, Paths.repo_root):
        if local_dynamodb:
            print("Using local dynamodb endpoint")
            env = {"AWS_ENDPOINT_URL": "http://localhost:8000"}
        else:
            env = None
        c.run(cmd, pty=True, env=env)


@task
def lint(c: Context):
    with Paths.cd(c, Paths.repo_root):
        c.run("ruff . --fix")
        c.run("isort .")
        c.run("black .")
