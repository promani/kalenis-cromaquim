#!/usr/bin/env python3
"""Configuración de ingreso de muestras: año de trabajo + secuencias + tipos de fracción."""
import sys
import datetime
from proteus import config, Model

DB = sys.argv[1] if len(sys.argv) > 1 else 'kalenislims'
cfg = config.set_trytond(DB, config_file='trytond.dev.conf')
print('Conectado a', DB)

Company = Model.get('company.company')
Sequence = Model.get('ir.sequence')
SequenceType = Model.get('ir.sequence.type')
WorkYear = Model.get('lims.lab.workyear')
FractionType = Model.get('lims.fraction.type')
ModelData = Model.get('ir.model.data')

company = Company.find([])[0]

def xmlid(module, fs_id):
    d = ModelData.find([('module', '=', module), ('fs_id', '=', fs_id)])[0]
    return d.db_id

# --- Secuencias (una por tipo, para la compañía) -------------------------
SEQS = [
    ('entry',          'Entradas',              'seq_type_entry'),
    ('sample',         'Muestras',              'seq_type_sample'),
    ('service',        'Servicios',             'seq_type_service'),
    ('results_report', 'Informes de resultados', 'seq_type_results_report'),
]
seqs = {}
for key, name, seqtype_fs in SEQS:
    st = SequenceType(xmlid('lims', seqtype_fs))
    found = Sequence.find([('name', '=', name),
                           ('sequence_type', '=', st.id)])
    if found:
        seqs[key] = found[0]
    else:
        s = Sequence(name=name, sequence_type=SequenceType(st.id))
        try:
            s.company = Company(company.id)
        except Exception:
            pass
        s.save()
        seqs[key] = s
        print('Secuencia creada:', name)

# --- Año de trabajo ------------------------------------------------------
YEAR = 2026
wy = WorkYear.find([('code', '=', str(YEAR))])
if wy:
    wy = wy[0]
    print('Año de trabajo', YEAR, 'ya existe')
else:
    wy = WorkYear(code=str(YEAR))
    wy.start_date = datetime.date(YEAR, 1, 1)
    wy.end_date = datetime.date(YEAR, 12, 31)
    wy.entry_sequence = Sequence(seqs['entry'].id)
    wy.sample_sequence = Sequence(seqs['sample'].id)
    wy.service_sequence = Sequence(seqs['service'].id)
    wy.results_report_sequence = Sequence(seqs['results_report'].id)
    wy.save()
    print('Año de trabajo', YEAR, 'creado con sus 4 secuencias')

# --- Tipos de fracción ---------------------------------------------------
for code, desc in [('MB', 'Microbiología'), ('SA', 'Sin acondicionar')]:
    ft = FractionType.find([('code', '=', code)])
    if not ft:
        ft = FractionType(code=code, description=desc)
        ft.save()
        print('Tipo de fracción creado:', desc)

print('\n== LISTO ==')
print('Secuencias:', len(seqs), '| Año de trabajo:', wy.code,
      '| Tipos de fracción:', len(FractionType.find([])))
