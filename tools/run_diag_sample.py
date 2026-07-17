import os, sys
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from logic import diagnostic

sample = {
    "Soil_Type": "Loamy",
    "Crop_Type": "Maize",
    "Crop_Growth_Stage": "Vegetative",
    "Season": "Kharif",
    "Irrigation_Type": "Drip",
    "Water_Source": "Groundwater",
    "Mulching_Used": "No",
    "Region": "Gombe",
    "Soil_pH": 6.5,
    "Soil_Moisture": 30.0,
    "Organic_Carbon": 1.2,
    "Electrical_Conductivity": 0.7,
    "Temperature_C": 26.0,
    "Humidity": 40.0,
    "Rainfall_mm": 5.0,
    "Sunlight_Hours": 8.0,
    "Wind_Speed_kmh": 5.0,
    "Field_Area_hectare": 1.0,
    "Previous_Irrigation_mm": 0.0,
}

res = diagnostic.run_diagnostic(sample)
print('run_diagnostic result:')
print(res)
