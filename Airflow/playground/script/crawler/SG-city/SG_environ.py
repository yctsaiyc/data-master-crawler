import sys
import os
import requests
import json
import pandas as pd
from datetime import datetime, timedelta
import pytz


def get_items_df(data_json, sublist_name):
    item_list = list()

    for i in data_json["items"]:
        for sub_dict in i[sublist_name]:
            sub_dict.update({k: v for k, v in i.items() if k != sublist_name})
            item_list.append(sub_dict)

    item_df = pd.json_normalize(item_list)
    return item_df


def get_items_df_P(data_json, sublist_name):
    item_df = pd.DataFrame()

    for i in data_json["items"]:
        item_df_i = pd.DataFrame.from_dict(i[sublist_name])
        item_df_i["timestamp"] = i["timestamp"]
        item_df_i["update_timestamp"] = i["update_timestamp"]
        item_df = pd.concat([item_df, item_df_i])

    return item_df


def get_SG_environ_df(config):
    response = requests.get(config["url"])

    if response.status_code == 200:
        data_json = response.json()
        df = pd.DataFrame()

        if config["name"] == "2-hour-weather-forecast":
            meta_df = pd.json_normalize(data_json["area_metadata"])
            meta_df.rename(columns={"name": "area"}, inplace=True)
            item_df = get_items_df(data_json, "forecasts")
            df = pd.merge(meta_df, item_df, how="right", on="area")

        elif config["name"] == "24-hour-weather-forecast":
            df = get_items_df(data_json, "periods")

        elif config["name"] == "4-day-weather-forecast":
            df = get_items_df(data_json, "forecasts")

        elif config["name"] in [
            "Air-Temperature-across-Singapore",
            "Rainfall-across-Singapore",
            "Relative-Humidity-across-Singapore",
            "Wind-Direction-across-Singapore",
            "Wind-Speed-across-Singapore",
        ]:
            meta_df = pd.json_normalize(data_json["metadata"]["stations"])
            meta_df.rename(columns={"id": "station_id"}, inplace=True)

            # data_json["items"] = [
            #     item
            #     for item in data_json["items"]
            #     if "00:00" in item["timestamp"] or "30:00" in item["timestamp"]
            # ]
            item_df = get_items_df(data_json, "readings")
            if not meta_df.empty and not item_df.empty:
                df = pd.merge(meta_df, item_df, how="right", on="station_id")
                # df["reading_type"] = data_A_Ra_Re_WD_WS["metadata"]["reading_type"]
                df["reading_unit"] = data_json["metadata"]["reading_unit"]

        elif config["name"] in ["PM25", "Pollutant-Standards-Index"]:
            meta_df = pd.json_normalize(data_json["region_metadata"])
            item_df = get_items_df_P(data_json, "readings")
            # Handle history data before 2016-03
            if meta_df.empty:
                item_df["name"] = item_df.index
                missing_cols = [
                    col for col in config["columns"] if col not in item_df.columns
                ]
                for col in missing_cols:
                    item_df[col] = ""
                df = item_df.reindex(columns=config["columns"])
            else:
                df = pd.merge(
                    meta_df,
                    item_df,
                    how="right",
                    left_on="name",
                    right_on=item_df.index,
                )

        elif config["name"] == "Ultra-violet-Index":
            item_list = list()
            for i in data_json["items"]:
                for sub_dict in i["index"]:
                    keys = list(sub_dict.keys())
                    for key in keys:
                        new_key = f"index.{key}"
                        sub_dict[new_key] = sub_dict.pop(key)
                    sub_dict.update({k: v for k, v in i.items() if k != "index"})
                    item_list.append(sub_dict)
            df = pd.json_normalize(item_list)

        df = df.replace("\n", "", regex=True)
        return df

    else:
        print(f"Failed to retrieve data. Status code: {response.status_code}")
        return None


def history_SG_environ(config):
    empty_count = 0
    today = datetime.now().date()
    df = pd.DataFrame()

    while empty_count < 200:
        config["url"] += "?date=" + today.strftime("%Y-%m-%d")
        response = requests.get(config["url"])
        empty_msg = [
            '{"message":"Internal Server Error"}',
            '{"items":[],"api_info":{"status":"healthy"}}',
            '{"items":[],"region_metadata":[],"api_info":{"status":"healthy"}}',
            '{"metadata":{"stations":[]},"items":[],"api_info":{"status":"healthy"}}',
        ]

        if response.text in empty_msg:
            empty_count += 1
        else:
            empty_count = 0
            df = pd.concat([df, get_SG_environ_df(config)], ignore_index=True)

        config["url"] = config["url"].split("?")[0]

        if today.day == 1 and not df.empty:
            print(today)
            csv_file_name = (
                "history_"
                + os.path.basename(config["csv_path"])
                + "_"
                + str(today.strftime("%y"))
                + str(today.month).zfill(2)
                + ".csv"
            )
            csv_path = os.path.join(config["csv_path"], csv_file_name)
            df.to_csv(csv_path, index=False)
            df = pd.DataFrame()

        today -= timedelta(days=1)


if __name__ == "__main__":
    config_file_path = sys.argv[1]
    with open(config_file_path, "r") as file:
        config = json.load(file)

    if len(sys.argv) > 2 and sys.argv[2] == "history":
        history_SG_environ(config)

    else:
        df = get_SG_environ_df(config)

        csv_file_name = (
            os.path.basename(config["csv_path"])
            + "_"
            + datetime.now(pytz.timezone("Asia/Taipei")).strftime("%y%m%d%H%M%S")
            + ".csv"
        )
        csv_path = os.path.join(config["csv_path"], csv_file_name)

        df.to_csv(csv_path, index=False)
