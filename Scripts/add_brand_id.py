import numpy as np
import pandas as pd
from sklearn.preprocessing import LabelEncoder

cosmetics = pd.read_csv(r'..\cosmetics.csv')

le = LabelEncoder()
le.fit(cosmetics['BrandName'])

brands = []
for i, l in enumerate(le.classes_):
    brands.append([i,l])

brands_id = pd.DataFrame(columns=['BrandId', 'BrandName'], data=brands)

cosmetics_new = cosmetics.merge(brands_id)
cosmetics_new.to_csv(r'cosmetics2.csv')