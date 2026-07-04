#!/usr/bin/env python3
"""Catálogo de microbiología de alimentos (starter estándar) para Cromaquim.
Crea: matrices/tipos de producto, métodos (workflow->activo), análisis (workflow->activo)
ligados al laboratorio Microbiología, y tipificaciones (análisis usable por matriz)."""
import sys
from decimal import Decimal
from proteus import config, Model

DB = sys.argv[1] if len(sys.argv) > 1 else 'kalenislims'
cfg = config.set_trytond(DB, config_file='trytond.dev.conf')
print('Conectado a', DB)

Analysis = Model.get('lims.analysis')
Method = Model.get('lims.lab.method')
Matrix = Model.get('lims.matrix')
ProductType = Model.get('lims.product.type')
Typification = Model.get('lims.typification')
Laboratory = Model.get('lims.laboratory')
Config = Model.get('lims.configuration')
ProductCategory = Model.get('product.category')
NotebookView = Model.get('lims.notebook.view')
ModelField = Model.get('ir.model.field')
Product = Model.get('product.product')
Template = Model.get('product.template')
Uom = Model.get('product.uom')

lab = Laboratory.find([('code', '=', 'MICRO')])[0]
unit = Uom.find(['OR', ('symbol', '=', 'u'), ('symbol', '=', 'x 1 u')])[0]

# --- Configuración del LIMS (prerequisito para activar análisis) ---------
# Categoría de producto (el producto de cada análisis se crea al activarlo)
cat = ProductCategory.find([('name', '=', 'Análisis')])
cat = cat[0] if cat else None
if cat is None:
    cat = ProductCategory(name='Análisis')
    cat.save()
    print('Categoría de producto "Análisis" creada')

# Vista de cuaderno por defecto (requerida por lims.configuration)
nv = NotebookView.find([('name', '=', 'General')])
if nv:
    nv = nv[0]
else:
    nv = NotebookView(name='General')
    cols = ['analysis', 'method', 'repetition', 'result', 'result_modifier',
            'professionals', 'start_date', 'end_date']
    for i, fname in enumerate(cols, start=1):
        fld = ModelField.find([('model.model', '=', 'lims.notebook.line'),
                               ('name', '=', fname)])[0]
        col = nv.columns.new()
        col.field = ModelField(fld.id)
        col.sequence = i * 10
    nv.save()
    print('Vista de cuaderno "General" creada con', len(cols), 'columnas')

# Producto de fracción (requerido por la config; mismo patrón que Kalenis usa
# para autogenerar los productos de análisis)
fp = Product.find([('template.name', '=', 'Fracción')])
if fp:
    fp = fp[0]
else:
    tmpl = Template()
    tmpl.name = 'Fracción'
    tmpl.type = 'service'
    tmpl.list_price = Decimal('1.0')
    tmpl.cost_price = Decimal('1.0')
    tmpl.default_uom = Uom(unit.id)
    tmpl.save()
    fp = Product()
    fp.template = Template(tmpl.id)
    fp.save()
    print('Producto "Fracción" creado')

# Config singleton: setear los campos sin default; el resto se autogenera
config_ = Config(1)
changed = False
if not config_.analysis_product_category:
    config_.analysis_product_category = ProductCategory(cat.id)
    changed = True
if not config_.default_notebook_view:
    config_.default_notebook_view = NotebookView(nv.id)
    changed = True
if not config_.fraction_product:
    config_.fraction_product = Product(fp.id)
    changed = True
if changed:
    config_.save()
    print('lims.configuration seteada (producto categoría + vista cuaderno + producto fracción)')

def goc(Mdl, code, **kw):
    r = Mdl.find([('code', '=', code)])
    if r:
        return r[0], False
    obj = Mdl(code=code, **kw)
    return obj, True

# --- Tipos de producto y matrices ---------------------------------------
prod_types, matrices = {}, {}
for code, desc in [('ALIM', 'Alimentos'), ('AGUA', 'Aguas')]:
    pt, new = goc(ProductType, code, description=desc)
    if new:
        pt.save(); print('Tipo de producto creado:', desc)
    prod_types[code] = pt
    mx, new = goc(Matrix, code, description=desc)
    if new:
        mx.save(); print('Matriz creada:', desc)
    matrices[code] = mx

# --- Catálogo: (cod_análisis, descripción, cod_método, nombre_método, determinación, matrices) ---
CATALOG = [
    ('MB-AER',  'Recuento de aerobios mesófilos totales', 'ISO4833',  'ISO 4833-1',  'Recuento de aerobios mesófilos',        ['ALIM', 'AGUA']),
    ('MB-COLT', 'Recuento de coliformes totales',         'ISO4832',  'ISO 4832',    'Recuento de coliformes totales',        ['ALIM', 'AGUA']),
    ('MB-COLF', 'Coliformes termotolerantes (fecales)',   'MB-CF',    'Coliformes fecales (NMP)', 'Coliformes termotolerantes', ['ALIM', 'AGUA']),
    ('MB-ECOLI','Escherichia coli',                       'ISO16649', 'ISO 16649-2', 'Recuento de Escherichia coli',          ['ALIM', 'AGUA']),
    ('MB-HYL',  'Recuento de hongos y levaduras',         'ISO21527', 'ISO 21527',   'Recuento de hongos y levaduras',        ['ALIM']),
    ('MB-SALM', 'Detección de Salmonella spp. en 25 g',   'ISO6579',  'ISO 6579-1',  'Detección de Salmonella spp.',          ['ALIM']),
    ('MB-SAUR', 'Staphylococcus aureus coagulasa +',      'ISO6888',  'ISO 6888-1',  'Recuento de S. aureus coagulasa +',     ['ALIM']),
    ('MB-LIST', 'Detección de Listeria monocytogenes',    'ISO11290', 'ISO 11290-1', 'Detección de Listeria monocytogenes',   ['ALIM']),
]

def get_method(code, name, determination):
    m, new = goc(Method, code, name=name, determination=determination,
                 requalification_months=12)
    if new:
        m.save()
        m.click('activate')
        print('  método creado y activado:', name)
    return m

n_an = n_typ = 0
for acode, adesc, mcode, mname, deter, mxs in CATALOG:
    method = get_method(mcode, mname, deter)

    ans = Analysis.find([('code', '=', acode)])
    if ans:
        an = ans[0]
    else:
        an = Analysis(code=acode, description=adesc, type='analysis',
                      behavior='normal')
        al = an.laboratories.new()
        al.laboratory = Laboratory(lab.id)
        an.methods.append(Method(method.id))
        an.save()
        n_an += 1
        print('Análisis creado:', adesc)
    # asegurar activo (la tipificación exige analysis.state == active)
    if an.state == 'draft':
        an.click('activate')

    for mxcode in mxs:
        ex = Typification.find([
            ('analysis', '=', an.id),
            ('matrix', '=', matrices[mxcode].id),
            ('method', '=', method.id)])
        if ex:
            continue
        t = Typification()
        t.product_type = ProductType(prod_types[mxcode].id)
        t.matrix = Matrix(matrices[mxcode].id)
        t.analysis = Analysis(an.id)
        t.method = Method(method.id)
        t.calc_decimals = 2
        t.default_repetitions = 0
        t.by_default = True
        t.save()
        n_typ += 1

print('\n== LISTO ==  análisis nuevos: %d | tipificaciones nuevas: %d' % (n_an, n_typ))
print('Análisis en laboratorio Microbiología:',
      Analysis.find_count([('laboratories.laboratory', '=', lab.id),
                           ('type', '=', 'analysis')]))
