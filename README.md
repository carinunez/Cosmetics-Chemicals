# Cosmetics-Chemicals

## Descripción

Este repositorio contedndra la ontología RDF y los scripts en Python para transformar una base de datos relacional (CSV) en tres subgrafos RDF:

- **Grafo A(grafo_product_cat_branch)** (Metadatos del producto como: Clases, subclases y marcas de producto)  
- **Grafo B** (CSF: Color/Sabor/Fragancia)  
- **Grafo C** (Químicos y asociaciones Producto–Químico)

La clase central es `ex:Product-<CDPHId>`, que enlaza la información incluida en cada subgrafo. Con esto se busca facilitar consultas SPARQL que exploten rutas e interconexiones propias de grafos, así como servir de punto de partida para tareas de análisis o machine learning (como podrian ser clasificación de categoría o detección de productos incompletos).
