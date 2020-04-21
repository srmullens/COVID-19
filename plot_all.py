#Import packages
import logging
logging.basicConfig(filename='logfile.log',format='%(name)s - %(levelname)s - %(message)s')

print("Import US table")
import plot_us_table
print("Import World table")
import plot_world_table
print("Import US chart")
import plot_us_chart
print("Import World chart")
import plot_world_chart
print("Import US doubling")
import plot_us_doubling
print("Import World doubling")
import plot_world_doubling

plot_types = ['active','deaths','recovered']

for plot_type in plot_types:
    if plot_type!="recovered":
        print(f"--> {plot_type} <--")
        print("*** Run US table ***")
        try: plot_us_table.plot_table(plot_type)
        except Exception as e: logging.exception("Exception occurred")
        print("*** Run World table ***")
        try: plot_world_table.plot_table(plot_type)
        except Exception as e: logging.exception("Exception occurred")
        print("*** Run US chart ***")
        try: plot_us_chart.plot_chart(plot_type)
        except Exception as e: logging.exception("Exception occurred")
        print("*** Run World chart ***")
        try: plot_world_chart.plot_chart(plot_type)
        except Exception as e: logging.exception("Exception occurred")
        print("*** Run US doubling ***")
        try: plot_us_doubling.plot_chart(plot_type)
        except Exception as e: logging.exception("Exception occurred")
        print("*** Run World doubling ***")
        try: plot_world_doubling.plot_chart(plot_type)
        except Exception as e: logging.exception("Exception occurred")
    else:
        print("*** Run World table ***")
        try: plot_world_table.plot_table(plot_type)
        except Exception as e: logging.exception("Exception occurred")
        print("*** Run World chart ***")
        try: plot_world_chart.plot_chart(plot_type)
        except Exception as e: logging.exception("Exception occurred")
        print("*** Run World doubling ***")
        try: plot_world_doubling.plot_chart(plot_type)
        except Exception as e: logging.exception("Exception occurred")
