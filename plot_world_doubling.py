#Import packages & other scripts
import os, sys
import requests
import numpy as np
import pandas as pd
import datetime as dt
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.legend_handler import HandlerLine2D, HandlerTuple
from operator import itemgetter

import read_data

def plot_chart(plot_type):
    #========================================================================================================
    # User-defined settings
    #========================================================================================================

    #Whether to save image or display. "directory_path" string is ignored if setting==False.
    save_image = {'setting': True,
                  'directory_path': "full_directory_path_here"}

    #What to plot (confirmed, confirmed_normalized, deaths, recovered, active, daily)
    if plot_type==None:
        plot_type = "deaths"

    #Include Mainland China?
    mainland_china = True

    #Plot total numbers?
    plot_total = True

    #Over how many days should the doubling rate be calculated?
    lag_days = 7

    #Additional settings
    settings = {
        'log_y': True, #Use logarithmic y-axis?
        'condensed_plot': True, #Condensed plot? (small dots and narrow lines)
        'highlight_country': 'us', #Highlight country?
        'number_of_countries': 20, #Limit number of countries plotted?
    }



    #========================================================================================================
    # Get COVID-19 case data
    #========================================================================================================

    #Z-Order:
    # 2-highlighted trend
    # 3-total trends
    # 4-country dots
    # 5-highlighted country dot
    # 6-total dots

    """
    COVID-19 case data is retrieved from Johns Hopkins CSSE:
    https://github.com/CSSEGISandData/COVID-19
    """

    #Avoid re-reading case data if it's already stored in memory

    try:
        cases
    except:
        print("--> Reading in COVID-19 case data from Johns Hopkins CSSE")
        output = read_data.read_world()
        dates = output['dates']
        cases = output['cases']

    #========================================================================================================
    # Create plot based on type
    #========================================================================================================
    max_value = 0; max_doubling = -6; min_doubling = 6
    lag_index = -lag_days - 1
    highlighted_series = []
    top_rates = [{'rate':-20}]*5
    top_cases = [{'cases':0}]*5
    country_text_color = 'k'

    #Create figure
    fig,ax = plt.subplots(figsize=(9,6),dpi=125)

    #Total count
    total_count = np.array([0.0 for i in cases['mainland china']['date']])
    total_count_raw = np.array([0.0 for i in cases['mainland china']['date']])

    #Iterate through every region
    sorted_keys = [y[1] for y in sorted([(np.nanmax(cases[x][plot_type]), x) for x in cases.keys()])][::-1]
    sorted_value = [y[0] for y in sorted([(np.nanmax(cases[x][plot_type]), x) for x in cases.keys()])][::-1]

    for idx,(key,value) in enumerate(zip(sorted_keys,sorted_value)):

        end_day = cases[key][plot_type][-1]
        start_day = cases[key][plot_type][lag_index]
        day_after_start = cases[key][plot_type][lag_index+1]

        doubling_rate = 999; inverse_doubling_rate = 999

        if end_day>1:
            if start_day>0 and end_day!=start_day and start_day!=day_after_start:
                doubling_rate = lag_days * np.log(2) / np.log(end_day/start_day)
                inverse_doubling_rate = 1 / doubling_rate

        #Special handling for China
        if mainland_china == False and key == 'mainland china': continue

        #Total count
        if key != 'mainland china':
            total_count_raw += np.array(cases[key][plot_type])
        total_count += np.array(cases[key][plot_type])

        #Plot countries, including highlighted country if applicable.
        if inverse_doubling_rate != 999:
            if 'highlight_country' in settings.keys() and settings['highlight_country'].lower() == key.lower():

                highlight_color = 'red'
                highlight_key = f"{key.title()}"
                if key.lower() == 'us' or key.lower() == 'uk':
                    highlight_key = f"{key.title().upper()}"
                highlight_doubling = f"{doubling_rate:.1f}"
                highlight_total = f"{end_day}"

                kwargs = {'zorder':5,
                        'color':highlight_color
                        }
                ax.scatter(inverse_doubling_rate,end_day,**kwargs)
                highlighted_series = cases[key][plot_type]
            else:
                country_color = 'gray'
                kwargs = {'zorder':6,
                        'color':country_color
                }
                ax.scatter(inverse_doubling_rate,end_day,**kwargs)

            # Gather countries with top 5 cases
            if end_day>top_cases[-1]['cases']:
                label = {
                        'rate':inverse_doubling_rate,
                        'cases':end_day,
                        'name':' '+key.title()
                }
                if label['name']==' Us' or label['name']==' Uk':
                    label['name']=label['name'].upper()
                top_cases.insert(0,label)
                top_cases.pop(-1)
                if len([i for i in top_cases if i['cases']==0])==0:
                    top_cases = sorted(top_cases, key=itemgetter('cases'),reverse=True)

            # Gather countries with top 5 doubling rates
            if inverse_doubling_rate>top_rates[-1]['rate']:
                label = {
                        'rate':inverse_doubling_rate,
                        'cases':end_day,
                        'name':' '+key.title()
                }
                if label['name']==' Us' or label['name']==' Uk':
                    label['name']=label['name'].upper()
                top_rates.insert(0,label)
                top_rates.pop(-1)
                if len([i for i in top_rates if i['rate']==0])==0:
                    top_rates = sorted(top_rates, key=itemgetter('rate'),reverse=True)

            #Label countries reducing totals
            if plot_type=='active' and doubling_rate <= 0:
                name = key.title()+" "
                kwargs = {'zorder':7,
                        'color':country_text_color,
                        'ha':'right',
                        'va':'center',
                        'family':'monospace',
                        'fontsize':6
                }
                ax.text(inverse_doubling_rate,end_day,name,**kwargs)

            #Output stats to terminal
            print(f"{key.title()}\t{start_day}->{end_day}\t{doubling_rate:.2f}")

            #Store values useful for the plot axes.
            max_value = max(max_value,end_day)
            max_doubling = max(max_doubling,inverse_doubling_rate)
            min_doubling = min(min_doubling,inverse_doubling_rate)


    #Label countries with top 5 cases
    for case in top_cases: print(case)
    kwargs = {'zorder':7,
            'color':country_text_color,
            'ha':'left',
            'va':'center',
            'family':'monospace',
            'fontsize':6
    }
    for i in range(len(top_cases)):
        plt.text(top_cases[i]['rate'],top_cases[i]['cases'],top_cases[i]['name'],**kwargs)

    #Label countries with top 5 doubling rates
    for rate in top_rates: print(rate)
    for i in range(len(top_rates)):
        plt.text(top_rates[i]['rate'],top_rates[i]['cases'],top_rates[i]['name'],**kwargs)

    print(f"\nRange: {1/min_doubling:.2f} to {1/max_doubling:.2f} days")


    #Calculate highlighted country running doubling rate
    if 'highlight_country' in settings.keys():
        highlighted_series_doubling_rate = []
        length_hs = len(highlighted_series)-lag_days

        for i in range(length_hs):
            if highlighted_series[i+lag_days] > 100 and highlighted_series[i]>0:
                highlighted_series_doubling_rate.append(1/(lag_days * np.log(2) / np.log(highlighted_series[i+lag_days]/highlighted_series[i])))

        #Plot line of highlighted series doubling rate history
        if len(highlighted_series_doubling_rate)>6:
            kwargs = {'zorder':2,
                    'color':highlight_color,
                    'lw':1,
                    'markevery':[-7],
                    'ms':2
                    }
            plt.plot(highlighted_series_doubling_rate,highlighted_series[-len(highlighted_series_doubling_rate):],'-o',**kwargs)
            hc_7 = True
        elif len(highlighted_series_doubling_rate)>1:
            kwargs = {'zorder':2,
                    'color':highlight_color,
                    'lw':1
                    }
            plt.plot(highlighted_series_doubling_rate,highlighted_series[-len(highlighted_series_doubling_rate):],**kwargs)
            hc_7 = False
        else:
            hc_7 = False


    #Calculate world running doubling rate
    length = len(total_count)-lag_days
    total_running_doubling_rate = []; total_raw_running_doubling_rate = []

    for i in range(length):
        if total_count_raw[i+lag_days] > 100:
            total_raw_running_doubling_rate.append(1/(lag_days * np.log(2) / np.log(total_count_raw[i+lag_days]/total_count_raw[i])))
            if mainland_china == True:
                total_running_doubling_rate.append(1/(lag_days * np.log(2) / np.log(total_count[i+lag_days]/total_count[i])))

    #Plot total count
    if plot_total == True:
        total_raw_doubling_rate = lag_days*np.log(2)/np.log(total_count_raw[-1]/total_count_raw[lag_index])
        total_raw_inverse_doubling_rate = 1/total_raw_doubling_rate

        total_raw_color = 'b'
        total_raw_doubling_title = f"{total_raw_doubling_rate:.1f}"
        total_raw_count_title = f"{int(total_count_raw[-1])}"
        kwargs = {'zorder':6,
                'color':total_raw_color
                }
        plt.scatter(total_raw_inverse_doubling_rate,total_count_raw[-1],**kwargs)

        kwargs = {'zorder':3,
                'lw':1,
                'color':total_raw_color,
                'markevery':[-7],
                'ms':2
                }
        plt.plot(total_raw_running_doubling_rate,total_count_raw[-len(total_raw_running_doubling_rate):],"-o",**kwargs)

        if mainland_china == True:
            total_doubling_rate = lag_days*np.log(2)/np.log(total_count[-1]/total_count[lag_index])
            total_inverse_doubling_rate = 1/total_doubling_rate

            total_color = 'k'
            total_doubling_title = f"{total_doubling_rate:.1f}"
            total_count_title = f"{int(total_count[-1])}"
            kwargs = {'zorder':6,
                'color':total_color
                }
            plt.scatter(total_inverse_doubling_rate,total_count[-1],**kwargs)

            kwargs = {'zorder':3,
                'lw':1,
                'color':total_color,
                'markevery':[-7],
                'ms':2
                }
            plt.plot(total_running_doubling_rate,total_count[-len(total_running_doubling_rate):],":o",**kwargs)

        #Store values useful for the plot.
        max_value = max(max_value,total_count[-1])
        max_doubling = max(max_doubling,1/(1*np.log(2)/np.log(total_count[-1]/total_count[-2])))
        min_doubling = min(min_doubling,1/(1*np.log(2)/np.log(total_count[-1]/total_count[-2])))


    #Plot grid and legend
    plt.grid()
    legend_title = f"Calculated from change\nbetween {cases[key]['date'][lag_index]:%b %d} and {cases[key]['date'][-1]:%b %d}"

    #Blank entries for legend.
    if 'highlight_country' in settings.keys():
        plt.plot([],[],'-o',color=highlight_color,label=f"{highlight_key} & trend after 100 cases\n     Time-{highlight_doubling} days, Total-{highlight_total}")
    if plot_total == True:
        plt.plot([],[],'-o',label=f'World Total (no China) & trend\n     Time-{total_raw_doubling_title} days, Total-{int(total_raw_count_title)}',color=total_raw_color)
        if mainland_china == True:
            plt.plot([],[],':o',label=f'World Total & trend\n     Time-{total_doubling_title} days, Total-{int(total_count_title)}',color=total_color)
    plt.scatter(np.nan,np.nan,color=country_color,label="Countries")

    dot_l = False
    if 'highlight_country' in settings.keys() and hc_7==True:
        p_hc = plt.scatter([],[], color=highlight_color, s=2)
        if plot_total == True:
            p_tc = plt.scatter([],[],color=total_color, s=2)
            if mainland_china == True:
                #print("hc,tc,mc")
                p_tc_raw = plt.scatter([],[], color=total_raw_color, s=2)
                dot_h = [(p_hc,p_tc_raw,p_tc)]
                dot_l = ["Small dots were 7 days ago"]
            else:
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
            if mainland_china == True:
                #print("tc,mc")
                p_tc_raw = plt.scatter([],[],color=total_raw_color, s=2)
                dot_h = [(p_tc_raw,p_tc)]
                dot_l = ["Small dots were 7 days ago"]
            else:
                #print("tc")
                dot_h = [(p_tc)]
                dot_l = ["Small dots were 7 days ago"]

    handles, labels = ax.get_legend_handles_labels()

    if dot_l:
        handles = handles + dot_h
        labels = labels + dot_l

    kwargs = {'loc':2,
            'prop':{'size':8}
            }
    if plot_type!='active': kwargs['loc']=1
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
    if plot_type!="active": left=0

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


    #Plot death comparisons from historic plagues
    if plot_type=="deaths":
        historic_deaths = read_data.historic_deaths()
        for pandemic in historic_deaths:
            deaths = pandemic['deaths']
            name = pandemic['name']
            years = pandemic['year']
            death_label = pandemic['label']
            kwargs = {'fontsize':5,
                    'family':'monospace',
                    'color':'red',
                    'ha':'left',
                    'va':'center',
                    'clip_on':True
                    }
            if deaths==850 or deaths==1100000: kwargs['va']='bottom'
            label_text = f" {death_label}-{name}"
            plt.text(0,deaths,label_text,**kwargs)



    #Plot titles
    title_string = {
        'confirmed':'Doubling Time of Cumulative COVID-19 Confirmed Cases',
        'deaths':'Doubling Time of Cumulative COVID-19 Deaths',
        'recovered':'Doubling Time of Cumulative COVID-19 Recovered Cases',
        'active':'Doubling Time of Daily COVID-19 Active Cases',
        'daily':'Doubling Time of Daily COVID-19 New Cases',
    }
    add_title = "\n(Non-Mainland China)" if mainland_china == False else ""
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
        kwargs = {'fontweight':'bold',
                'fontsize':8,
                'ha':'right',
                'va':'top'
                }
        active_text = "\"Active\" cases = confirmed total - recovered - deaths"
        plt.text(0.99,0.99,active_text,transform=ax.transAxes,**kwargs)

    if plot_type == 'deaths':
        kwargs = {'fontsize':5,
                'ha':'left',
                'va':'bottom'}
        deaths_text_short = " Historic pandemic data\n "
        deaths_text = "\t\t\t\t\tis from: https://www.visualcapitalist.com/history-of-pandemics-deadliest/\n Deaths totals are often under debate. COVID-19 death totals are likely underestimates.".expandtabs()
        plt.text(0,0.01,deaths_text,transform=ax.transAxes,**kwargs)
        kwargs['color']='red'
        plt.text(0,0.01,deaths_text_short,transform=ax.transAxes,**kwargs)

    #Show plot and close
    if save_image['setting'] == True:
        savepath = os.path.join(save_image['directory_path'],f"{plot_type}_doubling_world.png")
        plt.savefig(savepath,bbox_inches='tight')
    else:
        plt.show()

    plt.close()

    #Alert script is done
    print("Done!")

if __name__ == "__main__":
        plot_chart()
