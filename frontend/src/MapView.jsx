import { useEffect, useRef } from "react";
import L from "leaflet";
import "leaflet/dist/leaflet.css";

function parseCSV(text) {
  const rows = [];
  let row = [];
  let value = "";
  let insideQuotes = false;

  for (let i = 0; i < text.length; i++) {
    const char = text[i];
    const next = text[i + 1];

    if (char === '"' && insideQuotes && next === '"') {
      value += '"';
      i++;
    } else if (char === '"') {
      insideQuotes = !insideQuotes;
    } else if (char === "," && !insideQuotes) {
      row.push(value);
      value = "";
    } else if ((char === "\n" || char === "\r") && !insideQuotes) {
      if (char === "\r" && next === "\n") {
        i++;
      }

      row.push(value);
      value = "";

      if (row.some((item) => item.trim() !== "")) {
        rows.push(row);
      }

      row = [];
    } else {
      value += char;
    }
  }

  if (value !== "" || row.length > 0) {
    row.push(value);
    rows.push(row);
  }

  if (rows.length === 0) {
    return [];
  }

  const headers = rows[0];

  return rows.slice(1).map((values) => {
    const record = {};

    headers.forEach((header, index) => {
      record[header] = values[index] || "";
    });

    return record;
  });
}

function getParcelStyle(conflictType) {
  const type = (conflictType || "").toUpperCase();

  if (type.includes("GEOMETRY")) {
    return {
      color: "#dc2626",
      fillColor: "#ef4444",
      fillOpacity: 0.45,
      weight: 2,
    };
  }

  if (type.includes("AREA")) {
    return {
      color: "#ca8a04",
      fillColor: "#facc15",
      fillOpacity: 0.45,
      weight: 2,
    };
  }

  if (type.includes("OWNER")) {
    return {
      color: "#ea580c",
      fillColor: "#fb923c",
      fillOpacity: 0.45,
      weight: 2,
    };
  }

  if (type.includes("MULTIPLE")) {
    return {
      color: "#2563eb",
      fillColor: "#3b82f6",
      fillOpacity: 0.45,
      weight: 2,
    };
  }

  return {
    color: "#16a34a",
    fillColor: "#22c55e",
    fillOpacity: 0.18,
    weight: 1,
  };
}

function MapView() {
  const mapRef = useRef(null);
const parcelsLayerRef = useRef(null);
  useEffect(() => {
    let cancelled = false;
    if (mapRef.current) {
      return;
    }

    const map = L.map("bhoomi-map").setView([20.0015, 73.006], 15);

    L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
      attribution: "&copy; OpenStreetMap contributors",
    }).addTo(map);

    Promise.all([
      fetch("/ground_truth.geojson").then((response) => response.json()),
      fetch("/unified_conflict_report.csv").then((response) =>
        response.text()
      ),
      fetch("/resolution_recommendations.csv").then((response) =>
        response.text()
      ),
      fetch("/confidence_results.csv").then((response) =>
        response.text()
      ),
    ])
      .then(([geojson, unifiedCSV, resolutionCSV, confidenceCSV]) => {
        if (cancelled) return;
        const unifiedRecords = parseCSV(unifiedCSV);
        const resolutionRecords = parseCSV(resolutionCSV);
        const confidenceRecords = parseCSV(confidenceCSV);

        const resolutionMap = new Map(
          resolutionRecords.map((record) => [record.parcel_id, record])
        );

        const confidenceMap = new Map(
          confidenceRecords.map((record) => [record.parcel_id, record])
        );

        const conflictMap = new Map(
          unifiedRecords.map((record) => [record.parcel_id, record])
        );

        const parcelsLayer = L.geoJSON(geojson, {
          style: (feature) => {
            const parcelId = feature.properties?.parcel_id;
            const conflict = conflictMap.get(parcelId);

            return getParcelStyle(conflict?.conflict_type);
          },

          onEachFeature: (feature, layer) => {
            const properties = feature.properties || {};
            const parcelId = properties.parcel_id;

            const conflict = conflictMap.get(parcelId);
            const resolution = resolutionMap.get(parcelId);
            const confidence = confidenceMap.get(parcelId);

            const conflictType =
              conflict?.conflict_type || "NO CONFLICT";

            const recommendation =
              resolution?.recommended_action || "NO ACTION";

            const explanation =
              resolution?.explanation ||
              conflict?.recommendation ||
              "No significant conflict detected.";

            const confidenceScore =
              confidence?.confidence_score || "N/A";

            const confidenceLevel =
              confidence?.confidence_level || "N/A";

            const popup = `
              <div style="min-width: 240px;">
                <h3 style="margin: 0 0 10px; color: #123b5d;">
                  BHOOMI-X Parcel
                </h3>

                <p><strong>Parcel ID:</strong> ${
                  parcelId || "N/A"
                }</p>

                <p><strong>Survey No:</strong> ${
                  properties.survey_no || "N/A"
                }</p>

                <p><strong>Owner:</strong> ${
                  properties.owner_name || "N/A"
                }</p>

                <p><strong>Area:</strong> ${
                  properties.area_sqm || "N/A"
                } sq.m</p>

                <hr />

                <p><strong>Conflict:</strong> ${conflictType}</p>

                <p><strong>Confidence:</strong> ${
                  confidenceScore
                }% (${confidenceLevel})</p>

                <p><strong>Recommended Action:</strong><br />
                  ${recommendation}
                </p>

                <p><strong>Explanation:</strong><br />
                  ${explanation}
                </p>
              </div>
            `;

            layer.bindPopup(popup);

            layer.on({
              mouseover: (event) => {
                event.target.setStyle({
                  weight: 3,
                  fillOpacity: 0.65,
                });
              },

              mouseout: (event) => {
                parcelsLayer.resetStyle(event.target);
              },
            });
          },
        }).addTo(map);
        parcelsLayerRef.current = parcelsLayer;

        map.fitBounds(parcelsLayer.getBounds());
      })
      .catch((error) => {
        console.error(
          "Failed to load BHOOMI-X parcel data:",
          error
        );
      });

    mapRef.current = map;
    const focusParcel = (event) => {
  const parcelId = event.detail;

  if (!parcelsLayerRef.current) {
    return;
  }

  parcelsLayerRef.current.eachLayer((layer) => {
    const layerParcelId = layer.feature?.properties?.parcel_id;

    if (layerParcelId === parcelId) {
      map.fitBounds(layer.getBounds(), {
        padding: [50, 50],
        maxZoom: 18,
      });

      layer.openPopup();
    }
  });
};

window.addEventListener("bhoomi-focus-parcel", focusParcel);

    return () => {
        cancelled = true;
  window.removeEventListener("bhoomi-focus-parcel", focusParcel);
  map.remove();
  mapRef.current = null;
  parcelsLayerRef.current = null;
};
}, []);
 return (
  <div
    style={{
      position: "relative",
      width: "100%",
    }}
  >
    <div
      id="bhoomi-map"
      style={{
        height: "500px",
        width: "100%",
        borderRadius: "12px",
        overflow: "hidden",
      }}
    />

    <div
      style={{
        position: "absolute",
        bottom: "20px",
        right: "20px",
        zIndex: 1000,
        background: "white",
        padding: "14px 16px",
        borderRadius: "10px",
        boxShadow: "0 2px 10px rgba(0,0,0,0.2)",
        fontSize: "14px",
        lineHeight: "1.8",
      }}
    >
      <strong>Map Legend</strong>

      <div>🟢 No Conflict</div>
      <div>🟠 Owner Conflict</div>
      <div>🟡 Area Conflict</div>
      <div>🔴 Geometry Conflict</div>
      <div>🔵 Multiple Conflicts</div>
       </div>
  </div>
);
}
export default MapView;