#Import packas
import os, sys
import requests
import numpy as np
import pandas as pd
import datetime as dt
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

import read_data

def plot_chart(plot_type=None):
    #========================================================================================================
    # User-defined settings
    #========================================================================================================

    #Whether to save image or display. "directory_path" string is ignored if setting==False.
    save_image = {'setting': True,
                  'directory_path': "/Users/Steve/Desktop/UFlorida/3-Code/COVID/COVID-19"}

    #What to plot (confirmed, deaths, recovered, active, daily)
    if plot_type==None:
        plot_type = "active"

    #Include repatriated cases (e.g., cruises)?
    include_repatriated = False

    #Plot total numbers?
    plot_total = True

    #Additional settings
    settings = {
        'log_y': True, #Use logarithmic y-axis?
        'condensed_plot': True, #Condensed plot? (small dots and narrow lines)
        'highlight_state': 'New York', #Highlight state?
        'number_of_state': 20, #Limit number of states plotted?
    }

    #========================================================================================================
    # Get COVID-19 case data
    #========================================================================================================

    repatriated_locations = ['diamond princess',
                             'grand princess']

    """
    COVID-19 case data is retrieved from Johns Hopkins CSSE:
    https://github.com/CSSEGISandData/COVID-19
    """

    #Avoid re-reading case data if it's already stored in memory
    try:
        cases
    except:
        print("--> Reading in COVID-19 case data from Johns Hopkins CSSE")

        output = read_data.read_us()
        dates = output['dates']
        cases = output['cases']

    #========================================================================================================
    # Create plot based on type
    #========================================================================================================
    max_value = 0

    #Create figure
    fig,ax = plt.subplots(figsize=(9,6),dpi=125)

    #Total count
    total_count = np.array([0.0 for i in cases['diamond princess']['date']])
    total_count_rp = np.array([0.0 for i in cases['diamond princess']['date']])

    #Iterate through every region
    sorted_keys = [y[1] for y in sorted([(np.nanmax(cases[x][plot_type]), x) for x in cases.keys()])][::-1]
    sorted_value = [y[0] for y in sorted([(np.nanmax(cases[x][plot_type]), x) for x in cases.keys()])][::-1]
    for idx,(key,value) in enumerate(zip(sorted_keys,sorted_value)):

        #Special handling for Diamond Princess
        if include_repatriated == False and key in repatriated_locations: continue

        #Total count
        if key not in repatriated_locations: total_count += np.array(cases[key][plot_type])
        total_count_rp += np.array(cases[key][plot_type])

        #Skip plotting if zero
        if value == 0: continue

        #How many states to plot?
        lim = 19
        if 'number_of_states' in settings.keys():
            lim = settings['number_of_states'] - 1
        if lim > 19: lim = 19

        #Plot type
        if idx > 19:
            pass
        else:
            mtype = '--'; zord=2
            if np.nanmax(cases[key][plot_type]) > np.percentile(sorted_value,95): mtype = '-o'; zord=3
            zord = 22 - idx

            #Handle narrow plot
            kwargs = {
                'linewidth':1.0,
                'zorder':zord,
                'label':f"{key.title()} ({cases[key][plot_type][-1]})"
            }
            if 'condensed_plot' in settings.keys() and settings['condensed_plot'] == True:
                mtype = '-o'
                kwargs['linewidth']=0.5
                kwargs['ms']=2

            #Highlight individual state
            if 'highlight_state' in settings.keys() and settings['highlight_state'].lower() == key.lower():
                kwargs['linewidth']=2.0
                if 'ms' in kwargs.keys(): kwargs['ms'] = 4

            #Plot lines
            plt.plot(cases[key]['date'],cases[key][plot_type],mtype,**kwargs)

            max_value = max(max_value,max(cases[key][plot_type]))

    #Plot total count
    if plot_total == True:
        kwargs = {
            'zorder':2,
            'label':f'Total ({int(total_count[-1])})',
            'color':'k',
            'linewidth':2
        }
        plt.plot(cases[key]['date'],total_count,':',**kwargs)

        #plt.plot(cases[key]['date'],total_count,':',zorder=2,label=f'Total ({int(total_count[-1])})',color='k',linewidth=2)
        if include_repatriated == True:
            kwargs['label']=f'Total (+ Repatriated)\n({int(total_count_rp[-1])})'
            kwargs['color']='b'
            plt.plot(cases[key]['date'],total_count_rp,':',**kwargs)
            #plt.plot(cases[key]['date'],total_count_rp,':',zorder=2,label=f'Total (+ Repatriated)\n({int(total_count_rp[-1])})',color='b',linewidth=2)
        max_value = max(max_value,max(total_count))

    #Format x-ticks
    ax.set_xticks(cases[key]['date'][::7])
    ax.set_xticklabels(cases[key]['date'][::7])
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%b\n%d'))

    #Plot grid and legend
    plt.grid()
    kwargs = {
        'loc':2,
        'title':f"Top {lim+1} locations plotted",
        'prop':{'size':8}
        }
    plt.legend(**kwargs).set_zorder(51)
    #plt.legend(loc=2,prop={'size':8},title=f"Top {lim+1} locations plotted")

    #Plot title
    title_string = {
        'confirmed':'Cumulative COVID-19 Confirmed Cases',
        'deaths':'Cumulative COVID-19 Deaths',
        'recovered':'Cumulative COVID-19 Recovered Cases',
        'active':'Daily COVID-19 Active Cases',
        'daily':'Daily COVID-19 New Cases',
    }
    add_title = "\n(Non-Repatriated Cases)" if include_repatriated == False else ""
    plt.title(f"{title_string.get(plot_type)} {add_title}",fontweight='bold',loc='left')
    plt.xlabel("Date",fontweight='bold')
    plt.ylabel("Cases",fontweight='bold')

    #Add logarithmic y-scale
    if 'log_y' in settings.keys() and settings['log_y'] == True:
        plt.yscale('log')

        y_locs, y_labels = plt.yticks()
        for i,loc in enumerate(y_locs):
            if loc == 1.e+00: y_labels[i] = "1"
            elif loc == 1.e+01: y_labels[i] = "10"
            elif loc == 1.e+02: y_labels[i] = "100"
            elif loc == 1.e+03: y_labels[i] = "1K"
            elif loc == 1.e+04: y_labels[i] = "10K"
            elif loc == 1.e+05: y_labels[i] = "100K"
            elif loc == 1.e+06: y_labels[i] = "1M"
            elif loc == 1.e+07: y_labels[i] = "10M"
            elif loc == 1.e+08: y_labels[i] = "100M"
            elif loc == 1.e+09: y_labels[i] = "1B"
            elif loc == 1.e+10: y_labels[i] = "10B"

        plt.yticks(y_locs,y_labels)

        plt.ylim(bottom=1)

        if max_value<10: plt.ylim(top=10)
        elif max_value<100: plt.ylim(top=100)
        elif max_value<1000: plt.ylim(top=1000)  #1K
        elif max_value<10000: plt.ylim(top=10000)
        elif max_value<100000: plt.ylim(top=100000)
        elif max_value<1000000: plt.ylim(top=1000000) #1M
        elif max_value<10000000: plt.ylim(top=10000000)
        elif max_value<100000000: plt.ylim(top=100000000)
        elif max_value<1000000000: plt.ylim(top=1000000000) #1B
        elif max_value<10000000000: plt.ylim(top=10000000000)



    #Plot attribution
    plt.title(f'Data from Johns Hopkins CSSE{add_title}\nPlot by Stephen Mullens @srmullens\nCode adapted from Tomer Burg @burgwx',loc='right',fontsize=8)

    if plot_type == "active":
        kwargs = {
            'fontweight':'bold',
            'ha':'right',
            'va':'top',
            'fontsize':8
        }
        active_text = "\"Active\" cases = confirmed total - recovered - deaths"
        plt.text(0.99,0.99,active_text,transform=ax.transAxes,**kwargs)

    #Show plot and close
    if save_image['setting'] == True:
        savepath = os.path.join(save_image['directory_path'],f"{plot_type}_chart_us.png")
        plt.savefig(savepath,bbox_inches='tight')
    else:
        plt.show()
    plt.close()

    #Alert script is done
    print("Done!")

if __name__ == "__main__":
        plot_chart()
