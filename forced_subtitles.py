"""Read container subtitle flags in an isolated process, without decoding video."""
import av


def subtitle_flags(filename):
    with av.open(filename, timeout=5) as container:
        return [
            {
                'forced': bool(stream.disposition & av.stream.Disposition.forced),
                'codec': stream.codec_context.name,
            }
            for stream in container.streams.subtitles
        ]
