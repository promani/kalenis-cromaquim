#!/usr/bin/env python3
"""Configuración base de Cromaquim: compañía + moneda + laboratorio Microbiología + Sole."""
import sys
from decimal import Decimal
from proteus import config, Model

DB = sys.argv[1] if len(sys.argv) > 1 else 'kalenislims'
cfg = config.set_trytond(DB, config_file='trytond.dev.conf')
print('Conectado a', DB)

Currency = Model.get('currency.currency')
Party = Model.get('party.party')
Company = Model.get('company.company')
User = Model.get('res.user')
Laboratory = Model.get('lims.laboratory')
Professional = Model.get('lims.laboratory.professional')
Department = Model.get('company.department')
Location = Model.get('stock.location')

# 1. Moneda ARS -----------------------------------------------------------
ars = Currency.find([('code', '=', 'ARS')])
if ars:
    ars = ars[0]
    print('Moneda ARS ya existe:', ars.name)
else:
    ars = Currency(name='Peso Argentino', code='ARS', symbol='$',
                   numeric_code='032', rounding=Decimal('0.01'), digits=2)
    ars.save()
    print('Moneda ARS creada')

# 2. Tercero de la compañía ----------------------------------------------
party = Party.find([('name', '=', 'CROMAQUIM SRL')])
if party:
    party = party[0]
    print('Tercero CROMAQUIM SRL ya existe')
else:
    party = Party(name='CROMAQUIM SRL')
    ident = party.identifiers.new()
    try:
        ident.type = 'ar_cuit'
    except Exception as e:
        print('  (tipo ar_cuit no disponible, uso genérico):', e)
        ident.type = None
    ident.code = '30622329006'
    party.save()
    print('Tercero CROMAQUIM SRL creado con CUIT', ident.code, 'tipo=', ident.type)

# 3. Compañía -------------------------------------------------------------
company = Company.find([('party', '=', party.id)])
if company:
    company = company[0]
    print('Compañía ya existe')
else:
    company = Company()
    company.party = party
    company.currency = ars
    company.save()
    print('Compañía CROMAQUIM SRL creada (moneda %s)' % ars.code)

# 4. Asignar compañía a los usuarios -------------------------------------
for login in ['admin', 'sole']:
    us = User.find([('login', '=', login)])
    if not us:
        continue
    u = us[0]
    try:
        existing = [c.id for c in u.companies]
        if company.id not in existing:
            u.companies.append(Company(company.id))
    except AttributeError:
        print('  (res.user sin campo companies)')
    try:
        u.company = Company(company.id)
    except Exception as e:
        print('  no pude fijar company en', login, ':', e)
    u.save()
    print('Usuario', login, '-> compañía', company.party.name)

# 5. Sole como profesional de laboratorio (antes del lab: es requerido) ---
sole_users = User.find([('login', '=', 'sole')])
sole_user = sole_users[0] if sole_users else None

sole_party = Party.find([('name', '=', 'María Soledad Kessel')])
if sole_party:
    sole_party = sole_party[0]
else:
    sole_party = Party(name='María Soledad Kessel')
# el profesional exige party con is_lab_professional=True y usuario Lims vinculado
if not getattr(sole_party, 'is_lab_professional', False):
    sole_party.is_lab_professional = True
    if sole_user is not None:
        sole_party.lims_user = User(sole_user.id)
    sole_party.save()
    print('Tercero de Sole listo (is_lab_professional=True, usuario Lims=sole)')

prof = Professional.find([('party', '=', sole_party.id)])
if prof:
    prof = prof[0]
    print('Profesional de Sole ya existe')
else:
    prof = Professional(party=sole_party, code='MSK')
    try:
        prof.role = 'Responsable de Microbiología'
    except Exception:
        pass
    prof.save()
    print('Profesional de laboratorio creado para Sole (code MSK)')

# 6. Laboratorio Microbiología con Sole como responsable ------------------
lab = Laboratory.find([('code', '=', 'MICRO')])
if lab:
    lab = lab[0]
    changed = False
    for fld in ('default_manager', 'default_signer', 'default_laboratory_professional'):
        if getattr(lab, fld, None) is None:
            setattr(lab, fld, Professional(prof.id))
            changed = True
    if changed:
        lab.save()
    print('Laboratorio MICRO ya existe (responsables actualizados)')
else:
    storage = Location.find([('type', '=', 'storage'), ('name', '=', 'Storage Zone')])
    if not storage:
        storage = Location.find([('type', '=', 'storage')])
    lab = Laboratory(code='MICRO', description='Microbiología', section='mi')
    lab.related_location = Location(storage[0].id)
    lab.default_laboratory_professional = Professional(prof.id)
    lab.default_signer = Professional(prof.id)
    lab.default_manager = Professional(prof.id)
    lab.save()
    print('Laboratorio Microbiología creado (sección mi), Sole como manager/firmante')

# 8. Departamento Microbiología con Sole responsable ----------------------
dep = Department.find([('code', '=', 'MICRO')])
if dep:
    dep = dep[0]
    print('Departamento MICRO ya existe')
else:
    dep = Department(code='MICRO', name='Microbiología')
    if sole_user:
        dep.responsible = sole_user
    dep.save()
    print('Departamento Microbiología creado (responsable: Sole)')

print('\n== LISTO ==')
print('Compañía:', company.party.name, '| Moneda:', company.currency.code)
print('Laboratorio:', lab.description, '| Manager:', lab.default_manager.party.name if lab.default_manager else '-')
print('Departamento:', dep.name, '| Responsable:', dep.responsible.name if dep.responsible else '-')
