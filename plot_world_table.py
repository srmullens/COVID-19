#Import packages & other scripts
import os, sys
import requests
import numpy as np
import pandas as pd
import datetime as dt
import seaborn as sns
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

import read_data
from color_gradient import Gradient

def plot_table(plot_type=None):
    #========================================================================================================
    # User-defined settings
    #========================================================================================================

    #Report date(s) to plot
    #plot_start_date = dt.datetime(2020,2,21)
    #plot_start_date = dt.datetime(2020,3,9)
    #plot_end_date = dt.datetime(2020,3,23)

    today = dt.datetime.now()
    hour = int(today.strftime("%H"))
    today = dt.datetime(            \
        int(today.strftime("%Y")),  \
        int(today.strftime("%m")),  \
        int(today.strftime("%d")))
    yesterday = today - dt.timedelta(days=14)

    if hour>=20:
        plot_start_date = yesterday
        plot_end_date = today
    else:
        plot_start_date = yesterday - dt.timedelta(days=1)
        plot_end_date = today - dt.timedelta(days=1)
    print(f"{hour}: {plot_start_date:%m-%d} -> {plot_end_date:%m-%d}")

    #Whether to save image or display. "directory_path" string is ignored if setting==False.
    save_image = {'setting': True,
                  'directory_path': "/Users/Steve/Desktop/UFlorida/3-Code/COVID/COVID-19"}

    #What to plot (confirmed, deaths, recovered, active, daily)
    if plot_type==None:
        plot_type = "active"

    #Include Mainland China?
    mainland_china = False

    #Plot total numbers?
    plot_total = True

    #========================================================================================================
    # Get COVID-19 case data
    #========================================================================================================

    """
    COVID-19 case data is retrieved from Johns Hopkins CSSE:
    https://github.com/CSSEGISandData/COVID-19
    """

    #Avoid re-reading case data if it's already stored in memory
    try:
        cases
    except:
        output = read_data.read_world(negative_daily=False)
        dates = output['dates']
        cases = output['cases']

    #========================================================================================================
    # Create plot based on type
    #========================================================================================================

    #Function for returning number within range
    def return_val(start_range,end_range,start_size,end_size,val):
        frac = (val-start_range)/(end_range-start_range)
        frac = (frac * (end_size-start_size)) + start_size
        return frac

    #Total count
    total_count = np.array([0.0 for i in cases['mainland china']['date']])
    total_count_row = np.array([0.0 for i in cases['mainland china']['date']])

    #Empty array
    data_annot = []
    data = []
    rows = []

    #Iterate through every region
    sorted_keys = [y[1] for y in sorted([(cases[x][plot_type][-1], x) for x in cases.keys()])][::-1]
    sorted_value = [y[0] for y in sorted([(cases[x][plot_type][-1], x) for x in cases.keys()])][::-1]
    for idx,(key,value) in enumerate(zip(sorted_keys,sorted_value)):

        #Only plot the first 30 locations
        if idx > 40: continue

        #Special handling for Diamond Princess
        if mainland_china == False and key == 'mainland china': continue

        #Total count
        total_count += np.array(cases[key][plot_type])
        if key != 'mainland china': total_count_row += np.array(cases[key][plot_type])

        #Get start and end indices
        idx_start = dates.index(plot_start_date)
        idx_end = dates.index(plot_end_date)

        #Append to data
        data_annot.append(['-' if i == 0 or np.isnan(i) == True else str(i) for i in cases[key][plot_type][idx_start:idx_end+1]])
        data.append(cases[key][plot_type][idx_start:idx_end+1])

        #Append location to row
        name = key.upper() if key in ['uk','us'] else key.title()
        rows.append(name)

    #Add column and row labels
    columns = [i.strftime('%b\n%d') for i in dates][idx_start:idx_end+1]

    #Add total?
    if plot_total == True:
        data_annot.insert(0,['-' if i == 0 or np.isnan(i) == True else str(int(i)) for i in total_count][idx_start:idx_end+1])
        data.insert(0,[0 if np.isnan(i) == True else int(i) for i in total_count][idx_start:idx_end+1])
        rows.insert(0,"World Total")

    #Create data colortable
    max_val = 0.0
    for line in data:
            max_val = line[-1] if line[-1] > max_val else max_val
    if max_val < 40: max_val = 40

    color_obj = Gradient([['#EEEEEE',0.0],['#EEEEEE',0.9]],
                         [['#FFFF00',0.9],['#EE7B51',int(max_val*0.08)]],
                         [['#EE7B51',int(max_val*0.08)],['#B53079',int(max_val*0.3)]],
                         [['#B53079',int(max_val*0.3)],['#070092',int(max_val*0.7)]],
                         [['#070092',int(max_val*0.7)],['#000000',int(max_val*1.2)]])

    #Retrieve colormap
    clevs = np.append(np.array([0,0.95,1.0]),np.arange(2,max_val,1))
    cmap = color_obj.get_cmap(clevs)

    #Determine figure width
    mval = np.nanmax(data)
    if mval > 100000:
        fig_width = return_val(start_range=27, end_range=92, start_size=29, end_size=98, val=len(columns))
    elif mval > 10000:
        fig_width = return_val(start_range=27, end_range=92, start_size=24, end_size=80, val=len(columns))
    elif mval > 1000:
        fig_width = return_val(start_range=21, end_range=40, start_size=17.5, end_size=30, val=len(columns))
    else:
        fig_width = return_val(start_range=27, end_range=92, start_size=12, end_size=41, val=len(columns))
    if fig_width < 14: fig_width = 14

    #Create figure
    fig,ax = plt.subplots(figsize=(fig_width,16),dpi=150) #32,2

    #Reformat data into Pandas DataFrame
    data_df = pd.DataFrame(data,index=rows,columns=columns)

    #Plot seaborn heatmap
    ax = sns.heatmap(data_df, xticklabels=True, yticklabels=True, cmap=cmap, linewidths=0.5,
                     cbar_kws = dict(use_gridspec=False,location="bottom",fraction=0.05, pad=0.008),
                     annot_kws = dict(fontsize=12), annot=np.array(data_annot), fmt = '')

    #Format ticks
    ax.tick_params(right=True, top=True, labelright=True, labeltop=True,
                   bottom=False, labelbottom=False)
    ax.set_yticklabels(labels=rows, rotation=360)

    #Separate line for plotting total
    if plot_total == True:
        ax.hlines([1], *ax.get_xlim())

    #Change y-limits
    bottom, top = ax.get_ylim()
    ax.set_ylim(bottom + 0.5,0)

    #Plot title
    title_string = {
        'confirmed':'Cumulative COVID-19 Confirmed Cases',
        'deaths':'Cumulative COVID-19 Deaths',
        'recovered':'Cumulative COVID-19 Recovered Cases',
        'active':'Daily COVID-19 Active Cases',
        'daily':'Daily COVID-19 New Cases',
    }
    add_title = "(Non-Mainland China)" if mainland_china == False else ""
    plt.title(f"{title_string.get(plot_type)} {add_title}",fontweight='bold',loc='left',fontsize=16, pad=50)
    plt.title(f"Data from Johns Hopkins CSSE\nPlot made by Stephen Mullens @srmullens\nOriginal code from Tomer Burg @burgwx",loc='right',fontsize=11,color='blue')

    #Show plot and close
    if save_image['setting'] == True:
        savepath = os.path.join(save_image['directory_path'],f"{plot_type}_world_table.png")
        plt.savefig(savepath,bbox_inches='tight')
    else:
        plt.show()
    plt.close()

    #Alert script is done
    print("Done!")

if __name__ == "__main__":
        plot_table()
