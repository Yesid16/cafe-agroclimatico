"""Entrega local autocontenida: código, evidencia y artefactos pequeños; sin secretos."""
from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED

ROOT=Path(__file__).resolve().parents[1]
TOP={'cafe','corpus','docs','eval','tests','notebooks','scripts','assets','Docs_Entregables'}
ROOTFILES={'README.md','INFORME.md','requirements.txt','requirements-cloud.txt','pytest.ini',
           'app.py','run_all.sh','.env.example','.gitignore','.streamlit/config.toml'}
DATA={'data/processed/clima_semanal.csv','data/processed/semanal.csv','data/processed/modelo_roya.pkl','data/review/processed/semanal.csv','data/review/processed/modelo_roya.pkl'}


def main():
    output=ROOT/'artifacts/cafe_entrega.zip'
    output.parent.mkdir(exist_ok=True)
    count=0
    with ZipFile(output,'w',ZIP_DEFLATED) as z:
        for p in ROOT.rglob('*'):
            if not p.is_file():
                continue
            rel=p.relative_to(ROOT)
            parts=rel.parts
            name=rel.as_posix()
            if any(x in parts for x in ('.git','.venv','__pycache__','.pytest_cache')):
                continue
            allowed=(parts[0] in TOP or name in ROOTFILES or name in DATA
                     or (parts[0]=='results' and len(parts)==2 and p.suffix in {'.json','.md','.csv','.txt'})
                     or (parts[:2]==('data','raw') and p.suffix=='.json')
                     or (parts[:2] in {('results','revision_diaria'),('results','revision_calidad')} and p.suffix in {'.json','.csv','.md'})
                     or name=='Docs_Entregables/INFORME.pdf')
            if not allowed or p.name=='.env' or p.suffix in {'.zip','.pyc'}:
                continue
            z.write(p,name)
            count+=1
    with ZipFile(output) as z:
        assert z.testzip() is None
        assert 'data/processed/semanal.csv' in z.namelist()
        assert 'Docs_Entregables/INFORME.pdf' in z.namelist()
        assert not any(p=='.env' or p.endswith('/.env') for p in z.namelist())
    print(output, count, 'archivos', round(output.stat().st_size/1024/1024,1),'MiB')


if __name__=='__main__':
    main()
