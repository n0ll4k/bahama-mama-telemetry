import pandas as pd
import numpy as np
import xyzservices.providers as xyz
from bokeh.layouts import row, column, layout, grid
from bokeh.io import curdoc
from bokeh.plotting import figure, show, output_file
from bokeh.models import ColumnDataSource, Slope
from bokeh.models.annotations import Label, Span
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
        travel_plot.line( x='int_timestamp', y='front_axle_mm', source=travel_source, legend_label='front', color='steelblue', line_width=2)
        travel_plot.line( x='int_timestamp', y='rear_axle_mm', source=travel_source, legend_label='rear', color='green', line_width=2)
        return travel_plot
    
    @staticmethod 
    def create_travel_histograms( travel_df, damper ):
        hist_plot = figure( width=500, 
                            height=350, 
                            toolbar_location=None )
        if damper == "fork":
            column = "front_axle_mm"
            name = "Front Axle"
            color="steelblue"
        elif damper == "shock":
            column = "rear_axle_mm"
            name = "Rear Axle"
            color="green"
        else:
            column = ""
            name = ""
            return hist_plot        
        
        avg_travel = (travel_df[column].mean()).round(2)
        avg_txt = "Avg: {}mm".format(avg_travel)

        hist, edges = np.histogram(travel_df[column], bins=20, density=True )
        hist_plot.quad( top=hist, 
                        bottom=0, 
                        left=edges[:-1], 
                        right=edges[1:], 
                        fill_color=color,
                        line_color='gainsboro' )
        span_avg = Span(location=avg_travel, dimension='height', line_color='grey', line_dash='dashed', line_width=1)

        l_heigth = hist.max() - ( 0.05 * hist.max())
        l_avg = Label(x=avg_travel, x_offset=5, y=l_heigth, text=avg_txt, text_color='grey', text_font_size='14px' )
        hist_plot.add_layout(span_avg)
        hist_plot.add_layout(l_avg)
        hist_plot.y_range.start = 0
        hist_plot.xaxis.axis_label = "Travel"
        hist_plot.title = "{} Histogram".format(name)

        return hist_plot
    
    @staticmethod
    def create_velocity_balance( travel_df ):
        # Grab specific data from travel date frame
        front_comp_df = travel_df[travel_df['front_speeds_mm_s'] >= 0]
        front_reb_df = travel_df[travel_df['front_speeds_mm_s'] <= 0] 
        rear_comp_df = travel_df[travel_df['rear_speeds_mm_s'] >= 0]
        rear_reb_df = travel_df[travel_df['rear_speeds_mm_s'] <= 0]

        front_comp_source = ColumnDataSource(front_comp_df)
        rear_comp_source = ColumnDataSource(rear_comp_df)
        front_reb_source = ColumnDataSource(front_reb_df)
        rear_reb_source = ColumnDataSource(rear_reb_df)

        # Create regression lines
        front_comp = np.polyfit( x=front_comp_df['front_percentage'], y=front_comp_df['front_speeds_mm_s'], deg=1, full=True)
        fc_slope=front_comp[0][0]
        fc_intercept=front_comp[0][1]
        rear_comp = np.polyfit( x=rear_comp_df['rear_percentage'], y=rear_comp_df['rear_speeds_mm_s'], deg=1, full=True)
        rc_slope=rear_comp[0][0]
        rc_intercept=rear_comp[0][1]
        front_reb = np.polyfit( x=front_reb_df['front_percentage'], y=front_reb_df['front_speeds_mm_s'], deg=1, full=True)
        fr_slope=front_reb[0][0]
        fr_intercept=front_reb[0][1]
        rear_reb = np.polyfit( x=rear_reb_df['rear_percentage'], y=rear_reb_df['rear_speeds_mm_s'], deg=1, full=True)
        rr_slope=rear_reb[0][0]
        rr_intercept=rear_reb[0][1]

        front_comp_reg_line = Slope(gradient=fc_slope, y_intercept=fc_intercept, line_color="steelblue", line_width=2)
        rear_comp_reg_line = Slope(gradient=rc_slope, y_intercept=rc_intercept, line_color="green", line_width=2)
        front_reb_reg_line = Slope(gradient=fr_slope, y_intercept=fr_intercept, line_color="steelblue", line_width=2)
        rear_reb_reg_line = Slope(gradient=rr_slope, y_intercept=rr_intercept, line_color="green", line_width=2)
        
        # Create figures
        comp_plot = figure( title='Compression velocity balance',
                            width=500, 
                            height=350, 
                            toolbar_location=None )
        reb_plot = figure( title='Rebound velocity balance',
                           width=500, 
                           height=350, 
                           toolbar_location=None )
        reb_plot.y_range.flipped = True

        # Add scatter plots
        comp_plot.circle( x='front_percentage', y='front_speeds_mm_s', source=front_comp_source, size=3, alpha=0.3, color='steelblue' )
        comp_plot.circle( x='rear_percentage', y='rear_speeds_mm_s', source=rear_comp_source, size=3, alpha=0.3, color='green' )
        reb_plot.circle( x='front_percentage', y='front_speeds_mm_s', source=front_reb_source, size=3, alpha=0.3, color='steelblue' )
        reb_plot.circle( x='rear_percentage', y='rear_speeds_mm_s', source=rear_reb_source, size=3, alpha=0.3, color='green' )

        # Add regression lines
        comp_plot.add_layout(front_comp_reg_line)
        comp_plot.add_layout(rear_comp_reg_line)
        reb_plot.add_layout(front_reb_reg_line)
        reb_plot.add_layout(rear_reb_reg_line)

        return comp_plot, reb_plot

                        

    @staticmethod
    def present_data( travel_df, gps_df, export ):
        curdoc().theme = "dark_minimal"

        output_file(filename=export, title="Bahama Mama Telemetrie")    
        travel_plot = BmtVisualization.create_travel_plot( travel_df )

        fork_hist = BmtVisualization.create_travel_histograms( travel_df, "fork" )
        shock_hist = BmtVisualization.create_travel_histograms( travel_df, "shock" )
        map = BmtVisualization.create_map( gps_df )
        comp_vel, reb_vel = BmtVisualization.create_velocity_balance( travel_df )

        histogram_row = row( fork_hist, shock_hist)
        velocity_row = row( comp_vel, reb_vel)
        data_column = column( travel_plot, histogram_row, velocity_row)
        layout = row( data_column, map, sizing_mode="stretch_both")
    
        show(layout)
    
    @staticmethod
    def create_map( gps_df ):
        try:
            # Get Map dimensions
            map_x_range = gps_df['x'].min()-BmtVisualization.MAP_DIFF, gps_df['x'].max()+BmtVisualization.MAP_DIFF
            map_y_range = gps_df['y'].min()-BmtVisualization.MAP_DIFF, gps_df['y'].max()+BmtVisualization.MAP_DIFF
        except:
            map_x_range = (0,0)
            map_y_range = (0,0)
        
        # Load data
        source = ColumnDataSource(gps_df)

        # Create map
        map = figure(title="Map",
                x_axis_label='X [m]',
                y_axis_label='Y [m]',
                match_aspect=True,
                height=700,
                x_range=map_x_range,
                y_range=map_y_range)
        # Add map tile
        map.add_tile(xyz.OpenStreetMap.Mapnik)

        # Add data points
        map.line(x="x", y="y", color="green", alpha=0.8, source=source, line_width=2)

        return map


if __name__ == "__main__":
    import argparse
    import os
    parser = argparse.ArgumentParser(description="Visualizes BMT data files.")
    parser.add_argument( "-t", "--travel", dest="travel_file", action="store", required=True, help="Path to travel information file to be read." )
    parser.add_argument( "-g", "--gps", dest="gps_file", action="store", required=True, help="Path to gps information file to be read." )
    args = parser.parse_args()
    
    travel_df = BmtVisualization.open_travel_information( args.travel_file )
    gps_df = BmtVisualization.open_gps_information( args.gps_file )
    
    export_file = "{}.html".format( os.path.basename(args.gps_file)[:-7])
    export = os.path.abspath( os.path.join(os.path.dirname(args.gps_file), export_file ))

    BmtVisualization.present_data( travel_df, gps_df, export )