from src.components import Harvester


class FixMyStreetHistoryHarvester(Harvester):
    def run(self, source, fixmystreet_incidents):
        print(source, fixmystreet_incidents)
        if not source or not fixmystreet_incidents:
            print("[Harvester] Pas assez de versions précédentes pour comparaison.")
            return source.data.get("features", [])

        previous_version = fixmystreet_incidents[0]

        print(f"[Harvester] Source date: {source.date}")
        print(f"[Harvester] Previous version date: {previous_version.date}")

        current_features = source.data.get("features", [])
        previous_features = previous_version.data.get("features", [])

        print(f"[Harvester] Nb features actuelles : {len(current_features)}")
        print(f"[Harvester] Nb features précédentes : {len(previous_features)}")

        previous_map = {f["properties"]["id"]: f for f in previous_features}

        for feature in current_features:
            props = feature["properties"]
            fid = props["id"]

            prev = previous_map.get(fid)

            if prev:
                prev_props = prev["properties"]
                if props["updatedDate"] != prev_props["updatedDate"]:
                    feature["history"] = {
                        "issueId": fid,
                        "newStatus": props["status"],
                        "newDate": props["updatedDate"],
                        "oldStatus": prev_props["status"],
                        "oldDate": prev_props["updatedDate"]
                    }
                    print(f"[History] ID {fid} → changement détecté.")
                else:
                    feature["history"] = None
            else:
                feature["history"] = None

        print(f"[Harvester] Features retournées : {len(current_features)}")
        return current_features
