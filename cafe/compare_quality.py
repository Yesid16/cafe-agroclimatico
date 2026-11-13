"""Compara artefactos de Colab sin entrenar ni repetir consultas."""
import hashlib
import json
from pathlib import Path
import numpy as np
import pandas as pd
from . import config as C
from .risk_model import build_dataset, RoyaRiskModel


def compare_metrics(original, conservative):
    if len(original["resultados"]) != len(conservative["resultados"]):
        raise ValueError("Cantidad de modelos incompatible")
    result=[]
    for a,b in zip(original['resultados'],conservative['resultados']):
        if a['modelo']!=b['modelo']:
            raise ValueError('Modelos distintos u orden incompatible')
        result.append({'modelo':a['modelo'],
            **{key+'_original':a[key] for key in ('accuracy','f1_macro','brier','log_loss')},
            **{key+'_conservador':b[key] for key in ('accuracy','f1_macro','brier','log_loss')},
            **{'delta_'+key:round(b[key]-a[key],4) for key in ('accuracy','f1_macro','brier','log_loss')}})
    return result


def main():
    root=C.ROOT
    def read(path):
        return json.loads((root/path).read_text(encoding='utf-8'))
    a=read('results/metricas_modelo.json')
    b=read('results/revision_calidad/metricas_modelo.json')
    qa=read('results/revision_diaria/auditoria_diaria.json')
    original=read('results/auditoria_datos.json')
    if not all(hashlib.sha256((root / k.replace(chr(92), "/")).read_bytes()).hexdigest()==v for k,v in original['artefactos_sha256'].items()):
        raise ValueError('La instantánea original ya no coincide con la auditoría')
    candidate_path=root/'data/review/processed/semanal.csv'
    if hashlib.sha256(candidate_path.read_bytes()).hexdigest()!=qa['variante']['sha256']:
        raise ValueError('La candidata no coincide con la revisión diaria')
    w=pd.read_csv(root/'data/processed/semanal.csv',parse_dates=['semana'])
    v=pd.read_csv(candidate_path,parse_dates=['semana'])
    if a['cutoff']!=b['cutoff']:
        raise ValueError('Los cortes temporales son distintos')
    cutoff=pd.Timestamp(a['cutoff'])
    ds_a=build_dataset(w,a['terciles_train_mm'])
    ds_b=build_dataset(v,b['terciles_train_mm'])
    test_a=ds_a[ds_a.semana.gt(cutoff)]
    test_b=ds_b[ds_b.semana.gt(cutoff)]
    paired=test_a.merge(test_b,on=['municipio','semana'],suffixes=('_original','_variante'),
                       how='outer',indicator=True,validate='one_to_one')
    if not paired['_merge'].eq('both').all():
        raise ValueError('Los test no contienen las mismas claves; no describirlos como pareados')
    changes=paired.Riesgo_original.ne(paired.Riesgo_variante)
    artifacts=[root/'data/processed/semanal.csv',root/'data/processed/modelo_roya.pkl',
               candidate_path,root/'data/review/processed/modelo_roya.pkl']
    for directory,table in [(root/'data/processed',w),(root/'data/review/processed',v)]:
        model=RoyaRiskModel.load(directory/'modelo_roya.pkl')
        if not np.allclose(model.q,np.quantile(table.lluvia_mm,[1/3,2/3])):
            raise ValueError('Modelo no coherente con la tabla semanal')
        if not all(np.allclose(f.values.sum(axis=-1),1) for f in model.bn.cpt.values()):
            raise ValueError('CPT no normalizadas')
    result={'estado':'Dos experimentos de Colab presentes y coherentes; no se entrena en esta comparación',
        'cutoff':a['cutoff'],'n_train_original':a['n_train'],'n_train_conservador':b['n_train'],
        'n_test_comunes':len(paired),'etiquetas_test_modificadas':int(changes.sum()),
        'decision_demo':'Mantener original como referencia reproducible con advertencias; conservar sensibilidad separada. Los filtros no son validación certificada.',
        'limitacion_comparacion':'Mismas claves de test, pero cambian dos etiquetas y evidencias; no es comparación estricta sobre un objetivo fijo ni prueba de significancia.',
        'metricas':compare_metrics(a,b),
        'sha256':{p.relative_to(root).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in artifacts}}
    out=root/'results/revision_calidad'
    out.mkdir(exist_ok=True)
    paired.loc[changes,['municipio','semana','Riesgo_original','Riesgo_variante']].to_csv(out/'etiquetas_modificadas.csv',index=False)
    (out/'comparacion_calidad.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    md=['Comparación de sensibilidad (experimentos ejecutados en Colab).','',
        f"Corte {a['cutoff']}; entrenamiento {a['n_train']} original / {b['n_train']} conservador; {len(paired)} claves de prueba comunes.",
        f"Cambian {int(changes.sum())} etiquetas del indicador: no es una prueba sobre un objetivo totalmente fijo.",'',
        '| Modelo | F1 original | F1 conservador | Delta F1 | Brier original | Brier conservador |',
        '|---|---|---|---|---|---|']
    md += [f"| {r['modelo']} | {r['f1_macro_original']:.4f} | {r['f1_macro_conservador']:.4f} | {r['delta_f1_macro']:+.4f} | {r['brier_original']:.4f} | {r['brier_conservador']:.4f} |" for r in result['metricas']]
    md += ['',result['decision_demo'],result['limitacion_comparacion']]
    (out/'comparacion_calidad.md').write_text('\n'.join(md),encoding='utf-8')
    print('\n'.join(md))


if __name__=='__main__':
    main()
