
# poblar_grafoA_fecha_parse.py
import re
from rdflib import Graph, Namespace, URIRef, Literal
from rdflib.namespace import RDF, RDFS, XSD
import pandas as pd

# Crear grafo RDF
g = Graph()

# Namespace
EX = Namespace("http://example.org/cdph/") # Cambiar a un URI base adecuado en el futuro
g.bind("ex", EX)
g.bind("rdf", RDF)
g.bind("rdfs", RDFS)
g.bind("xsd", XSD)

# Leer CSV
ruta_csv = "Chemicals_concerns\\cosmetics_chem_concerns.csv"  # Ajustar ruta al path propio
df = pd.read_csv(ruta_csv, dtype=str).fillna("")

# Sets para evitar duplicados
productos_creados = set()
quimicos_creados = set()
concern_creada = set()


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

def uri_chemical(chemical_casRN):
    return EX[f"Chemical-{slugify(chemical_casRN)}"]




# URIs de clases
ClaseProduct = EX.Product
ClaseChemical = EX.Chemical
ClaseConcern = EX.Concern

# Propiedades
prop_containsChemical = EX.containsChemical # el producto tiene un quimico
prop_hasConcern = EX.hasConcern # preocupaciones asociadas a los chem


prop_hasCDPHId = EX.hasCDPHId
prop_hasProductName = EX.hasProductName

prop_hasChemID = EX.hasChemID
prop_CasNumber = EX.hasCasNumber
prop_ChemicalName = EX.hasChemicalName
prop_hasEWGName = EX.hasEWGName
prop_hasHazardScore = EX.hasHazardScore

# prop_ConcernType = EX.ConcernType
# prop_ConcernLevel = EX.ConcernLevel

prop_CancerConcern = EX.CancerConcern
prop_Allergies_InmunoticityConcern = EX.AllergiesConcern
prop_DevelopReproductiveConcern = EX.DevelopReproductiveConcern
prop_UseRestrictionsConcern = EX.UseRestrictionsConcern


def concern_level(graph, chem, prop, value):
    if str(value).strip() != '':
        graph.add((chem, prop, Literal(str(value).strip().lower(), datatype=XSD.string)))
    else:
        graph.add((chem, prop, Literal('', datatype=XSD.string)))

# Iterar filas
for _, row in df.iterrows():
    # Producto
    prod_id = row["CDPHId"]
    URIProd = uri_producto(prod_id)

    if prod_id not in productos_creados:
        g.add((URIProd, RDF.type, ClaseProduct))
        g.add((URIProd, prop_hasCDPHId, Literal(prod_id, datatype=XSD.string)))
        if row["ProductName"].strip():
            g.add((URIProd, prop_hasProductName, Literal(row["ProductName"], datatype=XSD.string)))
        productos_creados.add(prod_id)


    # Químico
    chem_id = row["ChemID"]
    URIChem = uri_chemical(chem_id)
    if chem_id not in quimicos_creados:
        g.add((URIChem, RDF.type, ClaseChemical))
        g.add((URIChem, prop_hasChemID, Literal(chem_id, datatype=XSD.string)))

        if "ChemID" in df.columns and row["ChemID"].strip():
            g.add((URIChem, prop_CasNumber, Literal(row["CasNumber"], datatype=XSD.string)))
            g.add((URIChem, prop_ChemicalName, Literal(row["ChemicalName"], datatype=XSD.string)))
            g.add((URIChem, prop_hasEWGName, Literal(row["name_EWG"], datatype=XSD.string)))

            for hazardS in row['hazard_score']:
                if hazardS == '':
                    g.add((URIChem, prop_hasHazardScore, Literal('', datatype=XSD.string)))
                else:
                    g.add((URIChem, prop_hasHazardScore, Literal(float(row["hazard_score"]), datatype=XSD.float)))

            # Agrego las preocupaciones de salud
            concern_level(g, URIChem, prop_CancerConcern, row["Cancer"])
            concern_level(g, URIChem, prop_Allergies_InmunoticityConcern, row["Allergies & Immunotoxicity"])
            concern_level(g, URIChem, prop_DevelopReproductiveConcern, row['Developmental and Reproductive Toxicity'])
            concern_level(g, URIChem, prop_UseRestrictionsConcern, row['Use Restrictions'])

        quimicos_creados.add(chem_id)
        
    g.add((URIProd, prop_containsChemical, URIChem))

    


# Serializar a archivo
output_file = "grafo_prod_chem_concerns.ttl"
g.serialize(destination=output_file, format="turtle")
print(f"Grafo A exportado a {output_file} con {len(g)} triples.")
