# poblar_grafo_product_cat_branch.py

import re
from rdflib import Graph, Namespace, URIRef, Literal
from rdflib.namespace import RDF, RDFS, XSD
import pandas as pd
from datetime import datetime

# Crear grafo RDF
g = Graph()

# Namespace
EX = Namespace("http://example.org/cdph/")
g.bind("ex", EX)
g.bind("rdf", RDF)
g.bind("rdfs", RDFS)
g.bind("xsd", XSD)

# Leer CSV
ruta_csv = "cscpopendata.csv"
df = pd.read_csv(ruta_csv, dtype=str).fillna("")

# Sets para evitar duplicados
productos_creados = set()
companias_creadas = set()
marcas_creadas = set()
categorias_creadas = set()
subcategorias_creadas = set()

# Función para convertir fechas
def convertir_a_iso(fecha_str):
    fecha_str = fecha_str.strip()
    if not fecha_str:
        return None
    formatos = ["%Y-%m-%dT%H:%M:%S", "%Y-%m-%d", "%m/%d/%Y", "%m/%d/%Y %H:%M:%S"]
    for fmt in formatos:
        try:
            return datetime.strptime(fecha_str, fmt).isoformat()
        except ValueError:
            continue
    return None

# Función para limpiar textos para URIs
def slugify(text):
    s = re.sub(r"\s+", "_", text.strip())
    s = re.sub(r"[^A-Za-z0-9_-]", "", s)
    return s

# URIs
def uri_producto(cdp_id): return EX[f"Product-{slugify(cdp_id)}"]
def uri_compania(company_id): return EX[f"Company-{slugify(company_id)}"]
def uri_marca(brand_name): return EX[f"Brand-{slugify(brand_name)}"]
def uri_categoria(cat_id): return EX[f"Category-{slugify(cat_id)}"]
def uri_subcategoria(subcat_id): return EX[f"SubCategory-{slugify(subcat_id)}"]

# Clases
ClaseProduct = EX.Product
ClaseCompany = EX.Company
ClaseBrand = EX.Brand
ClaseCategory = EX.Category
ClaseSubCategory = EX.SubCategory

# Propiedades
prop_hasCDPHId = EX.hasCDPHId
prop_hasProductName = EX.hasProductName
prop_hasInitialDateReported = EX.hasInitialDateReported
prop_hasMostRecentDateReported = EX.hasMostRecentDateReported
prop_hasDiscontinuedDate = EX.hasDiscontinuedDate
prop_productMadeByCompany = EX.productMadeByCompany
prop_productHasBrand = EX.productHasBrand
prop_productHasCategory = EX.productHasCategory
prop_productHasSubCategory = EX.productHasSubCategory
prop_hasCompanyId = EX.hasCompanyId
prop_hasCompanyName = EX.hasCompanyName
prop_hasBrandName = EX.hasBrandName
prop_hasPrimaryCategoryId = EX.hasPrimaryCategoryId
prop_hasPrimaryCategoryName = EX.hasPrimaryCategoryName
prop_hasSubCategoryId = EX.hasSubCategoryId
prop_hasSubCategoryName = EX.hasSubCategoryName

# Iterar sobre filas
for _, row in df.iterrows():
    prod_id = row["CDPHId"]
    URIProd = uri_producto(prod_id)

    if prod_id not in productos_creados:
        g.add((URIProd, RDF.type, ClaseProduct))
        g.add((URIProd, prop_hasCDPHId, Literal(prod_id, datatype=XSD.string)))
        if row["ProductName"].strip():
            g.add((URIProd, prop_hasProductName, Literal(row["ProductName"], datatype=XSD.string)))
        for campo, prop in [
            ("InitialDateReported", prop_hasInitialDateReported),
            ("MostRecentDateReported", prop_hasMostRecentDateReported),
            ("DiscontinuedDate", prop_hasDiscontinuedDate)
        ]:
            fecha = convertir_a_iso(row[campo])
            if fecha:
                g.add((URIProd, prop, Literal(fecha, datatype=XSD.dateTime)))
        productos_creados.add(prod_id)

    # Company
    comp_id = row["CompanyId"]
    URIComp = uri_compania(comp_id)
    if comp_id not in companias_creadas:
        g.add((URIComp, RDF.type, ClaseCompany))
        g.add((URIComp, prop_hasCompanyId, Literal(comp_id, datatype=XSD.string)))
        if row["CompanyName"].strip():
            g.add((URIComp, prop_hasCompanyName, Literal(row["CompanyName"], datatype=XSD.string)))
        companias_creadas.add(comp_id)
    g.add((URIProd, prop_productMadeByCompany, URIComp))

    # Brand
    if row["BrandName"].strip():
        brand_name = row["BrandName"]
        URIBrand = uri_marca(brand_name)
        if brand_name not in marcas_creadas:
            g.add((URIBrand, RDF.type, ClaseBrand))
            g.add((URIBrand, prop_hasBrandName, Literal(brand_name, datatype=XSD.string)))
            marcas_creadas.add(brand_name)
        g.add((URIProd, prop_productHasBrand, URIBrand))

    # Category
    cat_id = row["PrimaryCategoryId"]
    URICat = uri_categoria(cat_id)
    if cat_id not in categorias_creadas:
        g.add((URICat, RDF.type, ClaseCategory))
        g.add((URICat, prop_hasPrimaryCategoryId, Literal(cat_id, datatype=XSD.string)))
        if row["PrimaryCategory"].strip():
            g.add((URICat, prop_hasPrimaryCategoryName, Literal(row["PrimaryCategory"], datatype=XSD.string)))
        categorias_creadas.add(cat_id)
    g.add((URIProd, prop_productHasCategory, URICat))

    # SubCategory
    subcat_id = row["SubCategoryId"]
    URISubcat = uri_subcategoria(subcat_id)
    if subcat_id not in subcategorias_creadas:
        g.add((URISubcat, RDF.type, ClaseSubCategory))
        g.add((URISubcat, prop_hasSubCategoryId, Literal(subcat_id, datatype=XSD.string)))
        if row["SubCategory"].strip():
            g.add((URISubcat, prop_hasSubCategoryName, Literal(row["SubCategory"], datatype=XSD.string)))
        subcategorias_creadas.add(subcat_id)
    g.add((URIProd, prop_productHasSubCategory, URISubcat))

# Guardar grafo
output_file = "grafoA_metadata.ttl"
g.serialize(destination=output_file, format="turtle")
print(f"Grafo A exportado a {output_file} con {len(g)} triples.")

