# -*- coding: utf-8 -*-
"""
Created on Thu Feb  9 08:58:00 2023

@author: gws

This is a Python script that processes and analyzes data in a CSV file.
The script uses the pandas, numpy, and matplotlib libraries to import the data,
calculate moving averages, clean the data, and plot the results.
The user is prompted to input variables such as the window size for the moving average,
and upper and lower percentiles for cleaning the data.
The script also provides a graphical user interface using the tkinter library.

"""

import math
import pandas as pd
import numpy as np
from statistics import NormalDist
import matplotlib.pyplot as plt
import tkinter as tk
from tkinter import filedialog
from tkinter import Frame, Label, Scale

def get_variables():
    root = tk.Tk()
    root.title("Input Variables")
    root.geometry("250x200")

    frame = Frame(root)
    frame.pack()

    window_size_label = Label(frame, text="Window size:")
    window_size_label.pack()
    window_size_entry = tk.Entry(frame)
    window_size_entry.pack()

    upper_percentile_label = Label(frame, text="Upper percentile:")
    upper_percentile_label.pack()
    upper_percentile_slider = Scale(frame, from_=1, to=100, orient="horizontal", showvalue=0, command=lambda x: upper_percentile_entry.delete(0, "end") or upper_percentile_entry.insert(0, upper_percentile_slider.get()))
    upper_percentile_slider.set(99)
    upper_percentile_slider.pack()
    upper_percentile_entry = tk.Entry(frame)
    upper_percentile_entry.insert(0, upper_percentile_slider.get())
    upper_percentile_entry.pack()

    lower_percentile_label = Label(frame, text="Lower percentile:")
    lower_percentile_label.pack()
    lower_percentile_slider = Scale(frame, from_=1, to=100, orient="horizontal", showvalue=0, command=lambda x: lower_percentile_entry.delete(0, "end") or lower_percentile_entry.insert(0, lower_percentile_slider.get()))
    lower_percentile_slider.set(2)
    lower_percentile_slider.pack()
    lower_percentile_entry = tk.Entry(frame)
    lower_percentile_entry.insert(0, lower_percentile_slider.get())
    lower_percentile_entry.pack()

    def on_apply():
        global window_size, upper_percentile, lower_percentile
        window_size = int(window_size_entry.get())
        upper_percentile_input = upper_percentile_entry.get()
        if upper_percentile_input:
            upper_percentile = float(upper_percentile_input)
        else:
            upper_percentile = upper_percentile_slider.get()
        lower_percentile_input = lower_percentile_entry.get()
        if lower_percentile_input:
            lower_percentile = float(lower_percentile_input)
        else:
            lower_percentile = lower_percentile_slider.get()
        root.destroy()

    apply_button = tk.Button(frame, text="Apply", command=on_apply)
    apply_button.pack()

    root.mainloop()

    return window_size, upper_percentile/100, lower_percentile/100

def importing():
    reader = tk.Tk()
    file_path = filedialog.askopenfilename(filetype=[("Comma Separated Values (CSV)", ".csv")], title = "Open Data File in CSV")
    imported_data = pd.read_csv(file_path)
    reader.destroy()
    
    return imported_data

def moving_average(values, window_size):
    window = []
    moving_averages = []
    
    for value in values:
        window.append(value)
        if len(window) > window_size:
            window.pop(0)
        nansum = np.nansum(window)
        nancount = np.count_nonzero(~np.isnan(window))
        if nansum != 0 and nancount != 0:
            avg = nansum / nancount
        else:
            avg = float("NaN")
        avg = round(avg, 2)
        moving_averages.append(avg if not math.isnan(avg) else float("NaN"))
    
    return moving_averages


def cleaning_data(CurrentData, MovingAverage, upper_percentile, lower_percentile, ShiftData):
    CombinedData = np.array([CurrentData, MovingAverage]).T
    CombinedData = pd.DataFrame(CombinedData, columns = ["RawData","MovingAverage"])
    #CombinedData["MovingAverage"] = CombinedData["MovingAverage"].shift(-ShiftData)
    
    CombinedData["Error"] = CombinedData["MovingAverage"] - CombinedData["RawData"]
    CombinedData["Error"].fillna(value=CombinedData["MovingAverage"], inplace=True)
    
    StandardDeviation = CombinedData["Error"].std()
    MeanError = StandardDeviation / np.sqrt(np.count_nonzero(~np.isnan(CombinedData["Error"])))
    
    UpperDistribution = NormalDist(mu=MeanError, sigma=StandardDeviation).inv_cdf(upper_percentile)
    LowerDistribution = NormalDist(mu=MeanError, sigma=StandardDeviation).inv_cdf(lower_percentile)
    
    CombinedData["UpperCutoff"] = CombinedData["MovingAverage"] + UpperDistribution
    CombinedData["LowerCutoff"] = CombinedData["MovingAverage"] + LowerDistribution
    
    CombinedData["Clean"] = CombinedData[(CombinedData["RawData"] > CombinedData["LowerCutoff"]) & (CombinedData["RawData"] < CombinedData["UpperCutoff"])]["RawData"]
    
    return CombinedData


def plot_data(CombinedData):
    fig, ax = plt.subplots(figsize=[8, 5])

    CombinedData["RawData"].plot(color="#0087FF", legend=True, ax=ax)
    CombinedData["MovingAverage"].plot(color='#44B400', legend=True, ax=ax)
    CombinedData["UpperCutoff"].plot(color='#E55B00', legend=True, linestyle='dashed', ax=ax)
    CombinedData["LowerCutoff"].plot(color='#E55B00', legend=True, linestyle='dashed', ax=ax)

    ax.set_ylim(None, None)
    ax.set_xlim(0, None)
    ax.set_title("", fontsize=25)

    plt.show()
    
    fig, ax = plt.subplots(figsize=[8, 5])
    CombinedData["Clean"].plot(legend=True, ax=ax)

    ax.set_ylim(0, None)
    ax.set_xlim(0, None)
    ax.set_title("1st Iteration Cleaned Data", fontsize=25)

    plt.show()

def main():
    print("")
    SaveFile = []
    
    window_size, upper_percentile, lower_percentile = get_variables()
    ShiftData = math.floor(window_size/2)
    
    imported_data = importing()
    
    timestamp = imported_data["DateTime"]
    SaveFile.append(timestamp)
    RawData = imported_data.drop(imported_data.columns[0],axis=1)
    for i in range(len(RawData.columns)):
        col = RawData.columns[i]
        if "MW" in col or "MVA" in col:
            continue
        
        RawData = RawData[RawData[col] != 0]
        CurrentData = RawData[col].tolist()
        #MovingAverage = moving_average(CurrentData, window_size) # COUSTOM MOVING AVERAGE
        
        CurrentData = pd.Series(CurrentData)
        ExponentialMovingAverage = CurrentData.ewm(span=window_size).mean()
        
        
        CombinedData = cleaning_data(CurrentData, ExponentialMovingAverage, upper_percentile, lower_percentile, ShiftData)
        
        plot_data(CombinedData)
        
        SaveFile.append(CombinedData["Clean"].rename(col))
        SaveFile
    

    df = pd.DataFrame(SaveFile).T
    df.to_csv("Output.csv", index=False)
    
    
    

    
    
if __name__ == "__main__":
    main()












