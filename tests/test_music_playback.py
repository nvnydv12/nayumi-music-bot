"""Offline regression tests; load player definitions without starting Discord or databases."""
import ast
import asyncio
import re
import time
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock


source = Path(__file__).resolve().parents[1].joinpath('music_cog.py').read_text(encoding='utf-8')
tree = ast.parse(source)
nodes = [ast.ImportFrom(module='__future__', names=[ast.alias(name='annotations')], level=0)]
nodes.extend(n for n in tree.body if isinstance(n, ast.ClassDef) and n.name in {'Track', 'GuildPlayer'})
cog = next(n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == 'MusicCog')
methods = [n for n in cog.body if isinstance(n, ast.AsyncFunctionDef) and n.name in {'search_track', 'resolve_stream'}]
nodes.extend(methods)
scope = dict(asyncio=asyncio, re=re, time=time, is_247=lambda _: False,
             is_vc_connected=lambda vc: vc is not None,
             get_fast_reliable_thumbnail=lambda thumb, *_: thumb)
exec(compile(ast.fix_missing_locations(ast.Module(body=nodes, type_ignores=[])), '<music definitions>', 'exec'), scope)
GuildPlayer, Track = scope['GuildPlayer'], scope['Track']


def track(name='seed'):
    return Track(name, 'https://youtube.com/watch?v=' + name, 'Artist', 180, '', None)


class PlaybackTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.cog = SimpleNamespace(find_autoplay_track=AsyncMock(), update_voice_channel_status=AsyncMock())
        self.p = GuildPlayer(SimpleNamespace(loop=asyncio.get_running_loop(), user=None),
                             SimpleNamespace(id=1, voice_client=None), self.cog)
        self.p.current = track()
        self.p.autoplay = True
        self.p.start_idle_timer = Mock()
        self.p.play_track = AsyncMock()

    async def test_prefetch_does_not_reserve_unplayed_song(self):
        candidate = track('next')
        self.cog.find_autoplay_track.return_value = candidate
        await self.p.prefetch_autoplay()
        self.assertIs(self.p.prefetched_autoplay, candidate)
        self.assertEqual(self.p.played_uris, set())

    async def test_stop_during_lookup_never_restarts(self):
        started, release = asyncio.Event(), asyncio.Event()
        async def lookup(*args, **kwargs):
            started.set()
            await release.wait()
            return track('next')
        self.cog.find_autoplay_track.side_effect = lookup
        advance = asyncio.create_task(self.p.play_next())
        await started.wait()
        self.p.stop_playback()
        release.set()
        await advance
        self.p.play_track.assert_not_awaited()
        self.assertIsNone(self.p.prefetched_autoplay)

    async def test_manual_queue_wins_during_lookup(self):
        requested = track('requested')
        async def lookup(*args, **kwargs):
            self.p.queue.append(requested)
            return track('auto')
        self.cog.find_autoplay_track.side_effect = lookup
        await self.p.play_next()
        self.p.play_track.assert_awaited_once_with(requested)

    async def test_duplicate_completion_only_advances_once(self):
        self.p._finish_track = AsyncMock()
        await asyncio.gather(self.p.on_track_end(0), self.p.on_track_end(0))
        self.p._finish_track.assert_awaited_once()

    async def test_stale_prefetch_is_discarded(self):
        async def lookup(*args, **kwargs):
            self.p.current = track('replacement')
            return track('old-recommendation')
        self.cog.find_autoplay_track.side_effect = lookup
        await self.p.prefetch_autoplay()
        self.assertIsNone(self.p.prefetched_autoplay)

    async def test_failed_audio_does_not_repeat_track_loop(self):
        self.p.voice_client = Mock()
        self.p.loop_mode = 'track'
        self.p.play_next = AsyncMock()
        self.p.start_time = time.time()
        await self.p._finish_track()
        self.p.play_next.assert_awaited_once()
        self.p.play_track.assert_not_awaited()

    async def test_saavn_cached_stream_is_rejected(self):
        old = track()
        old.uri = 'https://www.jiosaavn.com/song/old'
        old.direct_url = 'https://cdn.example/audio'
        old.direct_url_time = time.time()
        result = await scope['resolve_stream'](None, old)
        self.assertIsNone(result)

    async def test_expired_stream_refreshes_exact_source(self):
        old = track()
        old.direct_url = 'https://expired.example/audio'
        old.direct_url_time = time.time() - 600
        extractor = Mock()
        extractor.extract_info.return_value = {'url': 'https://fresh.example/audio', 'duration': 180}
        context = Mock()
        context.__enter__ = Mock(return_value=extractor)
        context.__exit__ = Mock(return_value=False)
        scope.update(yt_dlp=SimpleNamespace(YoutubeDL=Mock(return_value=context)),
                     get_ytdl_opts=lambda *a, **k: {}, get_ytdl_cookie_file=lambda: None)
        original_uri = old.uri
        result = await scope['resolve_stream'](None, old)
        self.assertEqual(result, 'https://fresh.example/audio')
        extractor.extract_info.assert_called_once_with(original_uri, download=False)

    async def test_soundcloud_search_preserves_source_and_artwork(self):
        entry = {'id': '12345', 'url': 'https://soundcloud.com/artist/song',
                 'title': 'Song', 'uploader': 'Artist', 'duration': 180,
                 'thumbnail': 'https://images.example/art.jpg'}
        extractor = Mock()
        extractor.extract_info.return_value = entry
        context = Mock()
        context.__enter__ = Mock(return_value=extractor)
        context.__exit__ = Mock(return_value=False)
        scope.update(yt_dlp=SimpleNamespace(YoutubeDL=Mock(return_value=context)),
                     get_ytdl_opts=lambda *a, **k: {})
        found = await scope['search_track'](None, entry['url'], None)
        self.assertEqual(found.uri, entry['url'])
        self.assertEqual(found.thumbnail, entry['thumbnail'])

    async def test_three_failed_streams_stop_autoplay_retries(self):
        self.p.voice_client = Mock()
        self.p.play_next = AsyncMock()
        for _ in range(3):
            await self.p._finish_track(RuntimeError('unavailable'))
        self.assertFalse(self.p.autoplay)

    async def test_explicit_soundcloud_search_never_uses_youtube(self):
        extractor = Mock()
        extractor.extract_info.return_value = {'entries': [{
            'id': '123', 'url': 'https://soundcloud.com/artist/song',
            'title': 'Song', 'duration': 180}]}
        context = Mock()
        context.__enter__ = Mock(return_value=extractor)
        context.__exit__ = Mock(return_value=False)
        scope.update(yt_dlp=SimpleNamespace(YoutubeDL=Mock(return_value=context)),
                     get_sc_opts=lambda *a, **k: {}, is_unwanted_remake=lambda *a: False)
        result = await scope['search_track'](None, 'scsearch:Song', None)
        self.assertEqual(result.uri, 'https://soundcloud.com/artist/song')
        extractor.extract_info.assert_called_once_with('scsearch5:Song', download=False)

    async def test_loading_state_resets_after_error(self):
        self.p._play_track = AsyncMock(side_effect=RuntimeError('broken stream'))
        with self.assertRaises(RuntimeError):
            await GuildPlayer.play_track(self.p, track())
        self.assertFalse(self.p.is_loading)


if __name__ == '__main__':
    unittest.main()
