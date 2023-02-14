import pandas as pd
import numpy as np
import bokeh.layouts
import xyzservices.providers as xyz
from bokeh.io import curdoc
from bokeh.plotting import figure, show
from bokeh.models import ColumnDataSource
from bmt_calculations import BmtCalculations



class BmtVisualization:
    MAP_DIFF = 500
    @staticmethod
    def open_travel_information( travel_info_path ):
        travel_df = pd.DataFrame()
        try:
            travel_df = pd.read_csv( travel_info_path, index_col=0 )
        except:
            print( "Error reading data file: {}".format(travel_info_path) )

        return travel_df
    
    @staticmethod
    def open_gps_information( gps_info_path ):
        gps_df = pd.DataFrame()
        try:
            gps_df = pd.read_csv( gps_info_path, index_col=0 )
        except:
            print( "Error reading data file: {}".format(gps_info_path) )

        return gps_df
    
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
    def present_data( travel_df, gps_df ):
        curdoc().theme = "dark_minimal"

        travel_plot = BmtVisualization.create_travel_plot( travel_df )

        fork_hist = BmtVisualization.create_travel_histograms( travel_df, "fork" )
        shock_hist = BmtVisualization.create_travel_histograms( travel_df, "shock" )
        map = BmtVisualization.create_map( gps_df )

        layout = bokeh.layouts.layout( [
            [ travel_plot ],
            [ fork_hist, shock_hist ],
            [ map] ] )

        show(layout)
    
    @staticmethod
    def create_map( gps_df ):
        max_x_y = BmtCalculations.nmea0813_to_xy( gps_df['lat'].max(), gps_df['lon'].max())
        min_x_y = BmtCalculations.nmea0813_to_xy( gps_df['lat'].min(), gps_df['lon'].min())
        
        map_x_range = ( (min_x_y[0]-BmtVisualization.MAP_DIFF), (max_x_y[0]+BmtVisualization.MAP_DIFF) )
        map_y_range = ( (min_x_y[1]-BmtVisualization.MAP_DIFF), (max_x_y[1]+BmtVisualization.MAP_DIFF) )
        
        map = figure(title="Map",
                x_axis_label='X [m]',
                y_axis_label='Y [m]',
                match_aspect=True,
                x_range=map_x_range,
                y_range=map_y_range)
        map.add_tile(xyz.OpenStreetMap.Mapnik)

        #TODO Add gps track. Test data needed.

        return map


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Visualizes BMT data files.")
    parser.add_argument( "-t", "--travel", dest="travel_file", action="store", required=True, help="Path to travel information file to be read." )
    parser.add_argument( "-g", "--gps", dest="gps_file", action="store", required=True, help="Path to gps information file to be read." )
    args = parser.parse_args()
    
    fork_calibration_data = {'sensor_name':'Dummy fork sensor', 'adc_val_zero': 512, 'adc_val_max': 3, 'range_mm': 200 }
    shock_calibration_data = {'sensor_name':'Dummy shock sensor', 'adc_val_zero': 512, 'adc_val_max': 3, 'range_mm': 75 }
    gps_df = BmtVisualization.open_gps_information( args.gps_file )
    travel_df = BmtVisualization.open_travel_information( args.travel_file )

    
    df = BmtCalculations.adc_to_mm(travel_df, fork_calibration_data, shock_calibration_data )
    BmtVisualization.present_data( travel_df, gps_df )
