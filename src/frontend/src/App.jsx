//this is the main webpage used as the display
import { useEffect, useState } from "react";

async function requestJson(url, options = {}) {
  const response = await fetch(url, {
    headers: {
      "Content-Type": "application/json",
      ...(options.headers || {}),
    },
    ...options,
  });

  const payload = await response.json().catch(() => ({}));
  if (!response.ok) {
    throw new Error(payload.error || "Request failed");
  }

  return payload;
}

//would want to use this to show the cards and then put it in a list
//add cover to the function parameters and add the <img> tag under "track-list"
function TrackList({ title, count, items,}) {
  return (
    <div className="results">
      <div className="result-head">
        <h2>{title}</h2>
        <span>{count} tracks</span>
      </div>

      {items.length ? (
        <div className="track-list">
          {items.map((item, index) => (
            <article className="track-card" key={`${item.artist}-${item.name}-${index}`}>
              <img src={item.cover} alt={`${item.name} cover`} />
              <h3>{item.name}</h3>
              <p>{item.artist}</p>
            </article>
          ))}
        </div>
      ) : (
        <div className="empty-state">No recommendations yet. Use one of the forms to load tracks.</div>
      )}
    </div>
  );
}

export default function App() {
  const [health, setHealth] = useState("checking");
  const [genre, setGenre] = useState("");
  const [songLink, setSongLink] = useState("");
  const [items, setItems] = useState([]);
  const [title, setTitle] = useState("Recommendations");
  const [count, setCount] = useState(0);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    let isMounted = true;

    requestJson("/api/health")
      .then(() => {
        if (isMounted) {
          setHealth("online");
        }
      })
      .catch(() => {
        if (isMounted) {
          setHealth("offline");
        }
      });

    return () => {
      isMounted = false;
    };
  }, []);

  async function loadGenreRecommendations(event) {
    event.preventDefault();
    setLoading(true);
    setError("");

    try {
      const payload = await requestJson("/api/recommendations/genre", {
        method: "POST",
        body: JSON.stringify({ genre }),
      });

      setTitle(`Genre: ${genre}`);
      setItems(payload.items || []);
      setCount(payload.count || 0);
    } catch (requestError) {
      setError(requestError.message);
    } finally {
      setLoading(false);
    }
  }

  async function loadSongRecommendations(event) {
    event.preventDefault();
    setLoading(true);
    setError("");

    try {
      const payload = await requestJson("/api/recommendations/song", {
        method: "POST",
        body: JSON.stringify({ link: songLink }),
      });

      const source = payload.source ? `${payload.source.name} - ${payload.source.artist}` : "Song";
      setTitle(`Similar to ${source}`);
      setItems(payload.items || []);
      setCount(payload.count || 0);
    } catch (requestError) {
      setError(requestError.message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="app-shell">
      <div className="content">
        <section className="hero">
          <div className={`hero-badge ${health === "online" ? "ok" : health === "offline" ? "error" : ""}`}>
            Backend {health}
          </div>
          <h1>&lt;Insert Title Here&gt;</h1>
          <p>
            This template uses React on the client and a lightweight Python JSON API on the backend.
            Requests are sent to <strong>/api</strong>, so the frontend can talk to the backend without hard-coded hosts.
          </p>
        </section>

        <section className="grid">
          <div className="panel">
            <div className="panel-body stack">
              <form className="stack" onSubmit={loadSongRecommendations}>
                <div className="field">
                  <label htmlFor="songLink">Song link</label>
                  <input
                    id="songLink"
                    name="songLink"
                    value={songLink}
                    onChange={(event) => setSongLink(event.target.value)}
                    placeholder="Paste a Spotify or YouTube link"
                  />
                </div>

                <div className="button-row">
                  <button type="submit" className="secondary" disabled={loading}>
                    {loading ? "Loading..." : "Find similar songs"}
                  </button>
                </div>
              </form>

              {error ? <div className="status error"><strong>Error:</strong> {error}</div> : null}
            </div>
          </div>

          <div className="panel">
            <div className="panel-body">
              <TrackList title={title} count={count} items={items} />
            </div>
          </div>
        </section>
      </div>
    </main>
  );
}