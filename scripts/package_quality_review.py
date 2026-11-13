"""Paquete pequeño para medir en Colab la variante ya auditada."""
from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED
ROOT=Path(__file__).resolve().parents[1]


def main():
    out=ROOT/'artifacts/cafe_revision_calidad.zip'
    out.parent.mkdir(exist_ok=True)
    with ZipFile(out,'w',ZIP_DEFLATED) as z:
        for p in (ROOT/'cafe').glob('*.py'):
            z.write(p,p.relative_to(ROOT).as_posix())
        for name in ['data/review/processed/semanal.csv','scripts/colab_run.py',
                     'docs/REVISION_DATOS_DIARIOS.md']:
            z.write(ROOT/name,name)
        for p in (ROOT/'results/revision_diaria').glob('*'):
            if p.is_file():
                z.write(p,p.relative_to(ROOT).as_posix())
    with ZipFile(out) as z:
        assert z.testzip() is None
        assert 'cafe/review_experiment.py' in z.namelist()
        assert 'data/review/processed/semanal.csv' in z.namelist()
        assert not any(p=='.env' or p.endswith('/.env') for p in z.namelist())
    print(out,round(out.stat().st_size/1024),'KiB')


if __name__=='__main__':
    main()
