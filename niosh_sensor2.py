import streamlit as st
import pandas as pd
from streamlit_drawable_canvas import st_canvas
from PIL import Image
import matplotlib.pyplot as plt
from matplotlib.colors import Normalize
import time
import base64

st.set_page_config(page_title="NIOSH Sensor Data Visualization Project", layout="wide")
st.title("NIOSH Sensor Data Visualization Project")
img = Image.open("niosh_sensor.png")
img_width, img_height = img.size

sensor_data = pd.read_csv("October31.csv")
sensor_data["Timestamp"] = pd.to_datetime(sensor_data["Date"] + " " + sensor_data["Time"], errors="coerce")
sensor_data = sensor_data.drop(columns=["Date", "Time"]) 
sensor_columns = ["AboveSuperSac", "ControlRoom", "Palletizer", "TransferPoint", "TruckLoading"]

sensor_data = sensor_data.melt(id_vars=["Timestamp"], var_name="SensorID", value_name="Value")

st.write("Click on the map to place the 5 sensors. Sensors must match the following labels:")
sensor_labels = sensor_columns 
st.write(sensor_labels)

canvas_result = st_canvas(
    fill_color="rgba(255, 165, 0, 0.3)",
    stroke_width=1,
    background_image=img,
    update_streamlit=True,
    height=img_height,
    width=img_width,
    drawing_mode="point",
    point_display_radius=5,
    key="canvas"
)

if "animation_running" not in st.session_state:
    st.session_state["animation_running"] = False
if "animation_index" not in st.session_state:
    st.session_state["animation_index"] = 0

if canvas_result.json_data is not None:
    points = pd.json_normalize(canvas_result.json_data["objects"])
    if len(points) == len(sensor_labels):  
        points['X'] = points['left'].clip(0, img_width - 1)
        points['Y'] = points['top'].clip(0, img_height - 1)
        points['SensorID'] = sensor_labels

        merged_data = sensor_data.merge(points, on="SensorID")

        st.sidebar.write("Select Time Range")
        timestamps = pd.to_datetime(merged_data["Timestamp"].sort_values().unique())
        time_range = st.sidebar.slider(
            "Time Range",
            min_value=timestamps[0].to_pydatetime(),
            max_value=timestamps[-1].to_pydatetime(),
            value=(timestamps[0].to_pydatetime(), timestamps[-1].to_pydatetime()),
            format="MM/DD HH:mm"
        )
        start_time, end_time = pd.to_datetime(time_range)

        if st.sidebar.button("Start" if not st.session_state["animation_running"] else "Stop"):
            st.session_state["animation_running"] = not st.session_state["animation_running"]

        scatter_placeholder = st.empty()
        st.divider()
        while st.session_state["animation_running"] and st.session_state["animation_index"] < len(timestamps):
            current_index = st.session_state["animation_index"]
            current_timestamp = timestamps[current_index]

            if current_timestamp < start_time or current_timestamp > end_time:
                st.session_state["animation_index"] += 1
                continue

            filtered_data = merged_data[merged_data['Timestamp'] == current_timestamp]

            fig, ax = plt.subplots(figsize=(10, 10))

            ax.imshow(img, extent=[0, img_width, 0, img_height], origin="upper")

            scatter = ax.scatter(
                filtered_data["X"],
                img_height - filtered_data["Y"],  
                c=filtered_data["Value"],
                s=filtered_data["Value"] * 10,  
                cmap="viridis",
                norm=Normalize(
                    vmin=sensor_data["Value"].min(),
                    vmax=sensor_data["Value"].max()
                ),
                edgecolor="black",
                alpha=0.8
            )


            for _, row in filtered_data.iterrows():
                ax.text(
                    row["X"],
                    img_height - row["Y"],
                    f"{row['Value']:.1f}",
                    ha="center",
                    va="center",
                    fontsize=7, 
                    color="white" 
                )

            
            cbar = fig.colorbar(scatter, ax=ax, fraction=0.046, pad=0.04)
            cbar.set_label("Concentration", fontsize=12)

        
            ax.set_xlim([0, img_width])
            ax.set_ylim([0, img_height])  
            ax.set_title(f"Sensor Concentrations at {current_timestamp.strftime('%Y-%m-%d %H:%M')}", fontsize=16)
            ax.axis("off") 

            scatter_placeholder.pyplot(fig)

            st.session_state["animation_index"] += 1

            time.sleep(0.5)

        if st.session_state["animation_index"] >= len(timestamps):
            st.session_state["animation_index"] = 0
            st.session_state["animation_running"] = False
    else:
        st.warning("Please place the sensors.")

st.sidebar.markdown("---")
st.sidebar.write("Created by Intellygiene")



def get_base64_encoded_image(image_path):
    with open(image_path, "rb") as img_file:
        return base64.b64encode(img_file.read()).decode()

image_path = "intellygiene.png" 
website_url = "https://intellygiene.com" 

encoded_image = get_base64_encoded_image(image_path)

st.sidebar.markdown(
    f"""
    <a href="{website_url}" target="_blank">
        <img src="data:image/jpeg;base64,{encoded_image}" 
        alt="Clickable Image" style="width:100%; border-radius:10px;">
    </a>
    """,
    unsafe_allow_html=True,
)
