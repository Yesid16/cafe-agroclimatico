"""Experimento de sensibilidad SOLO en Colab, con resultados separados de la demo."""
from contextlib import contextmanager
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
from zipfile import ZipFile, ZIP_DEFLATED

ROOT=Path(__file__).resolve().parents[1]


@contextmanager
def experiment_environment(root):
    values={'CAFE_DATA_PROC':str(root/'data/review/processed'),
            'CAFE_RESULTS_DIR':str(root/'results/revision_calidad')}
    previous={key:os.environ.get(key) for key in values}
    os.environ.update(values)
    try:
        yield
    finally:
        for key,value in previous.items():
            if value is None:
                os.environ.pop(key,None)
            else:
                os.environ[key]=value


def main():
    if not (Path('/content').is_dir() and sys.platform.startswith('linux')):
        raise SystemExit('Ejecute este experimento en Colab; no se permite entrenar con este comando en el PC.')
    report=json.loads((ROOT/'results/revision_diaria/auditoria_diaria.json').read_text(encoding='utf-8'))
    path=ROOT/'data/review/processed/semanal.csv'
    if hashlib.sha256(path.read_bytes()).hexdigest()!=report['variante']['sha256']:
        raise ValueError('La variante no coincide con la auditoría')
    originals=[ROOT/'data/processed/semanal.csv',ROOT/'data/processed/modelo_roya.pkl',
               ROOT/'results/metricas_modelo.json']
    before={p:hashlib.sha256(p.read_bytes()).hexdigest() for p in originals if p.exists()}
    with experiment_environment(ROOT):
        subprocess.run([sys.executable,'-u','-m','cafe.risk_model'],cwd=ROOT,check=True)
    assert all(hashlib.sha256(p.read_bytes()).hexdigest()==v for p,v in before.items()), 'Cambió un artefacto original'
    target=ROOT/'artifacts/cafe_resultados_calidad.zip'
    target.parent.mkdir(exist_ok=True)
    with ZipFile(target,'w',ZIP_DEFLATED) as z:
        for folder in ['data/review/processed','results/revision_calidad','results/revision_diaria']:
            for p in (ROOT/folder).rglob('*'):
                if p.is_file():
                    z.write(p,p.relative_to(ROOT).as_posix())
    print('Experimento de sensibilidad finalizado en Colab. Originales intactos.',flush=True)
    print(target,flush=True)


if __name__=='__main__':
    main()
