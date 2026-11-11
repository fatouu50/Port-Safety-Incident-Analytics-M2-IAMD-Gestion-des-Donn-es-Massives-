import pandas as pd
import matplotlib.pyplot as plt
df = pd.read_csv('../01_DATA_RAW/safety_observations.csv')
print(df.shape)
print(df.head())
print(df.describe(include='all').transpose())
# TODO: 3 graphiques minimum et interprétation métier
