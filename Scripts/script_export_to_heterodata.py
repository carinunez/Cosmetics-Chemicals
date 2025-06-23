# script_export_to_heterodata.py

from rdflib import Graph, URIRef, RDF, Literal
from collections import defaultdict
from torch_geometric.data import HeteroData
import torch
from datetime import datetime

# 1) Carga del grafo RDF
ttl_file = "grafo_completo.ttl"  # Ajusta la ruta a la propia
g = Graph()
g.parse(ttl_file, format="turtle")

# 2) Helper de namespace
NS = "http://example.org/cdph/"
def uri(prop): return URIRef(NS + prop)

# 3) Definición de clases RDF
rdf_types = {
    "Product":     uri("Product"),
    "Brand":       uri("Brand"),
    "Company":     uri("Company"),
    "Category":    uri("Category"),
    "SubCategory": uri("SubCategory"),
    "Chemical":    uri("Chemical"),
}

# 4) Indexar nodos por tipo
node_maps  = {nt: {} for nt in rdf_types}
node_counts = {nt: 0 for nt in rdf_types}
for subj, _, obj in g.triples((None, RDF.type, None)):
    for ntype, cls in rdf_types.items():
        if obj == cls and subj not in node_maps[ntype]:
            node_maps[ntype][subj] = node_counts[ntype]
            node_counts[ntype] += 1

# 5) Pre-calcular edad y etiqueta para productos, y conteo de químicos
prod_age   = {}
prod_label = {}
chem_counts = defaultdict(int)

for prod_node in node_maps["Product"]:
    # Edad
    init = g.value(prod_node, uri("hasInitialDateReported"))
    most = g.value(prod_node, uri("hasMostRecentDateReported"))
    age_days = 0
    if isinstance(init, Literal) and isinstance(most, Literal):
        try:
            d0 = datetime.fromisoformat(str(init))
            d1 = datetime.fromisoformat(str(most))
            age_days = (d1 - d0).days
        except:
            pass
    prod_age[prod_node] = age_days
    # Etiqueta
    prod_label[prod_node] = int(bool(g.value(prod_node, uri("hasDiscontinuedDate"))))

# Conteo de químicos por producto
for s, _, o in g.triples((None, uri("productHasChemical"), None)):
    if s in node_maps["Product"] and o in node_maps["Chemical"]:
        chem_counts[s] += 1

# 6) Construir HeteroData
data = HeteroData()

# 7) Features y labels para Product
prod_feats  = []
prod_labels = []
for prod_node, idx in sorted(node_maps["Product"].items(), key=lambda x: x[1]):
    feat = [
        chem_counts.get(prod_node, 0),         # número de químicos
        int(bool(g.value(prod_node, uri("productHasBrand")))),
        int(bool(g.value(prod_node, uri("productHasCategory")))),
        int(bool(g.value(prod_node, uri("productHasSubCategory")))),
        int(bool(g.value(prod_node, uri("productMadeByCompany")))),
    ]
    prod_feats.append(feat)
    prod_labels.append(prod_label[prod_node])

data["Product"].x = torch.tensor(prod_feats, dtype=torch.float)
data["Product"].y = torch.tensor(prod_labels, dtype=torch.long)

# 8) Features para Chemical
chem_feats = []
for chem_node, idx in sorted(node_maps["Chemical"].items(), key=lambda x: x[1]):
    hv = 0
    h_lit = g.value(chem_node, uri("hasHazardScore"))
    if isinstance(h_lit, Literal):
        py = h_lit.toPython()
        if isinstance(py, (int, float)):
            hv = int(py)
        else:
            s = str(py)
            hv = int(s) if s.isdigit() else 0
    flags = [ # Me di cuenta de que son flags solo son indicaciones booleans despues de hacer la GNN, es decir, no estamos usando 
            # flags como tal, sino que son indicadores de si existen o no... lo cual como todos tiene hacen esta features inutiles XD. 
            # *Necesita cambio*
        int(bool(g.value(chem_node, uri("AllergiesConcern")))),
        int(bool(g.value(chem_node, uri("CancerConcern")))),
        int(bool(g.value(chem_node, uri("DevelopReproductiveConcern")))),
        int(bool(g.value(chem_node, uri("UseRestrictionsConcern")))),
    ]
    chem_feats.append([hv] + flags)

data["Chemical"].x = torch.tensor(chem_feats, dtype=torch.float)

# 9) Features “agregadas” para Brand, Company, Category, SubCategory
def build_hub_features(node_type, prop):
    feats = []
    for node, idx in sorted(node_maps[node_type].items(), key=lambda x: x[1]):
        prods = [s for s, _, o in g.triples((None, uri(prop), node))]
        n = len(prods)
        if n > 0:
            avg_age  = sum(prod_age[p] for p in prods) / n
            avg_chem = sum(chem_counts.get(p,0) for p in prods) / n
        else:
            avg_age = avg_chem = 0.0
        feats.append([n, avg_age, avg_chem])
    return torch.tensor(feats, dtype=torch.float)

data["Brand"].x       = build_hub_features("Brand",       "productHasBrand")
data["Company"].x     = build_hub_features("Company",     "productMadeByCompany")
data["Category"].x    = build_hub_features("Category",    "productHasCategory")
data["SubCategory"].x = build_hub_features("SubCategory", "productHasSubCategory")

# 10) Extraer aristas
obj_props = {
    ("Product", "hasBrand",       "Brand"):       "productHasBrand",
    ("Product", "hasCategory",    "Category"):    "productHasCategory",
    ("Product", "hasSubCategory", "SubCategory"): "productHasSubCategory",
    ("Product", "madeBy",         "Company"):     "productMadeByCompany",
    ("Product", "hasChemical",    "Chemical"):    "containsChemical",
}

for (src, rel, dst), prop in obj_props.items():
    edges = []
    for s, _, o in g.triples((None, uri(prop), None)):
        if s in node_maps[src] and o in node_maps[dst]:
            edges.append((node_maps[src][s], node_maps[dst][o]))
    if edges:
        data[(src, rel, dst)].edge_index = torch.tensor(edges, dtype=torch.long).t().contiguous()

# 11) Validar y mostrar resumen
data.validate(raise_on_error=True)
print(data)


# 11) Guardar HeteroData en un archivo .pt
torch.save(data, "hetero_data.pt")
print("HeteroData serializado en 'hetero_data.pt'")

