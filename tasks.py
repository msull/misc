from contextlib import contextmanager
from pathlib import Path

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
def compile_requirements(c, install=True, upgrade=False):
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
def setup_local_resources(c: Context, dynamodb=True, buckets=True):
    # assumes user has already run docker-compose up
    with c.cd(Paths.repo_root):
        if dynamodb:
            for file in (Paths.infra / "dynamodb_tables").iterdir():
                c.run(
                    f"AWS_REGION=us-west-2 AWS_DEFAULT_REGION=us-west-2 AWS_ACCESS_KEY_ID=unused AWS_SECRET_ACCESS_KEY=unused "
                    f"aws dynamodb create-table --cli-input-yaml file://{file} --endpoint-url http://localhost:8000"
                )

        if buckets:
            c.run(
                "AWS_REGION=us-west-2 AWS_DEFAULT_REGION=us-west-2 AWS_ACCESS_KEY_ID=minioadmin AWS_SECRET_ACCESS_KEY=minioadmin "
                "aws s3 mb s3://miscprivate --endpoint-url http://localhost:9000"
            )
            c.run(
                "AWS_REGION=us-west-2 AWS_DEFAULT_REGION=us-west-2 AWS_ACCESS_KEY_ID=minioadmin AWS_SECRET_ACCESS_KEY=minioadmin "
                "aws s3 mb s3://miscpublic --endpoint-url http://localhost:9000"
            )


@task
def run_streamlit(c: Context):
    cmd = "python -m streamlit run streamlit_app.py"
    with Paths.cd(c, Paths.repo_root):
        c.run(cmd, pty=True)


@task
def lint(c: Context):
    with Paths.cd(c, Paths.repo_root):
        c.run("ruff . --fix")
        c.run("isort .")
        c.run("black .")
