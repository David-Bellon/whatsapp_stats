from fastapi import FastAPI, Request, File, UploadFile
from fastapi.responses import HTMLResponse, StreamingResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
import re
import pandas as pd
import matplotlib.pyplot as plt
import datetime
from matplotlib.backends.backend_pdf import PdfPages
from io import BytesIO
from typing import Dict, List
from pydantic import BaseModel
import base64
import uuid
import json
import os
import logging
import time
from starlette.middleware.base import BaseHTTPMiddleware
import numpy as np

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('app.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

class RequestLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        
        # Log request
        logger.info(f"Request started: {request.method} {request.url.path} from {request.client.host}")
        
        try:
            response = await call_next(request)
            process_time = time.time() - start_time
            
            # Log response
            logger.info(
                f"Request completed: {request.method} {request.url.path} "
                f"Status: {response.status_code} "
                f"Time: {process_time:.2f}s"
            )
            
            return response
        except Exception as e:
            process_time = time.time() - start_time
            logger.error(
                f"Request failed: {request.method} {request.url.path} "
                f"Error: {str(e)} "
                f"Time: {process_time:.2f}s"
            )
            raise

app = FastAPI()
app.add_middleware(RequestLoggingMiddleware)
templates = Jinja2Templates(directory="templates")

# Create tmp directory if it doesn't exist
os.makedirs("tmp", exist_ok=True)

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

class StatsResponse(BaseModel):
    len: int
    first: str
    last: str

class ShareRequest(BaseModel):
    plots: Dict[str, List[str]]  # Dictionary mapping plot names to arrays of base64 strings

def get_df(file_content: str, device: str) -> pd.DataFrame:
    logger.info("Reading file")
    f = file_content
    if device == "iOS":
        f = f.split("\r")
    else:
        f = f.split("\n")
    pattern = r'^\d{1,2}/\d{1,2}/\d{2}$'
    dates = []
    hours = []
    names = []
    message = []
    for line in f:
        if device == "iOS":
            line = line.replace("[", "").replace("]", " -").replace("\n", "")
        first_half = line.split("-")[0].replace(" ", "")
        if re.match(pattern, first_half.split(",")[0]):
            try:
                second_half = line.split("-")[1].split(":", 1)
                message.append(second_half[1].lstrip(" "))
                date = first_half.split(",")[0]
                dates.append(date)
                hours.append(first_half.split(",")[1])
                names.append(second_half[0].lstrip(" "))
            except:
                None
        else:
            message[-1] = message[-1] + " " + line

    df = pd.DataFrame(columns=["Date", "Hour", "Name", "Message"])
    df["Date"] = dates
    df["Hour"] = hours
    df["Name"] = names
    df["Message"] = message
    return df


def plot_years_stacked(variable, years, values, x_label, y_label, title):
    # Stacked plot
    plt.figure(figsize=(12, 10))
    bottom = np.zeros(len(variable))  # to stack bars
    for i, year in enumerate(years):
        bars = plt.bar(variable, values[:, i], bottom=bottom, label=str(year), width=0.9)
        # Add data labels on each bar segment
        for bar in bars:
            height = bar.get_height()
            if height > 0:  # only label bars with positive height
                plt.text(
                    bar.get_x() + bar.get_width() / 2,  # x position: center of the bar
                    bar.get_y() + height / 2,           # y position: middle of the bar segment
                    f'{int(height)}',                   # label text (integer)
                    ha='center', va='center', fontsize=9, color='white'
                )
        bottom += values[:, i]

    plt.title(title, fontsize=16)
    plt.xlabel(x_label)
    plt.ylabel(y_label)
    plt.legend(title="Año")
    plt.xticks(variable)
    plt.tight_layout()
    img_buffer = BytesIO()
    plt.savefig(img_buffer, format='png')
    img_buffer.seek(0)

    return f"data:image/png;base64,{base64.b64encode(img_buffer.read()).decode('utf-8')}"


def plot_years_line(df, variable_name, x_label, y_label, title):
    df_plot = df.set_index(variable_name)
    df_plot = df_plot.T 

    # Plot
    plt.figure(figsize=(16, 10))  # Adjust figure size as needed

    for name in df_plot.columns:
        plt.plot(df_plot.index, df_plot[name], marker='o', label=name)

    # Labels and title
    plt.title(title, fontsize=16)
    plt.xlabel(x_label, fontsize=12)
    plt.ylabel(y_label, fontsize=12)
    plt.legend(title="Name")  # Move legend outside
    plt.grid(False)
    plt.tight_layout()
    img_buffer = BytesIO()
    plt.savefig(img_buffer, format='png')
    img_buffer.seek(0)

    return f"data:image/png;base64,{base64.b64encode(img_buffer.read()).decode('utf-8')}"


def plot_all_data(variable, years, values, x_label, y_label, title):
    # Each Year Images
    encoded_images = []
    for i, year in enumerate(years):
        plt.figure(figsize=(12, 10))
        bars = plt.bar(variable, values[:, i], label=str(year), width=0.9)
        # Add data labels on each bar segment
        for bar in bars:
            height = bar.get_height()
            if height > 0:  # only label bars with positive height
                plt.text(
                    bar.get_x() + bar.get_width() / 2,  # x position: center of the bar
                    bar.get_y() + height * 0.95,           # y position: middle of the bar segment
                    f'{int(height)}',                   # label text (integer)
                    ha='center', va='center', fontsize=10, color='white'
                )

        plt.xlabel(x_label)
        plt.ylabel(y_label)
        plt.legend(title="Año")
        plt.xticks(variable)
        plt.tight_layout()
        img_buffer = BytesIO()
        plt.savefig(img_buffer, format='png')
        img_buffer.seek(0)

        encoded_images.append(f"data:image/png;base64,{base64.b64encode(img_buffer.read()).decode('utf-8')}")

    return encoded_images


@app.get("/", response_class=HTMLResponse)
async def main_page(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/privacy_policy", response_class=HTMLResponse)
async def privacy_policy(request: Request):
    return templates.TemplateResponse("privacy_policy.html", {"request": request})

@app.post("/numbers/{device}", response_model=StatsResponse)
async def simple_stats(device: str, file: UploadFile = File(...)):
    content = await file.read()
    logger.info("here")
    df = get_df(content.decode("utf-8", errors="ignore"), device)
    length = len(df)
    first_date = list(df["Date"])[0]
    last_date = list(df["Date"])[-1]
    return {"len": length, "first": first_date, "last": last_date}

@app.post("/hours/{device}")
async def hour_dist(device: str, file: UploadFile = File(...)):
    content = await file.read()
    df = get_df(content.decode("utf-8"), device)
    df["Date"] = pd.to_datetime(df["Date"], format='%d/%m/%y')
    df["Year"] = df["Date"].dt.year
    df["Hour"] = df["Hour"].str.split(":").str[0].astype(int)

    group_by = df.groupby(["Hour", "Year"]).count().reset_index()
    df_pivot = group_by.pivot(index='Hour', columns='Year', values='Message').reset_index().fillna(0)
    print(df_pivot)

    encoded_images = []

    hours = df_pivot['Hour']
    years = df_pivot.columns[1:]  # exclude 'Hour'
    values = df_pivot[years].fillna(0).to_numpy()
    
    encoded_images.append(plot_years_stacked(hours, years, values, x_label="Horas", y_label="Numero Mensajes", title="Mensajes por Hora"))
    for image in plot_all_data(hours, years, values, x_label="Horas", y_label="Numero Mensajes", title="Mensajes por Hora"):
        encoded_images.append(image)
    
    plt.close()
    return JSONResponse(content={"images": encoded_images})

@app.post("/months/{device}")
async def month_dist(device: str, file: UploadFile = File(...)):
    content = await file.read()
    df = get_df(content.decode("utf-8"), device)
    month_names = {
        1: "Enero",
        2: "Febrero",
        3: "Marzo",
        4: "Abril",
        5: "Mayo",
        6: "Junio",
        7: "Julio",
        8: "Agosto",
        9: "Septiembre",
        10: "Octubre",
        11: "Noviembre",
        12: "Diciembre"
    }
    df["Date"] = pd.to_datetime(df["Date"], format='%d/%m/%y')
    df["Month"] = df["Date"].dt.month
    df["Year"] = df["Date"].dt.year

    group_by = df.groupby(["Month", "Year"]).count().reset_index()
    df_pivot = group_by.pivot(index='Month', columns='Year', values='Message').reset_index().fillna(0)
    df_pivot["Month"] = df_pivot["Month"].map(month_names)
    print(df_pivot)
    
    encoded_images = []

    months = df_pivot['Month']
    years = df_pivot.columns[1:]
    values = df_pivot[years].fillna(0).to_numpy()
    
    encoded_images.append(plot_years_stacked(months, years, values, x_label="Mes", y_label="Numero Mensajes", title="Mensajes por Mes"))
    for image in plot_all_data(months, years, values, x_label="Mes", y_label="Numero Mensajes", title="Mensajes por Mes"):
        encoded_images.append(image)

    
    plt.close()
    return JSONResponse(content={"images": encoded_images})

@app.post("/dayDist/{device}")
async def day_dist(device: str, file: UploadFile = File(...)):
    content = await file.read()
    df = get_df(content.decode("utf-8"), device)
    day_names = {
        0: "L",
        1: "M",
        2: "X",
        3: "J",
        4: "V",
        5: "S",
        6: "D"
    }
    df["Date"] = pd.to_datetime(df["Date"], format='%d/%m/%y')
    df["WeekDay"] = df["Date"].dt.weekday
    df["Year"] = df["Date"].dt.year

    group_by = df.groupby(["WeekDay", "Year"]).count().reset_index()
    df_pivot = group_by.pivot(index='WeekDay', columns='Year', values='Message').reset_index().fillna(0)
    df_pivot["WeekDay"] = df_pivot["WeekDay"].map(day_names)
    print(df_pivot)

    encoded_images = []

    week_days = df_pivot['WeekDay']
    years = df_pivot.columns[1:]
    values = df_pivot[years].fillna(0).to_numpy()
    
    encoded_images.append(plot_years_stacked(week_days, years, values, x_label="Dia Semana", y_label="Numero Mensajes", title="Mensajes por Dia de la Semana"))
    for image in plot_all_data(week_days, years, values, x_label="Dia Semana", y_label="Numero Mensajes", title="Mensajes por Dia de la Semana"):
        encoded_images.append(image)

    plt.close()
    return JSONResponse(content={"images": encoded_images})

@app.post("/eachPerson/{device}")
async def each_person(device: str, file: UploadFile = File(...)):
    content = await file.read()
    df = get_df(content.decode("utf-8"), device)
    df["Date"] = pd.to_datetime(df["Date"], format='%d/%m/%y')
    df["Year"] = df["Date"].dt.year
    df["Is_Multimedia"] = df["Message"].str.startswith("<", na=False)

    group_by = df.groupby(["Name", "Year"]).count().reset_index()
    df_pivot = group_by.pivot(index='Name', columns='Year', values='Message').reset_index().fillna(0)
    print(df_pivot)

    encoded_images = []

    names = df_pivot['Name']
    years = df_pivot.columns[1:]
    values = df_pivot[years].fillna(0).to_numpy()

    encoded_images.append(plot_years_stacked(names, years, values, x_label="Persona", y_label="Numero Mensajes", title="Mensajes por Persona"))
    encoded_images.append(plot_years_line(df_pivot, variable_name="Name", x_label="Años", y_label="Numero Mensajes", title="Mensajes Enviados por Año por Persona"))

    df = df.loc[df["Is_Multimedia"] == True]
    group_by = df.groupby(["Name", "Year"]).count().reset_index()
    df_pivot = group_by.pivot(index='Name', columns='Year', values='Message').reset_index().fillna(0)
    print(df_pivot)
    names = df_pivot['Name']
    years = df_pivot.columns[1:]
    values = df_pivot[years].fillna(0).to_numpy()
    encoded_images.append(plot_years_stacked(names, years, values, x_label="Persona", y_label="Numero Mensajes Multimedia", title="Mensajes Multimedia Enviados por Año por Persona"))
    encoded_images.append(plot_years_line(df_pivot, variable_name="Name", x_label="Años", y_label="Numero Mensajes Multimedia", title="Mensajes Multimedia Enviados por Año por Persona"))

    plt.clf()
    return JSONResponse(content={"images": encoded_images})

@app.post("/noMess/{device}")
async def no_message(device: str, file: UploadFile = File(...)):
    content = await file.read()
    df = get_df(content.decode("utf-8"), device)
    df["Date"] = pd.to_datetime(df["Date"], format='%d/%m/%y')
    df["Year"] = df["Date"].dt.year

    group_by = df.groupby(["Name", "Year"]).apply(lambda x: len(set(x["Date"]))).reset_index()
    df_pivot = group_by.pivot(index='Name', columns='Year', values=0).reset_index().fillna(0)
    print(df_pivot)
    
    encoded_images = []
    names = df_pivot['Name']
    years = df_pivot.columns[1:]
    values = df_pivot[years].fillna(0).to_numpy()

    encoded_images.append(plot_years_stacked(names, years, values, x_label="Personas", y_label="Dias Hablados", title="Días Hablados por Persona"))
    encoded_images.append(plot_years_line(df_pivot, "Name", x_label="Años", y_label="Dias Hablados", title="Días Hablados por Persona"))
    plt.clf()
    return JSONResponse(content={"images": encoded_images})

@app.post("/streak/{device}")
async def streak(device: str, file: UploadFile = File(...)):
    content = await file.read()
    df = get_df(content.decode("utf-8"), device)
    in_group = list(df["Name"].unique())
    dict_days_max_no_talk = {}
    for name in in_group:
        person_df = df.loc[df["Name"] == name]
        dates = list(person_df["Date"])
        dict_days_max_no_talk[name] = 0
        for i in range(1, len(dates)):
            previous_date_split = dates[i - 1].split("/")
            current_date_split = dates[i].split("/")
            previous_day = datetime.datetime(int(previous_date_split[2]), int(previous_date_split[1]),
                                             int(previous_date_split[0]))
            current_day = datetime.datetime(int(current_date_split[2]), int(current_date_split[1]),
                                            int(current_date_split[0]))
            if (current_day - previous_day).days > 1:
                if (current_day - previous_day).days > dict_days_max_no_talk[name]:
                    dict_days_max_no_talk[name] = (current_day - previous_day).days

    plt.figure(figsize=(10, 10))
    bars = plt.bar(list(dict_days_max_no_talk.keys()), list(dict_days_max_no_talk.values()), label="Dias NO hablados")
    plt.legend(loc="upper left")
    plt.title("Racha días seguidos sin hablar")
    plt.xlabel("Persona")
    plt.ylabel("Dias")
    plt.bar_label(bars)
    img_buffer = BytesIO()
    plt.savefig(img_buffer, format='png')
    img_buffer.seek(0)
    plt.clf()

    encoded_images = []
    encoded_images.append(f"data:image/png;base64,{base64.b64encode(img_buffer.read()).decode('utf-8')}")
    return JSONResponse(content={"images": encoded_images})

@app.post("/share")
async def share_stats(request: ShareRequest):
    logger.info("Received share request")
    try:
        # Generate a unique ID for this share
        share_id = str(uuid.uuid4())
        logger.info(f"Generated share ID: {share_id}")
        
        # Store the plots in a temporary file
        with open(f'tmp/{share_id}.json', 'w') as f:
            json.dump(request.plots, f)
        logger.info(f"Successfully stored plots for share ID: {share_id}")
        
        return {"share_id": share_id}
    except Exception as e:
        logger.error(f"Error processing share request: {str(e)}")
        raise

@app.get("/share/{share_id}")
async def view_shared_stats(share_id: str, request: Request):
    logger.info(f"Received request to view shared stats with ID: {share_id}")
    try:
        with open(f'tmp/{share_id}.json', 'r') as f:
            plots = json.load(f)
        logger.info(f"Successfully retrieved plots for share ID: {share_id}")
        return templates.TemplateResponse("shared_stats.html", {
            "request": request,
            "plots": plots,
            "plot_names": {
                'hours': 'Messages by Hour',
                'months': 'Messages by Month',
                'days': 'Messages by Day of Week',
                'people': 'Messages by Person',
                'days_talk': 'Days Talked by Person',
                'streak': 'Longest Streak Without Talking'
            }
        })
    except FileNotFoundError:
        logger.error(f"Share not found for ID: {share_id}")
        return templates.TemplateResponse("error.html", {
            "request": request,
            "error": "Share not found or expired"
        })
    except Exception as e:
        logger.error(f"Error retrieving shared stats for ID {share_id}: {str(e)}")
        raise

if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=7777)