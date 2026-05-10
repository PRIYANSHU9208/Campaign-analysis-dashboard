from flask import Flask, render_template, request
import pandas as pd
import json
import plotly
import plotly.express as px

app = Flask(__name__)

# STORE DATA

all_data = []

USD_TO_INR = 115


# HOME PAGE

@app.route("/")
def home():

    total_spend = sum(
        item["spend"]
        for item in all_data
    )

    total_campaigns = len(all_data)

    lead_count = len([
        x for x in all_data
        if x["type"] == "LEADS"
    ])

    engagement_count = len([
        x for x in all_data
        if x["type"] == "ENGAGEMENT"
    ])

    graphJSON = None

    # ONLY THOSE ROWS WHERE CALLS > 0

    graph_data = [

        x for x in all_data

        if x["calls"] > 0

    ]

    if len(graph_data) > 0:

        df = pd.DataFrame(graph_data)

        # CPC

        df["cpc"] = df.apply(

            lambda x:

            x["spend"] / x["calls"]

            if x["calls"] > 0

            else 0,

            axis=1

        )

        # DATE FORMAT

        df["date"] = pd.to_datetime(

            df["date"]

        ).dt.strftime("%Y-%m-%d")

        # SORT DATE

        df = df.sort_values("date")

        # UNIQUE LABEL

        df["label"] = (

            df["date"]

            + " | "

            + df["name"]

        )

        # BAR GRAPH

        fig = px.bar(

            df,

            x="label",

            y="cpc",

            color="type",

            title="Campaign CPC Comparison"

        )

        fig.update_layout(

            template="plotly_white",

            height=600,

            xaxis_title="Campaign & Date",

            yaxis_title="CPC",

            bargap=0.35

        )

        fig.update_xaxes(

            tickangle=-35

        )

        graphJSON = json.dumps(

            fig,

            cls=plotly.utils.PlotlyJSONEncoder

        )

    return render_template(

        "index.html",

        campaigns=all_data,

        total_spend=round(
            total_spend,
            2
        ),

        total_campaigns=total_campaigns,

        lead_count=lead_count,

        engagement_count=engagement_count,

        graphJSON=graphJSON

    )


# FILE UPLOAD

@app.route("/upload", methods=["POST"])
def upload():

    global all_data

    files = request.files.getlist("files")

    for file in files:

        filename = file.filename.lower()

        try:

            # CSV

            if filename.endswith(".csv"):

                df = pd.read_csv(
                    file,
                    encoding_errors="ignore"
                )

            # EXCEL

            else:

                df = pd.read_excel(file)

            process_dataframe(df)

        except Exception as e:

            print(e)

    return home()


# UPDATE CALLS

@app.route("/update_calls", methods=["POST"])
def update_calls():

    global all_data

    for item in all_data:

        key = f'calls_{item["id"]}'

        if key in request.form:

            try:

                item["calls"] = int(

                    request.form.get(key)

                )

            except:

                item["calls"] = 0

    return home()


# REMOVE ALL DATA

@app.route("/clear", methods=["POST"])
def clear():

    global all_data

    all_data.clear()

    return home()


# PROCESS DATA

def process_dataframe(df):

    global all_data

    possible_campaign_cols = [

        'ï»¿"Campaign name"',

        '"Campaign name"',

        'Campaign name'

    ]

    campaign_col = None

    for col in possible_campaign_cols:

        if col in df.columns:

            campaign_col = col

            break

    if campaign_col is None:

        campaign_col = df.columns[0]

    for _, row in df.iterrows():

        try:

            campaign_name = str(

                row.get(
                    campaign_col,
                    "Campaign"
                )

            )

            spend = float(

                row.get(
                    "Amount spent (USD)",
                    0
                )

            ) * USD_TO_INR

            # DATE FORMAT

            date = pd.to_datetime(

                row.get(
                    "Day",
                    "-"
                )

            ).strftime("%Y-%m-%d")

            campaign_type = (

                "LEADS"

                if "lead"
                in campaign_name.lower()

                else "ENGAGEMENT"

            )

            all_data.append({

                "id":
                len(all_data),

                "name":
                campaign_name,

                "type":
                campaign_type,

                "spend":
                round(spend, 2),

                "date":
                date,

                "calls":
                0

            })

        except Exception as e:

            print(e)


# RUN APP

if __name__ == "__main__":

    app.run(
        debug=True,
        threaded=True
    )