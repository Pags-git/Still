"""Plain-text SRT/WebVTT reading and seek-safe cue lookup."""
from bisect import bisect_right
from dataclasses import dataclass
from html.parser import HTMLParser
from pathlib import Path
import re


@dataclass(frozen=True)
class Cue:
    start: int
    end: int
    text: str


class PlainText(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.parts = []

    def handle_data(self, data):
        self.parts.append(data)

    def handle_starttag(self, tag, attrs):
        if tag.lower() == 'br':
            self.parts.append('\n')


TIME = r'(?:(\d{1,3}):)?(\d{2}):(\d{2})[,.](\d{3})'
TIMING = re.compile(r'^\s*' + TIME + r'\s*-->\s*' + TIME + r'(?:\s+.*)?$')


def milliseconds(parts):
    hours, minutes, seconds, fraction = parts
    if int(minutes) >= 60 or int(seconds) >= 60:
        raise ValueError('Invalid subtitle timestamp')
    return ((int(hours or 0) * 60 + int(minutes)) * 60 + int(seconds)) * 1000 + int(fraction)


def parse_subtitles(text):
    cues = []
    text = text.lstrip('\ufeff').replace('\r\n', '\n').replace('\r', '\n')
    for block in re.split(r'\n[ \t]*\n', text):
        lines = block.strip().splitlines()
        if not lines or lines[0].startswith(('WEBVTT', 'NOTE', 'STYLE', 'REGION')):
            continue
        for index, line in enumerate(lines):
            match = TIMING.match(line)
            if not match:
                continue
            start = milliseconds(match.groups()[:4])
            end = milliseconds(match.groups()[4:])
            plain = PlainText()
            plain.feed('\n'.join(lines[index + 1:]))
            content = ''.join(plain.parts).strip()
            if end <= start:
                raise ValueError('A subtitle ends before it starts')
            if content:
                cues.append(Cue(start, end, content))
            break
    if not cues:
        raise ValueError('No readable subtitle cues found. Choose an SRT or VTT file.')
    return sorted(cues, key=lambda cue: (cue.start, cue.end))


class SubtitleTrack:
    def __init__(self, cues):
        self.cues = cues
        self.starts = [cue.start for cue in cues]
        self.max_ends = []
        latest = 0
        for cue in cues:
            latest = max(latest, cue.end)
            self.max_ends.append(latest)

    @classmethod
    def load(cls, filename):
        data = Path(filename).read_bytes()
        if data.startswith((b'\xff\xfe', b'\xfe\xff')):
            text = data.decode('utf-16')
        else:
            try:
                text = data.decode('utf-8-sig')
            except UnicodeDecodeError:
                text = data.decode('cp1252')
        return cls(parse_subtitles(text))

    def text_at(self, position):
        index = bisect_right(self.starts, position) - 1
        active = []
        while index >= 0 and self.max_ends[index] > position:
            cue = self.cues[index]
            if cue.start <= position < cue.end:
                active.append(cue.text)
            index -= 1
        return '\n'.join(reversed(active))


def embedded_text(text):
    """Normalize Qt's decoded text; advanced ASS styling is not rendered."""
    text = re.sub(r'\{\\[^}]*\}', '', text)
    text = text.replace(r'\N', '\n').replace(r'\n', '\n').replace(r'\h', ' ')
    plain = PlainText()
    plain.feed(text)
    return ''.join(plain.parts).strip()
