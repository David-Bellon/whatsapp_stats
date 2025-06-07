from fastapi import FastAPI, Request, File, UploadFile
from fastapi.responses import HTMLResponse, FileResponse, StreamingResponse
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

app = FastAPI()
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
    plots: Dict[str, str]  # Dictionary mapping plot names to base64 strings

def get_df(file_content: str, device: str) -> pd.DataFrame:
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

@app.get("/", response_class=HTMLResponse)
async def main_page(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/privacy_policy", response_class=HTMLResponse)
async def privacy_policy(request: Request):
    return templates.TemplateResponse("privacy_policy.html", {"request": request})

@app.post("/numbers/{device}", response_model=StatsResponse)
async def simple_stats(device: str, file: UploadFile = File(...)):
    content = await file.read()
    df = get_df(content.decode("utf-8", errors="ignore"), device)
    length = len(df)
    first_date = list(df["Date"])[0]
    last_date = list(df["Date"])[-1]
    logger.info("here")
    return {"len": length, "first": first_date, "last": last_date}

@app.post("/hours/{device}")
async def hour_dist(device: str, file: UploadFile = File(...)):
    content = await file.read()
    df = get_df(content.decode("utf-8"), device)
    hours = df["Hour"]
    dict_hours = {}
    for hour in hours:
        hole = int(hour.split(":")[0])
        if hole in list(dict_hours.keys()):
            dict_hours[hole] += 1
        else:
            dict_hours[hole] = 0

    plt.figure(figsize=(10, 10))
    bars = plt.bar(list(dict_hours.keys()), list(dict_hours.values()))
    plt.xlabel("Horas")
    plt.ylabel("Numero Mensajes")
    plt.xticks(list(dict_hours.keys()), list(dict_hours.keys()))
    plt.bar_label(bars)
    img_buffer = BytesIO()
    plt.savefig(img_buffer, format='png')
    img_buffer.seek(0)
    plt.clf()
    return StreamingResponse(img_buffer, media_type='image/png')

@app.post("/months/{device}")
async def month_dist(device: str, file: UploadFile = File(...)):
    content = await file.read()
    df = get_df(content.decode("utf-8"), device)
    dates = df["Date"]
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
    dict_date = {}
    for date in dates:
        month = int(date.split("/")[1])
        if month in list(dict_date.keys()):
            dict_date[month] += 1
        else:
            dict_date[month] = 0
    for i in list(dict_date.keys()):
        dict_date[month_names[i]] = dict_date.pop(i)
    plt.figure(figsize=(10, 10))
    bars = plt.bar(list(dict_date.keys()), list(dict_date.values()))
    plt.xlabel("Mes")
    plt.ylabel("Numero Mensajes")
    plt.bar_label(bars)
    img_buffer = BytesIO()
    plt.savefig(img_buffer, format='png')
    img_buffer.seek(0)
    plt.clf()
    return StreamingResponse(img_buffer, media_type='image/png')

@app.post("/dayDist/{device}")
async def day_dist(device: str, file: UploadFile = File(...)):
    content = await file.read()
    df = get_df(content.decode("utf-8"), device)
    dates = df["Date"]
    day_names = {
        0: "L",
        1: "M",
        2: "X",
        3: "J",
        4: "V",
        5: "S",
        6: "D"
    }
    dict_day = {
        0: 0,
        1: 0,
        2: 0,
        3: 0,
        4: 0,
        5: 0,
        6: 0
    }
    for date in dates:
        day = datetime.datetime(int(date.split("/")[-1]), int(date.split("/")[1]), int(date.split("/")[0])).weekday()
        if day in list(dict_day.keys()):
            dict_day[day] += 1
        else:
            dict_day[day] = 0
    for i in list(dict_day.keys()):
        dict_day[day_names[i]] = dict_day.pop(i)
    plt.figure(figsize=(10, 10))
    bars = plt.bar(list(dict_day.keys()), list(dict_day.values()))
    plt.xlabel("Dia")
    plt.ylabel("Numero Mensajes")
    plt.bar_label(bars)
    img_buffer = BytesIO()
    plt.savefig(img_buffer, format='png')
    img_buffer.seek(0)
    plt.clf()
    return StreamingResponse(img_buffer, media_type='image/png')

@app.post("/eachPerson/{device}")
async def each_person(device: str, file: UploadFile = File(...)):
    content = await file.read()
    df = get_df(content.decode("utf-8"), device)
    in_group = list(df["Name"].unique())
    names = df["Name"]
    dict_names = {}
    for name in names:
        if name in in_group:
            if name in list(dict_names.keys()):
                dict_names[name] += 1
            else:
                dict_names[name] = 0

    df_only_mul = df.loc[df["Message"].str[0] == "<"]
    mul_names = {}
    for guy in in_group:
        own_mes = df_only_mul.loc[df_only_mul["Name"] == guy]
        mul_names[guy] = len(own_mes)
    plt.figure(figsize=(10, 10))
    bars = plt.bar(list(dict_names.keys()), list(dict_names.values()), label="Mensajes Totales")
    plt.bar(list(mul_names.keys()), list(mul_names.values()), label="Mensajes Multimedia")
    plt.legend()
    plt.xlabel("Persona")
    plt.ylabel("Numero Mensajes")
    plt.bar_label(bars)
    img_buffer = BytesIO()
    plt.savefig(img_buffer, format='png')
    img_buffer.seek(0)
    plt.clf()
    return StreamingResponse(img_buffer, media_type='image/png')

@app.post("/noMess/{device}")
async def no_message(device: str, file: UploadFile = File(...)):
    content = await file.read()
    df = get_df(content.decode("utf-8"), device)
    in_group = list(df["Name"].unique())
    days_talk = {}
    for name in in_group:
        person_df = df.loc[df["Name"] == name]
        days_talk[name] = len(set(person_df['Date']))

    dict_days_max_no_talk = {}
    for name in in_group:
        person_df = df.loc[df["Name"] == name]
        dates = list(person_df["Date"])
        dict_days_max_no_talk[name] = 0
        for i in range(1, len(dates)):
            previous_date_split = dates[i-1].split("/")
            current_date_split = dates[i].split("/")
            previous_day = datetime.datetime(int(previous_date_split[2]), int(previous_date_split[1]), int(previous_date_split[0]))
            current_day = datetime.datetime(int(current_date_split[2]), int(current_date_split[1]), int(current_date_split[0]))
            if (current_day - previous_day).days > 1:
                if (current_day - previous_day).days > dict_days_max_no_talk[name]:
                    dict_days_max_no_talk[name] = (current_day - previous_day).days

    plt.figure(figsize=(10, 10))
    bars = plt.bar(list(days_talk.keys()), list(days_talk.values()), label="Dias hablados")
    plt.legend()
    plt.title(f"Maximo Numero de Días = {len(list(df['Date'].unique()))} dias")
    plt.xlabel("Persona")
    plt.ylabel("Dias")
    plt.bar_label(bars)
    img_buffer = BytesIO()
    plt.savefig(img_buffer, format='png')
    img_buffer.seek(0)
    plt.clf()
    return StreamingResponse(img_buffer, media_type='image/png')

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
    return StreamingResponse(img_buffer, media_type='image/png')

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
            "plots": plots
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