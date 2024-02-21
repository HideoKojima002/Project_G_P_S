import json
import gpxpy.gpx
import dateutil.parser 


def convertor_to_gpx():
    with open("Архив данных/ID496_2024-02-11-tracking.json", "r", encoding='utf-8') as f:  # input file
        data = json.load(f)

    filename = f.name.replace('.json', '.gpx')
    gpx = gpxpy.gpx.GPX()
    gpx_track = gpxpy.gpx.GPXTrack()
    gpx.tracks.append(gpx_track)
    gpx_segment = gpxpy.gpx.GPXTrackSegment()
    gpx_track.segments.append(gpx_segment)

    for item in data["result"]:
        lat = item["latitude"]
        lat_deg = int(lat // 100)
        lat_min = lat % 100
        lat_dec = lat_deg + lat_min / 60
        if item["NS"] == "S":
            lat_dec = -lat_dec

        lon = item["longitude"]
        lon_deg = int(lon // 100)
        lon_min = lon % 100
        lon_dec = lon_deg + lon_min / 60
        if item["EW"] == "W":
            lon_dec = -lon_dec

        speed = item["Speed,km/h"] / 3.6
        # speed = float(item["Speed,km/h"])
        # speed = item["Speed,knots"] * 0.514444
        date_time = dateutil.parser.parse(item["date"] + " " + item["time"])
        gpx_point = gpxpy.gpx.GPXTrackPoint(lat_dec, lon_dec, speed=speed, time=date_time)
        gpx_segment.points.append(gpx_point)

    with open(filename, "w", encoding='utf-8') as f:  # output file
        f.write(gpx.to_xml())


def main():
    convertor_to_gpx()


if __name__ == '__main__':
    main()
