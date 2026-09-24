import os
import aiohttp
from typing import List, Dict, Optional, Any

DEFAULT_LASTFM_KEY = "892ec4bdf3b1ea3aa74353988aaa4ee1"
BASE_URL = "http://ws.audioscrobbler.com/2.0/"


class LastFMClient:
    """
    Asynchronous Last.fm API client ported from Groove-Music's LastFM helper.
    Provides musical similarity graphs, artist relations, and top tracks.
    """

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("LASTFM_API_KEY") or DEFAULT_LASTFM_KEY

    async def _get(self, params: Dict[str, Any], timeout_sec: float = 6.0) -> Optional[Dict[str, Any]]:
        if not self.api_key:
            return None
        params["api_key"] = self.api_key
        params["format"] = "json"
        headers = {
            "User-Agent": "Nayumi-MusicBot/2.0 (LastFM Recommendation Engine)"
        }
        try:
            timeout = aiohttp.ClientTimeout(total=timeout_sec)
            async with aiohttp.ClientSession() as session:
                async with session.get(BASE_URL, params=params, headers=headers, timeout=timeout) as resp:
                    if resp.status == 200:
                        return await resp.json()
        except Exception as e:
            # Silent fallback on network / timeout errors
            pass
        return None

    async def search_artist(self, artist: str) -> Optional[Dict[str, Any]]:
        """Searches for an artist to obtain canonical name and metadata."""
        if not artist or not self.api_key:
            return None
        data = await self._get({
            "method": "artist.search",
            "artist": artist,
            "limit": 1
        })
        if not data:
            return None
        try:
            matches = data.get("results", {}).get("artistmatches", {}).get("artist")
            if isinstance(matches, list) and matches:
                return matches[0]
            elif isinstance(matches, dict):
                return matches
        except Exception:
            pass
        return None

    async def get_similar_tracks(self, artist: str, track: str, limit: int = 10) -> List[Dict[str, str]]:
        """
        Fetches tracks similar to the given artist and track title.
        Returns a list of dicts: [{"title": "...", "author": "..."}]
        """
        if not self.api_key or not track:
            return []
        params = {
            "method": "track.getsimilar",
            "track": track,
            "limit": limit
        }
        if artist:
            params["artist"] = artist

        data = await self._get(params)
        if not data:
            return []

        results = []
        try:
            tracks = data.get("similartracks", {}).get("track", [])
            if isinstance(tracks, dict):
                tracks = [tracks]
            for t in tracks:
                name = t.get("name")
                art_name = t.get("artist", {}).get("name") if isinstance(t.get("artist"), dict) else str(t.get("artist") or "")
                if name and art_name:
                    results.append({
                        "title": name,
                        "author": art_name
                    })
        except Exception:
            pass
        return results

    async def get_similar_artists(self, artist: str, limit: int = 5) -> List[str]:
        """
        Fetches artists musically similar to the given artist.
        Returns a list of artist name strings.
        """
        if not self.api_key or not artist:
            return []

        search_res = await self.search_artist(artist)
        target_artist = search_res.get("name") if (search_res and search_res.get("name")) else artist

        data = await self._get({
            "method": "artist.getsimilar",
            "artist": target_artist,
            "limit": limit,
            "autocorrect": 1
        })
        if not data:
            return []

        results = []
        try:
            artists = data.get("similarartists", {}).get("artist", [])
            if isinstance(artists, dict):
                artists = [artists]
            for a in artists:
                name = a.get("name")
                if name:
                    results.append(name)
        except Exception:
            pass
        return results

    async def get_top_tracks(self, artist: str, limit: int = 5) -> List[Dict[str, str]]:
        """
        Fetches the top tracks for a given artist.
        Returns a list of dicts: [{"title": "...", "author": "..."}]
        """
        if not self.api_key or not artist:
            return []

        data = await self._get({
            "method": "artist.gettoptracks",
            "artist": artist,
            "limit": limit,
            "autocorrect": 1
        })
        if not data:
            return []

        results = []
        try:
            tracks = data.get("toptracks", {}).get("track", [])
            if isinstance(tracks, dict):
                tracks = [tracks]
            for t in tracks:
                name = t.get("name")
                art_name = t.get("artist", {}).get("name") if isinstance(t.get("artist"), dict) else str(t.get("artist") or artist)
                if name:
                    results.append({
                        "title": name,
                        "author": art_name or artist
                    })
        except Exception:
            pass
        return results

    async def get_top_tracks_by_tag(self, tag: str, limit: int = 10) -> List[Dict[str, str]]:
        """
        Fetches top tracks associated with a musical genre or tag.
        Returns a list of dicts: [{"title": "...", "author": "..."}]
        """
        if not self.api_key or not tag:
            return []

        data = await self._get({
            "method": "tag.gettoptracks",
            "tag": tag,
            "limit": limit
        })
        if not data:
            return []

        results = []
        try:
            tracks = data.get("tracks", {}).get("track", [])
            if isinstance(tracks, dict):
                tracks = [tracks]
            for t in tracks:
                name = t.get("name")
                art_name = t.get("artist", {}).get("name") if isinstance(t.get("artist"), dict) else str(t.get("artist") or "")
                if name:
                    results.append({
                        "title": name,
                        "author": art_name
                    })
        except Exception:
            pass
        return results


# Global singleton instance for high performance
lastfm_client = LastFMClient()
