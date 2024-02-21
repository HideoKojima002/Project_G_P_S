import json
import pandas as pd
import folium
import geopy.distance
import datetime


"""
Внимание! Если средняя скорость не совпадает с средней скоростью при парсинге JSONа, 
учитывайте тот факт, что время входа в зону и сама зона отличается от результата работы данной программы,
ибо тут мы вводим зону вручную, и результат близкий именно к проезду, а не детекции. 
"""


def data_from_zone(filename, zone_lat, zone_lon):
    df = pd.read_json(filename)
    df = df["result"].apply(pd.Series)

    df["latitude"] = df["latitude"].apply(lambda x: int(x // 100) + (x % 100) / 60)
    df["longitude"] = df["longitude"].apply(lambda x: int(x // 100) + (x % 100) / 60)

    df.loc[df["NS"] == "S", "latitude"] = -df["latitude"]
    df.loc[df["EW"] == "W", "longitude"] = -df["longitude"]

    df["speed"] = df["Speed,km/h"] / 3.6

    df["datetime"] = pd.to_datetime(df["date"] + " " + df["time"])

    df = df.drop(columns=["NS", "EW", "date", "time", "Speed,km/h"])

    zone_radius = 9  # Радиус зоны в метрах

    # создаем карту с центром в зоне
    m = folium.Map(location=[zone_lat, zone_lon], zoom_start=12)

    # круг зоны
    folium.Circle(
        location=[zone_lat, zone_lon],
        radius=zone_radius,
        color="red",
        fill=True,
        fill_color="red",
        fill_opacity=0.2
    ).add_to(m)

    # добавляем линию, обозначающую траекторию движения
    folium.PolyLine(
        locations=df[["latitude", "longitude"]].values.tolist(),
        color="blue",
        weight=3
    ).add_to(m)

    # вычисляем расстояние от каждой точки до центра зоны
    df["distance"] = df.apply(lambda x: geopy.distance.distance((x["latitude"], x["longitude"]), (zone_lat, zone_lon)).meters, axis=1)

    # определяем, находится ли точка внутри зоны
    df["in_zone"] = df["distance"] <= zone_radius

    df["direction"] = df["in_zone"].diff().map({True: "entry", False: "exit", None: None})

    total_time = df.loc[df["in_zone"], "datetime"].diff().sum()

    # количество проездов сквозь зону
    count = df["direction"].value_counts().get("entry", 0)

    df["datetime_utc+5"] = df["datetime"].dt.tz_localize("UTC").dt.tz_convert("Etc/GMT-5")
    df["datetime_utc+5_str"] = df["datetime_utc+5"].dt.strftime("%H:%M:%S")  # ("%Y-%m-%d %H:%M:%S")

    last_entry = df.loc[df["direction"] == "entry", "datetime_utc+5_str"].max()
    last_exit = df.loc[df["direction"] == "exit", "datetime_utc+5_str"].max()

    avg_speed = df.loc[df["in_zone"], "speed"].mean() * 3.6  # умножаем на 3.6 для перевода в км/ч
    max_speed = df.loc[df["in_zone"], "speed"].max() * 3.6
    min_speed = df.loc[df["in_zone"], "speed"].min() * 3.6
    distance = df.loc[df["in_zone"], "speed"].mul(df.loc[df["in_zone"], "datetime"].diff().dt.total_seconds()).sum()

    # df_entries_exits = df.groupby("direction")["datetime_utc+5"].apply(list).apply(pd.Series).T

    # print(f"Общее время в зоне: {total_time}")
    print(f"Общее количество входов и выходов в зоне: {int(count)}")
    print(f"Общее количество проездов в зоне: {int(count / 2)}")
    if last_entry is not None:
        print(f"Последний заход из зоны: {last_entry}")
    if last_exit is not None:
        print(f"Последний выход из зоны: {last_exit}")
    print(f"Минмальная скорость в зоне: {min_speed:.2f} км/ч")
    print(f"Средняя скорость в зоне: {avg_speed:.2f} км/ч")
    print(f"Максимальная скорость в зоне: {max_speed:.2f} км/ч")
    # print(f"Расстояние в зоне: {distance:.2f} m")

    m.save(filename.replace('json', 'html'))

    # todo Если что поставить "datetime_utc+5_str" для норм времени
    entries = df.loc[df["direction"] == "entry", "datetime_utc+5_str"].reset_index(drop=True)
    print(f"Время каждого захода в зону:")
    count = 1
    for i, entry in enumerate(entries):
        if i % 2 == 0:
            # print(f"{count}. Вход в зону в {entry}")  #  print(f"{count}. Вход в зону в {entry}")
            print(f'{entry}')
            count += 1
        # else:            # Если нужны Выходы из зоны то раскомментируйте уберите #
            # print(f'ВЫХОД {entry}')
            # print(f"{i + 1}. Выход из зоны в {entry}")

    count = 1
    df["rolling_in_zone"] = df["in_zone"].rolling(2).sum()
    df["rolling_speed"] = df["speed"].rolling(2).mean() * 3.6
    average_result = []
    min_result = []
    max_result = []
    print(f"Скорость при входе в зону:")
    for i, (entry, speed) in enumerate(zip(entries, df.loc[df["rolling_in_zone"] == 1, "rolling_speed"])):
        if i % 2 == 0:
            # print(f"{count}. {entry} - {speed:.2f} км/ч")
            format_speed = f'{speed:.2f}'.replace('.', ',')
            print(f'{format_speed}')
            count += 1
            # ДЛЯ ПОДСЧЕТА СРЕДНЕЙ СКОРОСТИ
            num_speed = speed
        else:
            # print(f'ВЫХОД {speed:.2f}')
            # num = ((num_speed+speed)/2)
            # average_result.append(num)

            s = pd.Series([speed, num_speed])
            average_speed = s.mean()
            min_speeds = s.min()
            max_speeds = s.max()
            max_result.append(max_speeds)
            min_result.append(min_speeds)
            average_result.append(average_speed)

    print(f'Средняя скорость в зоне')
    for i, el in enumerate(average_result):
        format_speed = f'{el:.2f}'.replace('.', ',')
        # print(f'{i+1}. Средняя скорость - {el:.2f}')
        # print(f'{i + 1}. \t{el:.2f}')
        print(f'{i + 1}. \t{format_speed}')
    # Это вывод скорости при заходе в зону
    # df["speed_kmh"] = df["speed"] * 3.6
    # print(f"Скорость при заходе в зону:")
    # for i, (entry, speed) in enumerate(zip(entries, df.loc[df["direction"] == "entry", "speed_kmh"])):
    #     if i % 2 == 0:
    #         print(f"{int(speed)}")
    print(f'Минимальная скорость в зоне')
    for i, el in enumerate(min_result):
        format_speed = f'{el:.2f}'.replace('.', ',')
        # print(f'{i + 1}. Минимальная скорость - {el:.2f}')
        # print(f'{i + 1}. \t{el:.2f}')
        print(f'{i + 1}. \t{format_speed}')
    print(f'Максимальная скорость в зоне')
    for i, el in enumerate(max_result):
        format_speed = f'{el:.2f}'.replace('.', ',')
        # print(f'{i + 1}. Максимальная скорость - {el:.2f}')
        # print(f'{i + 1}. \t{el:.2f}')
        print(f'{i + 1}. \t{format_speed}')


def main():
    filename = 'Архив данных/ID496_2024-02-10-tracking.json'

    # задаем координаты и радиус зоны. Для (52) - 56.7490955, 60.7504651. Для соседней дороги (53) - 56.749534, 60.750734. (41) 56.783297, 60.781675. (68) 56.899058, 60.766394. (01) 56.955560, 60.608112 Петрова 100% точности. (33) 56.914146, 60.758132
    # zone_lat = 56.749534          # 53
    # zone_lon = 60.750734
    zone_lat = 56.7490955         # 52
    zone_lon = 60.7504651
    # zone_lat = 56.914146
    # zone_lon = 60.758132
    # zone_lat = 56.955560          # 1
    # zone_lon = 60.608112
    # zone_lat = 56.899058          # 68
    # zone_lon = 60.766394
    # zone_lat = 56.783297          # 41
    # zone_lon = 60.781675
    # zone_lat = 56.914146          # 33
    # zone_lon = 60.758132
    data_from_zone(filename, zone_lat, zone_lon)


if __name__ == '__main__':
    main()
