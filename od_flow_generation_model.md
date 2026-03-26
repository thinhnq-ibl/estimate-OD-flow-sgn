# OD Flow Generation Model

## 1. Notation

Assume the city is divided into a set of **subzones**

\[ `\mathcal{Z}`{=tex} = {1,2,...,N} \]

For each subzone (i):

-   (P_i) : population\
-   (O_i) : origin mass\
-   (D_j) : destination mass of zone (j)

Set of POI categories:

\[ C =
{`\text{office}`{=tex},`\text{public\_transport}`{=tex},`\text{shop}`{=tex},`\text{amenity}`{=tex},`\text{tourism}`{=tex},`\text{leisure}`{=tex}}
\]

Each category has a weight (w_c).

------------------------------------------------------------------------

# 2. Destination Mass from POIs

Let (n\_{j,c}) be the number of POIs of category (c) in subzone (j).

Destination mass:

\[ D_j = `\sum`{=tex}*{c `\in `{=tex}C} w_c `\cdot `{=tex}n*{j,c} + 1 \]

Weights:

  Category           Weight
  ------------------ --------
  office             15
  public_transport   50
  shop               10
  amenity            2
  tourism            4
  leisure            1

------------------------------------------------------------------------

# 3. Origin Mass

Origin mass of subzone (i):

\[ O_i = P_i + 1 \]

------------------------------------------------------------------------

# 4. Distance Between Subzones

Distance between zones:

\[ d\_{ij} \]

Distance bins:

\[ b(i,j)=
```{=tex}
\begin{cases}
B_1 & d_{ij} < 1km \\
B_2 & 1km \le d_{ij} < 10km \\
B_3 & 10km \le d_{ij} < 100km
\end{cases}
```
\]

------------------------------------------------------------------------

# 5. Intervening Opportunities

For each pair (i,j):

\[ s\_{ij} = `\sum`{=tex}*{k `\neq `{=tex}i,j ;:; d*{ik} \< d\_{ij}} D_k
\]

This represents the total opportunity mass closer to (i) than (j).

------------------------------------------------------------------------

# 6. Radiation Interaction Score

Using the radiation model:

\[ A\_{ij} = `\frac{O_i \cdot D_j}`{=tex} {(O_i + s\_{ij})(O_i + D_j +
s\_{ij})} \]

Where:

-   (O_i): origin population mass\
-   (D_j): destination opportunity mass\
-   (s\_{ij}): intervening opportunities

------------------------------------------------------------------------

# 7. Facebook Distance Distribution

Meta mobility data provides trip distribution by distance:

\[ p_0 = P(d \< 1km) \]

\[ p\_{10} = P(1km `\le `{=tex}d \< 10km) \]

\[ p\_{100} = 1 - p_0 - p\_{10} \]

------------------------------------------------------------------------

# 8. Normalization within Distance Bins

For each bin (b):

\[ S_b = `\sum`{=tex}*{(i,j):b(i,j)=b} A*{ij} \]

Trip probability:

\[ Pr\_{ij} =
```{=tex}
\begin{cases}
\frac{A_{ij}}{S_{B_1}} \cdot p_0 & b(i,j)=B_1 \\
\frac{A_{ij}}{S_{B_2}} \cdot p_{10} & b(i,j)=B_2 \\
\frac{A_{ij}}{S_{B_3}} \cdot (1-p_0-p_{10}) & b(i,j)=B_3
\end{cases}
```
\]

------------------------------------------------------------------------

# 9. Generate OD Flow

Let total trips in the system be:

\[ T \]

Generated OD flow:

\[ F\_{ij} = T `\cdot `{=tex}Pr\_{ij} \]

------------------------------------------------------------------------

# 10. Normalization

Total generated trips:

\[ T\^{gen} = `\sum`{=tex}*{i,j} F*{ij} \]

Normalized flow:

\[ `\tilde{F}`{=tex}\_{ij} = `\frac{F_{ij}}{T^{gen}}`{=tex} \]

------------------------------------------------------------------------

# 11. Ground Truth Normalization

Let ground truth OD matrix be (G\_{ij}).

\[ T\^{GT} = `\sum`{=tex}*{i,j} G*{ij} \]

Normalized ground truth:

\[ `\tilde{G}`{=tex}\_{ij} = `\frac{G_{ij}}{T^{GT}}`{=tex} \]

------------------------------------------------------------------------

# 12. Evaluation Metric: CPC

Common Part of Commuters (CPC):

\[ CPC = `\frac{
2 \sum_{i,j} \min(\tilde{F}_{ij}, \tilde{G}_{ij})
}{
\sum_{i,j} \tilde{F}_{ij} + \sum_{i,j} \tilde{G}_{ij}
}`{=tex} \]

Since both matrices are normalized:

\[ CPC = `\sum`{=tex}*{i,j} `\min`{=tex}(`\tilde{F}`{=tex}*{ij},
`\tilde{G}`{=tex}\_{ij}) \]

------------------------------------------------------------------------

# 13. Model Pipeline

\[ Population + POIs \]

\[ `\Downarrow`{=tex} \]

\[ (O_i, D_j) \]

\[ `\Downarrow`{=tex} \]

\[ d\_{ij} `\rightarrow `{=tex}s\_{ij} \]

\[ `\Downarrow`{=tex} \]

\[ A\_{ij} ; (`\text{Radiation Model}`{=tex}) \]

\[ `\Downarrow`{=tex} \]

\[ Distance bin normalization using Facebook distribution \]

\[ `\Downarrow`{=tex} \]

\[ F\_{ij} ; (`\text{Generated OD}`{=tex}) \]

\[ `\Downarrow`{=tex} \]

\[ CPC(F,G) \]
