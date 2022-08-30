from statistics import median
import matplotlib
import seaborn as sns
import string
import pandas as pd
import json
from functools import cmp_to_key
from statsmodels.stats.multicomp import pairwise_tukeyhsd

def makeletters(df, alpha=0.05, sortingOrder=None):
    df["p-adj"] = df["p-adj"].astype(float)

    group1 = set(df.group1.tolist())  
    group2 = set(df.group2.tolist())  
    groupSet = group1 | group2  
    groups = sorted(list(groupSet))
    
    letters = list(string.ascii_lowercase)[:len(groups)]
    cldgroups = letters
    
    cld = pd.DataFrame(list(zip(groups, letters, cldgroups)))
    cld[3]=""
    
    for row in df.itertuples():
        if df["p-adj"][row[0]] > (alpha):
            cld.iat[groups.index(df["group1"][row[0]]), 2] += cld.iat[groups.index(df["group2"][row[0]]), 1]
            cld.iat[groups.index(df["group2"][row[0]]), 2] += cld.iat[groups.index(df["group1"][row[0]]), 1]
            
        if df["p-adj"][row[0]] < (alpha):
                cld.iat[groups.index(df["group1"][row[0]]), 3] +=  cld.iat[groups.index(df["group2"][row[0]]), 1]
                cld.iat[groups.index(df["group2"][row[0]]), 3] +=  cld.iat[groups.index(df["group1"][row[0]]), 1]

    cld[2] = cld[2].apply(lambda x: "".join(sorted(x)))
    cld[3] = cld[3].apply(lambda x: "".join(sorted(x)))
    cld.rename(columns={0: "groups"}, inplace=True)
    
    if sortingOrder is None:
        pass 
    else:
        def tm_sorter(column):
            correspondence = {team: order for order, team in enumerate(sortingOrder)}
            return column.map(correspondence)
        cld = cld.sort_values(cld.columns[0], key=tm_sorter)
    cld["labels"] = ""

    letters = list(string.ascii_lowercase)
    unique = []
    for item in cld[2]:

        for fitem in cld["labels"].unique():
            for c in range(0, len(fitem)):
                if not set(unique).issuperset(set(fitem[c])):
                    unique.append(fitem[c])
        g = len(unique)

        for kitem in cld[1]:
            if kitem in item:
                if cld["labels"].loc[cld[1] == kitem].iloc[0] == "":
                    cld["labels"].loc[cld[1] == kitem] += letters[g]

                if kitem in ' '.join(cld[3][cld["labels"]==letters[g]]): 
                    g=len(unique)+1
                    
                if len(set(cld["labels"].loc[cld[1] == kitem].iloc[0]).intersection(cld.loc[cld[2] == item, "labels"].iloc[0])) <= 0:
                    if letters[g] not in list(cld["labels"].loc[cld[1] == kitem].iloc[0]):
                        cld["labels"].loc[cld[1] == kitem] += letters[g]
                    if letters[g] not in list(cld["labels"].loc[cld[2] == item].iloc[0]):
                        cld["labels"].loc[cld[2] == item] += letters[g]
    cld = cld.sort_values("labels")
    cld.drop(columns=[1, 2, 3], inplace=True)
    return(cld)

def multcompCatplot(**kwargs):
    if "kind" not in kwargs:
        kwargs["kind"] = "box"
    if kwargs["kind"] != "box":
        quit("Currently only boxplots are supported, so please set kind='box'")
    value = kwargs["y"];
    kwargs["data"]  = kwargs["data"].dropna();
    facet_vars = ["row","col","x","hue"];
    if "letterSize" not in kwargs:
        kwargs["letterSize"] = 18
    letterSize = kwargs["letterSize"]
    del kwargs["letterSize"]
    facet_orders = {}
    facets = []
    for var in facet_vars:
        if var not in kwargs:
            continue
        facets.append(kwargs[var])
        kwargs["data"][kwargs[var]] = kwargs["data"][kwargs[var]].astype('category')
        facet_orders[kwargs[var]] = kwargs["data"][kwargs[var]].cat.categories.to_list()
    df = kwargs["data"].dropna();
    facets = [kwargs[var] for var in facet_vars if var in kwargs]
    tk = pd.DataFrame()
    tk["values"] = df[value]
    tk["comb"] = df[facets].apply(lambda x: x.to_json(), axis=1)
    tukey = pairwise_tukeyhsd(endog=tk['values'],
                          groups=tk['comb'],
                          alpha=0.05)
    tukey_df = pd.DataFrame(data=tukey._results_table.data[1:], columns=tukey._results_table.data[0])
    median_df = tk.groupby(["comb"])["values"].median().sort_values(ascending=False)
    letters_df = makeletters(tukey_df,alpha=0.05,sortingOrder=median_df.index.tolist())
    
    def sortCustom(a,b):
        aj = json.loads(a[0])
        bj = json.loads(b[0])
        for var in facets:
            if aj[var] == bj[var]:
                continue;
            if facet_orders[var].index(aj[var]) < facet_orders[var].index(bj[var]):
                return -1
            return 1
        return 0
    letters = [[x[1],x[2]] for x in letters_df.reset_index().values.tolist()]
    letters.sort(key=cmp_to_key(sortCustom))
    custom_color = None
    if "custom_color" in kwargs:
        custom_color = kwargs["custom_color"]
        del kwargs["custom_color"]
    if "addPoints" in kwargs:
        if "hue" in kwargs:
            quit("Cannot use hue, col or row together with points")
        if "col" in kwargs:
            xcol = kwargs["col"]
        else:
            xcol = None
        if "row" in kwargs:
            xrow = kwargs["row"]
        else:
            xrow = None
        addPoints = True
        del kwargs["addPoints"]
    else:
        addPoints = False
    if "pointSize" in kwargs:
        pointSize = kwargs["pointSize"]
        del kwargs["pointSize"]
    else:
        pointSize = 5
    g = sns.catplot(**kwargs)
    if addPoints:
        g.map_dataframe(sns.stripplot, x=kwargs["x"], y=kwargs["y"], hue=custom_color[0], palette=custom_color[1], linewidth=1, size=pointSize)
    c = 0
    for ax in g.axes.ravel():
        for p in ax.get_children():
            if type(p) == matplotlib.patches.PathPatch:
                bbox = p.get_extents().transformed(ax.transData.inverted())
                dataj, annotation = letters.pop(0)
                data = json.loads(dataj)
                if (not addPoints) and custom_color and (custom_color[0] in data) and (data[custom_color[0]] in custom_color[1]):
                    p.set_facecolor(custom_color[1][data[custom_color[0]]])
                else:
                    p.set_facecolor("white")
                ax.text(bbox.xmax, bbox.ymax, annotation, ha = 'right', va = 'bottom', size=letterSize)
    return g

colors = {
    "Col-0": "#f0e442", 
    "d14": "#d55e00", 
    "kai2": "#cc79a7", 
    "max2": "#009e73", 
    "smxl6/7/8": "#e69f00",
    "xnd1-5":"#0072b2"
}