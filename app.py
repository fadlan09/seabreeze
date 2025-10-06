# app.py
import streamlit as st
import xarray as xr
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import cartopy.crs as ccrs
import cartopy.feature as cfeature

st.set_page_config(page_title="🌊 Sea Breeze Simulator", layout="wide")

# === 1. Load Data ===
@st.cache_data
def load_data():
    ds = xr.open_dataset("seabreeze.nc")
    return ds

ds = load_data()

# Deteksi koordinat
lat_name = "latitude" if "latitude" in ds.coords else "lat"
lon_name = "longitude" if "longitude" in ds.coords else "lon"

# === 2. Sidebar: Lokasi & Waktu ===
st.sidebar.title("🌊 Sea Breeze Simulator")
locations = {
    "Jakarta": (106.85, -6.2),
    "Surabaya": (112.75, -7.25),
    "Makassar": (119.40, -5.1),
    "Kupang": (123.60, -10.1),
    "Medan": (98.67, 3.59)
}

loc_name = st.sidebar.selectbox("📍 Pilih lokasi pesisir", list(locations.keys()))
lon_sel, lat_sel = locations[loc_name]

times = pd.to_datetime(ds["time"].values)
time_sel = st.sidebar.slider("🕐 Pilih waktu", 0, len(times) - 1, 12)
time = times[time_sel]

st.sidebar.markdown("---")
st.sidebar.info("💡 Data dari ERA5 per jam. Lokasi darat–laut dihitung otomatis ±1° dari titik pesisir.")

# === 3. Peta Suhu & Angin ===
st.header(f"🗺️ Sea Breeze Simulation – {loc_name} – {time.strftime('%Y-%m-%d %H:%M UTC')}")

t2m = ds["t2m"].isel(time=time_sel)
u10 = ds["u10"].isel(time=time_sel)
v10 = ds["v10"].isel(time=time_sel)

fig = plt.figure(figsize=(9, 6))
ax = plt.axes(projection=ccrs.PlateCarree())
t2m.plot.contourf(ax=ax, cmap="coolwarm", transform=ccrs.PlateCarree(), cbar_kwargs={'label': '2m Temperature (K)'})
ax.quiver(ds[lon_name][::4], ds[lat_name][::4], u10[::4, ::4], v10[::4, ::4],
          transform=ccrs.PlateCarree(), scale=600)
ax.coastlines()
ax.add_feature(cfeature.BORDERS, linewidth=0.5)
ax.gridlines(draw_labels=True, linewidth=0.2)
ax.set_title("2m Temperature and Wind Vectors", fontsize=14)
st.pyplot(fig)

# === 4. Grafik Darat vs Laut ===
st.subheader("📊 Suhu Darat vs Laut di Sekitar Lokasi")

# Tentukan area darat dan laut sekitar lokasi
dlat, dlon = 1.0, 1.0
area = t2m.sel({lat_name: slice(lat_sel - dlat, lat_sel + dlat),
                lon_name: slice(lon_sel - dlon, lon_sel + dlon)})

# Asumsi barat (−dlon) laut, timur (+dlon) darat
sea_area = area.sel({lon_name: slice(lon_sel - dlon, lon_sel)})
land_area = area.sel({lon_name: slice(lon_sel, lon_sel + dlon)})

sea_temp = sea_area.mean(dim=[lat_name, lon_name])
land_temp = land_area.mean(dim=[lat_name, lon_name])

# Hitung harian
sea_series = ds["t2m"].sel({lat_name: slice(lat_sel - dlat, lat_sel + dlat),
                            lon_name: slice(lon_sel - dlon, lon_sel)}).mean(dim=[lat_name, lon_name])
land_series = ds["t2m"].sel({lat_name: slice(lat_sel - dlat, lat_sel + dlat),
                             lon_name: slice(lon_sel, lon_sel + dlon)}).mean(dim=[lat_name, lon_name])

fig2, ax2 = plt.subplots(figsize=(8, 4))
ax2.plot(times, sea_series, label="🌊 Laut", color="blue")
ax2.plot(times, land_series, label="🏝️ Darat", color="red")
ax2.axvline(time, color="gray", linestyle="--", label="Waktu terpilih")
ax2.set_ylabel("2m Temperature (K)")
ax2.set_xlabel("Waktu")
ax2.legend()
ax2.set_title(f"Perbandingan Suhu Darat vs Laut – {loc_name}")
fig2.autofmt_xdate()
st.pyplot(fig2)

st.markdown("---")
st.caption("📘 Versi 1 – Visualisasi dasar sea breeze dari ERA5 (t2m, u10, v10). Versi lanjut akan menambahkan cross-section dan analisis tekanan.")

