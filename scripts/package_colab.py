"""Empaqueta el código actual sin secretos para ejecutarlo en Colab."""
from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED

ROOT = Path(__file__).resolve().parents[1]
ALLOWED = {'cafe', 'corpus', 'docs', 'eval', 'tests', 'notebooks', 'scripts', 'assets'}
FILES = {'README.md', 'requirements.txt', 'requirements-cloud.txt', 'app.py', '.env.example', 'pytest.ini', 'run_all.sh', 'INFORME.md', '.streamlit/config.toml'}


def main():
    out = ROOT / 'artifacts'
    out.mkdir(exist_ok=True)
    path = out / 'cafe_colab_source.zip'
    with ZipFile(path, 'w', ZIP_DEFLATED) as z:
        for p in ROOT.rglob('*'):
            rel = p.relative_to(ROOT)
            if not p.is_file() or any(x in rel.parts for x in ('.git', '.venv', '__pycache__', '.pytest_cache')):
                continue
            if rel.parts[0] not in ALLOWED and str(rel).replace('\\', '/') not in FILES:
                continue
            if p.name == '.env' or p.suffix in {'.pyc', '.zip'}:
                continue
            z.write(p, rel.as_posix())
    print(path)


if __name__ == '__main__':
    main()
