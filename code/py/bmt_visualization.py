import pandas as pd
from bokeh.io import curdoc
from bokeh.plotting import figure, show
from bokeh.models import ColumnDataSource
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
    def present_data( travel_df ):
        curdoc().theme = "dark_minimal"

        travel_source = ColumnDataSource(travel_df)
        plot = figure(title="Plot responsive sizing example",
                      sizing_mode="stretch_width",
                      height=250,
                      x_axis_label="Timestamp",
                      y_axis_label="Travel",)
        plot.line( x='int_timestamp', y='fork_mm', source=travel_source, legend_label='front', line_width=2)
        plot.line( x='int_timestamp', y='shock_mm', source=travel_source, legend_label='rear', color='green', line_width=2)

        show(plot)


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Visualizes BMT data files.")
    parser.add_argument( "-f", "--file", dest="file", action="store", required=True, help="Path to file to be read." )
    args = parser.parse_args()
    
    df = BmtVisualization.open_travel_information( args.file )

    fork_calibration_data = {'sensor_name':'Dummy fork sensor', 'adc_val_zero': 25, 'adc_val_max': 4095, 'range_mm': 200 }
    shock_calibration_data = {'sensor_name':'Dummy shock sensor', 'adc_val_zero': 26, 'adc_val_max': 4090, 'range_mm': 75 }
    df = BmtCalculations.adc_to_mm(df, fork_calibration_data, shock_calibration_data )
    BmtVisualization.present_data( df )