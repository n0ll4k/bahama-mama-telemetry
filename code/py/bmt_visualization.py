import pandas as pd
import numpy as np
from bokeh.io import curdoc
from bokeh.plotting import figure, show
from bokeh.models import ColumnDataSource
import bokeh.layouts
from bmt_calculations import BmtCalculations



class BmtVisualization:
    @staticmethod
    def open_travel_information( travel_info_path ):
        travel_df = pd.DataFrame()
        try:
            travel_df = pd.read_csv( travel_info_path, index_col=0 )
        except:
            print( "Error reading data file: {}".format(travel_info_path) )

        return travel_df
    
    @staticmethod
    def create_travel_plot( travel_df ):
        travel_source = ColumnDataSource(travel_df)
        travel_plot = figure(title="Plot responsive sizing example",
                      width=1000,
                      height=350,
                      x_axis_label="Timestamp",
                      y_axis_label="Travel",)
        travel_plot.line( x='int_timestamp', y='fork_mm', source=travel_source, legend_label='front', color='steelblue', line_width=2)
        travel_plot.line( x='int_timestamp', y='shock_mm', source=travel_source, legend_label='rear', color='green', line_width=2)
        return travel_plot
    
    @staticmethod 
    def create_travel_histograms( travel_df, damper ):
        hist_plot = figure( width=500, 
                            height=350, 
                            toolbar_location=None )
        if damper == "fork":
            column = "fork_mm"
            name = "Fork"
            color="steelblue"
        elif damper == "shock":
            column = "shock_mm"
            name = "Shock"
            color="green"
        else:
            column = ""
            name = ""
            return hist_plot        
        
        hist, edges = np.histogram(travel_df[column], density=True )
        hist_plot.quad( top=hist, 
                        bottom=0, 
                        left=edges[:-1], 
                        right=edges[1:], 
                        fill_color=color,
                        line_color='gainsboro' )
        hist_plot.y_range.start = 0
        hist_plot.xaxis.axis_label = "Travel"
        hist_plot.title = "{} Histogram".format(name)

        return hist_plot


    @staticmethod
    def present_data( travel_df ):
        curdoc().theme = "dark_minimal"

        travel_plot = BmtVisualization.create_travel_plot( travel_df )

        fork_hist = BmtVisualization.create_travel_histograms( travel_df, "fork" )
        shock_hist = BmtVisualization.create_travel_histograms( travel_df, "shock" )

        layout = bokeh.layouts.layout( [
            [ travel_plot ],
            [ fork_hist, shock_hist ] ] )

        show(layout)


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Visualizes BMT data files.")
    parser.add_argument( "-f", "--file", dest="file", action="store", required=True, help="Path to file to be read." )
    args = parser.parse_args()
    
    df = BmtVisualization.open_travel_information( args.file )

    fork_calibration_data = {'sensor_name':'Dummy fork sensor', 'adc_val_zero': 3, 'adc_val_max': 512, 'range_mm': 200 }
    shock_calibration_data = {'sensor_name':'Dummy shock sensor', 'adc_val_zero': 3, 'adc_val_max': 512, 'range_mm': 75 }
    df = BmtCalculations.adc_to_mm(df, fork_calibration_data, shock_calibration_data )
    BmtVisualization.present_data( df )