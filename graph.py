import pandas as pd
import matplotlib.pyplot as plt

filename = input("Enter filename")
# Load the data into a Pandas DataFrame
data = pd.read_csv(filename, header=None, names=['time', 'value'])

# Drop rows with missing values
data = data.dropna()

# Filter the data to include only the LiveBPM values
live_bpm = data[data['value'].str.startswith('LiveBPM')]

# Check if the live_bpm DataFrame is empty
if live_bpm.empty:
    print('No LiveBPM values found in the data')
else:
    # Extract the time and BPM values from the LiveBPM data
    live_bpm['time'] = pd.to_datetime(live_bpm['time'].str.split(',', expand=True)[1])
    live_bpm['bpm'] = live_bpm['value'].str.split(',', expand=True)[1].astype(int)

    # Set the time column as the index of the DataFrame
    live_bpm.set_index('time', inplace=True)

    # Plot the LiveBPM data using matplotlib
    plt.plot(live_bpm['bpm'])
    plt.xlabel('Time')
    plt.ylabel('Live BPM')
    plt.show()
