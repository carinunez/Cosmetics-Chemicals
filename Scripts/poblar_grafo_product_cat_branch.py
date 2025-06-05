
# poblar_grafoA_fecha_parse.py
import re
from rdflib import Graph, Namespace, URIRef, Literal
from rdflib.namespace import RDF, RDFS, XSD
import pandas as pd
from datetime import datetime

# Crear grafo RDF
g = Graph()

# Namespace
EX = Namespace("http://example.org/cdph/") # Cambiar a un URI base adecuado en el futuro
g.bind("ex", EX)
g.bind("rdf", RDF)
g.bind("rdfs", RDFS)
g.bind("xsd", XSD)

# Leer CSV
ruta_csv = "cscpopendata.csv"  # Ajustar ruta al path propio
df = pd.read_csv(ruta_csv, dtype=str).fillna("")

# Sets para evitar duplicados
productos_creados = set()
companias_creadas = set()
marcas_creadas = set()
categorias_creadas = set()
subcategorias_creadas = set()

# Función para convertir fechas a ISO 8601
def convertir_a_iso(fecha_str):
    fecha_str = fecha_str.strip()
    if not fecha_str:
        return None
    # Intentar varios formatos comunes
    formatos = ["%Y-%m-%dT%H:%M:%S", "%Y-%m-%d", "%m/%d/%Y", "%m/%d/%Y %H:%M:%S"]
    for fmt in formatos:
        try:
            dt = datetime.strptime(fecha_str, fmt)
            # Convertir a formato completo ISO con hora
            return dt.isoformat()
        except ValueError:
            continue
    # Si no coincide con ningún formato, devolvemos None (o la cadena sin procesar)
    return None

def slugify(text):
    """
    Convierte cualquier texto en un slug válido para IRI local name:
    - Reemplaza espacios por guiones bajos.
    - Elimina todo lo que no sea letra, número, guión o guion bajo.
    - Convierte a ASCII si fuera necesario (aquí se asume que no hay acentos, 
      pero si hay, podrías usar un paquete como unidecode).
    """
    # 1. Reemplaza espacios (u otras series blancas) por guiones bajos
    s = re.sub(r"\s+", "_", text.strip())
    # 2. Elimina TODOS los caracteres que no sean A-Z a-z 0-9 _ -
    s = re.sub(r"[^A-Za-z0-9_-]", "", s)
    return s

# Funciones para URIs
def uri_producto(cdp_id):
    # Si cdp_id fuera `"10"` o `"100"`, quedaría igual. 
    # En principio tus IDs numéricos no tienen problema.
    return EX[f"Product-{slugify(cdp_id)}"]

def uri_compania(company_id):
    return EX[f"Company-{slugify(company_id)}"]

def uri_marca(brand_name):
    # Ahora “L'Oreal USA” -> slugify -> “LOreal_USA”
    slug = slugify(brand_name)
    return EX[f"Brand-{slug}"]

def uri_categoria(cat_id):
    return EX[f"Category-{slugify(cat_id)}"]

def uri_subcategoria(subcat_id):
    return EX[f"SubCategory-{slugify(subcat_id)}"]


# URIs de clases
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

# Iterar filas
for _, row in df.iterrows():
    prod_id = row["CDPHId"]
    URIProd = uri_producto(prod_id)

    if prod_id not in productos_creados:
        g.add((URIProd, RDF.type, ClaseProduct))
        g.add((URIProd, prop_hasCDPHId, Literal(prod_id, datatype=XSD.string)))
        if row["ProductName"].strip():
            g.add((URIProd, prop_hasProductName, Literal(row["ProductName"], datatype=XSD.string)))

        # Convertir y agregar fechas
        inicial = convertir_a_iso(row["InitialDateReported"])
        if inicial:
            g.add((URIProd, prop_hasInitialDateReported, Literal(inicial, datatype=XSD.dateTime)))
        reciente = convertir_a_iso(row["MostRecentDateReported"])
        if reciente:
            g.add((URIProd, prop_hasMostRecentDateReported, Literal(reciente, datatype=XSD.dateTime)))
        descontinuado = convertir_a_iso(row["DiscontinuedDate"])
        if descontinuado:
            g.add((URIProd, prop_hasDiscontinuedDate, Literal(descontinuado, datatype=XSD.dateTime)))
        productos_creados.add(prod_id)

    # Compañía
    comp_id = row["CompanyId"]
    URIComp = uri_compania(comp_id)
    if comp_id not in companias_creadas:
        g.add((URIComp, RDF.type, ClaseCompany))
        g.add((URIComp, prop_hasCompanyId, Literal(comp_id, datatype=XSD.string)))
        if "CompanyName" in df.columns and row["CompanyName"].strip():
            g.add((URIComp, prop_hasCompanyName, Literal(row["CompanyName"], datatype=XSD.string)))
        companias_creadas.add(comp_id)
    g.add((URIProd, prop_productMadeByCompany, URIComp))

    # Marca
    if "BrandName" in df.columns and row["BrandName"].strip():
        brand_name = row["BrandName"]
        URIBrand = uri_marca(brand_name)
        if brand_name not in marcas_creadas:
            g.add((URIBrand, RDF.type, ClaseBrand))
            g.add((URIBrand, prop_hasBrandName, Literal(brand_name, datatype=XSD.string)))
            marcas_creadas.add(brand_name)
        g.add((URIProd, prop_productHasBrand, URIBrand))

    # Categoría
    cat_id = row["PrimaryCategoryId"]
    URICat = uri_categoria(cat_id)
    if cat_id not in categorias_creadas:
        g.add((URICat, RDF.type, ClaseCategory))
        g.add((URICat, prop_hasPrimaryCategoryId, Literal(cat_id, datatype=XSD.string)))
        if "PrimaryCategoryName" in df.columns and row["PrimaryCategoryName"].strip():
            g.add((URICat, prop_hasPrimaryCategoryName, Literal(row["PrimaryCategoryName"], datatype=XSD.string)))
        categorias_creadas.add(cat_id)
    g.add((URIProd, prop_productHasCategory, URICat))

    # Subcategoría
    subcat_id = row["SubCategoryId"]
    URISubcat = uri_subcategoria(subcat_id)
    if subcat_id not in subcategorias_creadas:
        g.add((URISubcat, RDF.type, ClaseSubCategory))
        g.add((URISubcat, prop_hasSubCategoryId, Literal(subcat_id, datatype=XSD.string)))
        if "SubCategoryName" in df.columns and row["SubCategoryName"].strip():
            g.add((URISubcat, prop_hasSubCategoryName, Literal(row["SubCategoryName"], datatype=XSD.string)))
        subcategorias_creadas.add(subcat_id)
    g.add((URIProd, prop_productHasSubCategory, URISubcat))

# Serializar a archivo
output_file = "grafoA_metadata.ttl"
g.serialize(destination=output_file, format="turtle")
print(f"Grafo A exportado a {output_file} con {len(g)} triples.")
