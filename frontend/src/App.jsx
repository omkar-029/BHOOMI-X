import MapView from "./MapView";
import { useEffect, useState } from "react";
function App() {
  const [stats, setStats] = useState(null);
  const [reviewParcel, setReviewParcel] = useState(null);
  const [decision, setDecision] = useState(null);
  useEffect(() => {
  fetch("http://127.0.0.1:8000/stats")
    .then((response) => response.json())
    .then((data) => setStats(data))
    .catch((error) => console.error(error));
    }, []);
    
  return (
    
    <div>
      <header>
        <h1>BHOOMI-X</h1>
        <p>Intelligent Geospatial Data Harmonization Engine</p>
      </header>

      <main>
        <section>
          <h2>Dashboard Overview</h2>

          <div>
            <div>
              <h3>{stats?.total_parcels ?? 0}</h3>
              <p>Total Parcels</p>
            </div>

            <div>
              <h3>{stats?.officer_reviews ?? 0}</h3>
              <p>Officer Reviews</p>
            </div>

            <div>
              <h3>{stats?.auto_cleared ?? 0}</h3>
              <p>Auto Cleared</p>
            </div>
          </div>
        </section>

        <section>
          <h2>Conflict Overview</h2>
          <section>
  <h2>Geospatial Parcel Map</h2>
  <MapView />
</section>

          <div>
            <p>Owner Conflicts: <strong>{stats?.owner_conflicts ?? 0}</strong></p>
            <p>Area Conflicts: <strong>{stats?.area_conflicts ?? 0}</strong></p>
            <p>Geometry Conflicts: <strong>{stats?.geometry_conflicts ?? 0}</strong></p>
          </div>
        </section>

        <section>
          <h2>Officer Review Queue</h2>

          <table>
            <thead>
              <tr>
                <th>Parcel ID</th>
                <th>Issue</th>
                <th>Confidence</th>
                <th>Priority</th>
                <th>Action</th>
              </tr>
            </thead>

            <tbody>
             <tr>
   <td
  onClick={() =>
    window.dispatchEvent(
      new CustomEvent("bhoomi-focus-parcel", { detail: "P0006" })
    )
  }
  style={{ cursor: "pointer", color: "#2563eb", fontWeight: "600" }}
>
  P0006
</td>
                <td>Owner Conflict</td>
                <td>80%</td>
               <td>{decision === "Approved" ? "Approved" : "Medium"}</td>
             <td><button onClick={() => setReviewParcel("P0006")}>Review</button></td>
              </tr>

              <tr>
                <td
  onClick={() =>
    window.dispatchEvent(
      new CustomEvent("bhoomi-focus-parcel", { detail: "P0016" })
    )
  }
  style={{ cursor: "pointer", color: "#2563eb", fontWeight: "600" }}
>
  P0016
</td>
                <td>Owner Conflict</td>
                <td>80%</td>
                <td>Medium</td>
              </tr>

              <tr>
                <td
  onClick={() =>
    window.dispatchEvent(
      new CustomEvent("bhoomi-focus-parcel", { detail: "P0041" })
    )
  }
  style={{ cursor: "pointer", color: "#2563eb", fontWeight: "600" }}
>
  P0041
</td>
                <td>Geometry Conflict</td>
                <td>78%</td>
                <td>High</td>
              </tr>

              <tr>
                <td
  onClick={() =>
    window.dispatchEvent(
      new CustomEvent("bhoomi-focus-parcel", { detail: "P0031" })
    )
  }
  style={{ cursor: "pointer", color: "#2563eb", fontWeight: "600" }}
>
  P0031
</td>
                <td>Area Conflict</td>
                <td>82%</td>
                <td>Medium</td>
              </tr>
            </tbody>
          </table>
        </section>
     {reviewParcel && (
  <section>
    <h2>Officer Review</h2>
   <p><strong>Parcel:</strong> {reviewParcel} | <strong>Issue:</strong> Owner Conflict | <strong>Confidence:</strong> 80% | <strong>Action:</strong> Verify ownership documents.</p>
  {decision && <p><strong>Status:</strong> {decision}</p>}
  <button onClick={() => { setDecision("Approved"); setReviewParcel(null); }}>Approve</button>
    <button onClick={() => setReviewParcel(null)}>Close</button>
  </section>
)}
      </main>
     
    </div>
  )
}

export default App