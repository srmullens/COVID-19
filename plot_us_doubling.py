#Import packages & other scripts
import os, sys
import requests
import numpy as np
import pandas as pd
import datetime as dt
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.legend_handler import HandlerLine2D, HandlerTuple

import read_data

def plot_chart(plot_type=None):
    #========================================================================================================
    # User-defined settings
    #========================================================================================================

    #Whether to save image or display. "directory_path" string is ignored if setting==False.
    save_image = {'setting': True,
                  'directory_path': "full_directory_path_here"}

    #What to plot (confirmed, confirmed_normalized, deaths, recovered, active, daily)
    if plot_type==None:
        plot_type = "active"

    #Include repatriated cases (e.g., cruises)?
    include_repatriated = False

    #Plot total numbers?
    plot_total = True

    #Over how many days should the doubling rate be calculated?
    lag_days = 7

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

    #Z-Order:
    # 2-highlighted trend
    # 3-total trend
    # 4-highlighted state dot
    # 5-total dot
    # 6-state dots

    repatriated_locations = ['diamond princess',
                             'grand princess']

    """
    COVID-19 case data is retrieved from Johns Hopkins CSSE:
    https://github.com/CSSEGISandData/COVID-19
    """
    abbr_state = read_data.abbr_state()
    state_abbr = {v: k for k, v in abbr_state.items()}

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
    max_value = 0; max_doubling = -6; min_doubling = 6
    lag_index = -lag_days - 1
    highlighted_series = []

    #Create figure
    fig,ax = plt.subplots(figsize=(9,6),dpi=125)

    #Total count
    total_count = np.array([0.0 for i in cases['diamond princess']['date']])
    total_count_rp = np.array([0.0 for i in cases['diamond princess']['date']])

    #Iterate through every region
    sorted_keys = [y[1] for y in sorted([(np.nanmax(cases[x][plot_type]), x) for x in cases.keys()])][::-1]
    sorted_value = [y[0] for y in sorted([(np.nanmax(cases[x][plot_type]), x) for x in cases.keys()])][::-1]
    for idx,(key,value) in enumerate(zip(sorted_keys,sorted_value)):

        end_day = cases[key][plot_type][-1]
        start_day = cases[key][plot_type][lag_index]
        day_after_start = cases[key][plot_type][lag_index+1]

        doubling_time = 999; inverse_doubling_time = 999

        if end_day>1:
            if start_day>0 and end_day!=start_day and start_day!=day_after_start:
                doubling_time = lag_days * np.log(2) / np.log(end_day/start_day)
                inverse_doubling_time = 1 / doubling_time

        #Special handling for Diamond Princess
        if include_repatriated == False and key in repatriated_locations: continue

        #Total count
        if key not in repatriated_locations:
            total_count += np.array(cases[key][plot_type])
        total_count_rp += np.array(cases[key][plot_type])

        #Plot states, including highlighted state if applicable.
        if inverse_doubling_time != 999:
            # Plot highlighted state
            if 'highlight_state' in settings.keys() and settings['highlight_state'].lower() == key.lower():
                highlight_color = 'red'
                highlight_key = f"{key.title()}"
                highlight_doubling = f"{doubling_time:.1f}"
                highlight_total = f"{end_day}"
                kwargs = {'zorder':4,
                        'color':highlight_color
                        }
                ax.scatter(inverse_doubling_time,end_day,**kwargs)
                highlighted_series = cases[key][plot_type]
            # Plot rest of states
            else:
                country_text_color = 'k'
                ST = state_abbr.get(key.title())
                if(ST==None): print(key.title(),ST)
                kwargs = {'zorder':6,
                        'color':country_text_color,
                        'ha':'center',
                        'va':'center',
                        'family':'monospace',
                        'fontsize':8
                        }
                ax.text(inverse_doubling_time,end_day,ST,**kwargs)

            #Output stats to terminal
            print(f"{key.title()}\t{start_day}->{end_day}\t{doubling_time:.2f}")

            #Store values useful for the plot axes.
            max_value = max(max_value,end_day)
            max_doubling = max(max_doubling,inverse_doubling_time)
            min_doubling = min(min_doubling,inverse_doubling_time)


    print(f"\nRange: {1/min_doubling:.2f} to {1/max_doubling:.2f} days")


    #Calculate highlighted state running doubling time
    if 'highlight_state' in settings.keys():
        highlighted_series_doubling_time = []
        length_hs = len(highlighted_series)-lag_days

        for i in range(length_hs):
            if highlighted_series[i+lag_days] > 100 and highlighted_series[i]>0:
                highlighted_series_doubling_time.append(1/(lag_days * np.log(2) / np.log(highlighted_series[i+lag_days]/highlighted_series[i])))

        #Plot line of highlighted series doubling time history
        if len(highlighted_series_doubling_time)>6:
            kwargs = {'zorder':2,
                    'color':highlight_color,
                    'lw':1,
                    'markevery':[-7],
                    'ms':2
                    }
            plt.plot(highlighted_series_doubling_time,highlighted_series[-len(highlighted_series_doubling_time):],'-o',**kwargs)
            hc_7 = True
        elif len(highlighted_series_doubling_time)>1:
            kwargs = {'zorder':2,
                    'color':highlight_color,
                    'lw':1
                    }
            plt.plot(highlighted_series_doubling_time,highlighted_series[-len(highlighted_series_doubling_time):],**kwargs)
            hc_7 = False
        else:
            hc_7 = False

    #Calculate US running doubling time
    length = len(total_count)-lag_days
    total_running_doubling_time = []; total_rp_running_doubling_time = []

    for i in range(length):
        if total_count[i+lag_days] > 100:
            total_running_doubling_time.append(1/(lag_days * np.log(2) / np.log(total_count[i+lag_days]/total_count[i])))
            total_rp_running_doubling_time.append(1/(lag_days * np.log(2) / np.log(total_count_rp[i+lag_days]/total_count_rp[i])))

    #Plot total count
    if plot_total == True:
        total_doubling_time = lag_days*np.log(2)/np.log(total_count[-1]/total_count[lag_index])
        total_inverse_doubling_time = 1/total_doubling_time

        total_color = 'k'
        total_doubling_title = f"{total_doubling_time:.1f}"
        total_count_title = f"{int(total_count[-1])}"
        kwargs = {'zorder':5,
                'color':total_color
                }
        plt.scatter(total_inverse_doubling_time,total_count[-1],**kwargs)

        kwargs = {'zorder':3,
                'lw':1,
                'color':total_color,
                'markevery':[-7],
                'ms':2
                }
        plt.plot(total_running_doubling_time,total_count[-len(total_running_doubling_time):],"-o",**kwargs)

        #Store values useful for the plot.
        max_value = max(max_value,total_count[-1])
        max_doubling = max(max_doubling,1/(1*np.log(2)/np.log(total_count[-1]/total_count[-2])))
        min_doubling = min(min_doubling,1/(1*np.log(2)/np.log(total_count[-1]/total_count[-2])))


    #Plot grid and legend
    plt.grid()
    legend_title = f"Calculated from change\nbetween {cases[key]['date'][lag_index]:%b %d} and {cases[key]['date'][-1]:%b %d}"

    #Blank entry for legend.
    if 'highlight_state' in settings.keys():
        plt.plot([],[],'-o',color=highlight_color,label=f"{highlight_key} & trend after 100 cases\n     Time-{highlight_doubling} days, Total-{highlight_total}")
    if plot_total == True:
        plt.plot([],[],'-o',label=f'US Total & trend\n     Time-{total_doubling_title} days, Total-{int(total_count_title)}',color=total_color)
    ax.scatter([],[],color='white',label="Abbreviated States & Territories")

    dot_l = False
    if 'highlight_state' in settings.keys() and hc_7==True:
        p_hc = plt.scatter([],[], color=highlight_color, s=2)
        if plot_total == True:
            p_tc = plt.scatter([],[],color=total_color, s=2)
            #print("hc,tc")
            dot_h = [(p_hc,p_tc)]
            dot_l = ["Small dots were 7 days ago"]

        else:
            #print("hc")
            dot_h = [(p_hc)]
            dot_l = ["Small dot was 7 days ago"]
    else:
        if plot_total == True:
            p_tc = plt.scatter([],[],color=total_color, s=2)
            #print("tc")
            dot_h = [(p_tc)]
            dot_l = ["Small dot was 7 days ago"]

    handles, labels = ax.get_legend_handles_labels()

    if dot_l:
        handles = handles + dot_h
        labels = labels + dot_l

    kwargs = {'loc':2,
            'prop':{'size':8}
            }
    if plot_type=='deaths': kwargs['loc']=1
    plt.legend(handles,labels,title=legend_title,handler_map={tuple: HandlerTuple(ndivide=None)},**kwargs).set_zorder(51)


    #Format x-ticks
    xticks = [1/-0.5,1/-1,1/-2,1/-3,1/-4,1/-5,1/-6,1/-7,0,1/7,1/6,1/5,1/4,1/3,1/2,1/1,1/0.5]
    xtick_labels = [
                "Halving\nEvery\nHalf-day",
                "Halving\nEvery\nDay",
                "Halving\nEvery\n2 Days",
                "Halving\nEvery\n3 Days",
                "Halving\nEvery\n4 Days",
                "Halving\nEvery\n5 Days",
                "Halving\nEvery\n6 Days",
                "Halving\nEvery\nWeek",
                "no\nchange",
                "Doubling\nEvery\nWeek",
                "Doubling\nEvery\n6 Days",
                "Doubling\nEvery\n5 Days",
                "Doubling\nEvery\n4 Days",
                "Doubling\nEvery\n3 Days",
                "Doubling\nEvery\n2 Days",
                "Doubling\nEvery\nDay",
                "Doubling\nEvery\nHalf-day"
            ]

    #Format x-axis
    if np.absolute(max_doubling) > np.absolute(min_doubling):
        left = -max_doubling-0.1; right = max_doubling+0.1
    else: left = min_doubling-0.1; right = -min_doubling+0.1
    if plot_type!='active': left=0

    if right<0.333 or (left==0 and right<0.5):
        xticks = xticks[:5]+xticks[7:10]+xticks[12:]
        xtick_labels = xtick_labels[:5]+xtick_labels[7:10]+xtick_labels[12:]
    elif right<0.5 or (left==0 and right<1):
        xticks = xticks[:4]+xticks[7:10]+xticks[13:]
        xtick_labels = xtick_labels[:4]+xtick_labels[7:10]+xtick_labels[13:]
    elif right<1 or (left==0 and right<2):
        xticks = xticks[:3]+xticks[7:10]+xticks[14:]
        xtick_labels = xtick_labels[:3]+xtick_labels[7:10]+xtick_labels[14:]
    elif right<2 or (left==0 and right>=2):
        xticks = xticks[:3]+xticks[7:10]+xticks[14:]
        xtick_labels = xtick_labels[:3]+[xtick_labels[7],"",xtick_labels[9]]+xtick_labels[14:]
    else:
        xticks = xticks[:3]+xticks[8]+xticks[6:]
        xtick_labels = xtick_labels[:3]+[""]+xtick_labels[6:]

    ax.set_xticks(xticks)
    ax.set_xticklabels(xtick_labels)
    plt.xlim(left,right)


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



    #Plot title
    title_string = {
        'confirmed':'Doubling Time of Cumulative COVID-19 Confirmed Cases',
        'deaths':'Doubling Time of Cumulative COVID-19 Deaths',
        'recovered':'Doubling Time of Cumulative COVID-19 Recovered Cases',
        'active':'Doubling Time of Daily COVID-19 Active Cases',
        'daily':'Doubling Time of Daily COVID-19 New Cases',
    }
    add_title = "\n(Non-Repatriated Cases)" if include_repatriated == False else ""
    plt.title(f"{title_string.get(plot_type)} {add_title}",fontweight='bold',loc='left')
    if left==0:
        xlabel_text = "<--slower increase\t\t\tfaster increase-->".expandtabs()
    else:
        xlabel_text = "<--faster decrease\t\t\tfaster increase-->".expandtabs()
    plt.xlabel(xlabel_text,fontweight='bold')
    plt.ylabel("Number of Cases",fontweight='bold')



    #Plot attribution
    plt.title(f'Data from Johns Hopkins CSSE\nPlot by Stephen Mullens @srmullens\nCode adapted from Tomer Burg @burgwx',loc='right',fontsize=6)

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
        savepath = os.path.join(save_image['directory_path'],f"{plot_type}_doubling_us.png")
        plt.savefig(savepath,bbox_inches='tight')
    else:
        plt.show()

    plt.close()

    #Alert script is done
    print("Done!")

if __name__ == "__main__":
        plot_chart()
