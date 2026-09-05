from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json

try:
    from .main import get_similar_by_song, parseTrackInfo
except ImportError:
    from main import get_similar_by_song, parseTrackInfo


HOST = "127.0.0.1"
PORT = 8000


class ApiHandler(BaseHTTPRequestHandler):
    def _set_headers(self, status=200, content_type="application/json; charset=utf-8"):
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")

    def _write_json(self, status, payload):
        body = json.dumps(payload).encode("utf-8")
        self._set_headers(status)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _read_json(self):
        content_length = int(self.headers.get("Content-Length", "0"))
        if not content_length:
            return {}

        raw_body = self.rfile.read(content_length)
        if not raw_body:
            return {}

        try:
            return json.loads(raw_body.decode("utf-8"))
        except json.JSONDecodeError:
            return None

    def do_OPTIONS(self):
        self._set_headers(204)
        self.end_headers()

    def do_GET(self):
        if self.path == "/api/health":
            self._write_json(200, {"status": "ok", "service": "song-recommender-api"})
            return

        self._write_json(404, {"error": "Not found"})

    def do_POST(self):
        body = self._read_json()
        if body is None:
            self._write_json(400, {"error": "Request body must be valid JSON"})
            return

        if self.path == "/api/parse":
            link = (body.get("link") or "").strip()
            if not link:
                self._write_json(400, {"error": "A link is required"})
                return

            parsed_track = parseTrackInfo(link)
            if not parsed_track:
                self._write_json(400, {"error": "Only Spotify or YouTube links are supported"})
                return

            self._write_json(200, {"track": parsed_track})
            return

        if self.path == "/api/recommendations/genre":
            genre = (body.get("genre") or "").strip()
            if not genre:
                self._write_json(400, {"error": "A genre is required"})
                return

            recommendations = get_recs_by_genre(genre)
            self._write_json(200, {"items": recommendations, "count": len(recommendations)})
            return

        if self.path == "/api/recommendations/song":
            track = body.get("track")
            if isinstance(track, dict) and track.get("name") and track.get("artist"):
                song = {"name": str(track["name"]).strip(), "artist": str(track["artist"]).strip()}
            else:
                link = (body.get("link") or "").strip()
                if not link:
                    self._write_json(400, {"error": "Provide either a track object or a song link"})
                    return

                song = parseTrackInfo(link)
                if not song:
                    self._write_json(400, {"error": "Only Spotify or YouTube links are supported"})
                    return

            recommendations = get_similar_by_song(song)
            self._write_json(200, {"source": song, "items": recommendations, "count": len(recommendations)})
            return

        self._write_json(404, {"error": "Not found"})


def run_server(host=HOST, port=PORT):
    server = ThreadingHTTPServer((host, port), ApiHandler)
    print(f"Backend API running at http://{host}:{port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("Shutting down backend API")
    finally:
        server.server_close()


if __name__ == "__main__":
    run_server()