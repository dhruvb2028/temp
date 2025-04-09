from flask import Flask, request, jsonify
from youtube_transcript_api import YouTubeTranscriptApi, TranscriptsDisabled, NoTranscriptFound
from urllib.parse import urlparse, parse_qs
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

def extract_video_id(youtube_url):
    parsed = urlparse(youtube_url)
    if parsed.hostname in ['www.youtube.com', 'youtube.com']:
        return parse_qs(parsed.query).get('v', [None])[0]
    elif parsed.hostname == 'youtu.be':
        return parsed.path[1:]
    return None

@app.route('/get_transcript_api', methods=['POST'])
def get_transcript_api():
    # Option 1: Use force=True to get JSON even when Content-Type is not application/json.
    data = request.get_json(force=True)
    if not data or 'url' not in data:
        return jsonify({'error': 'Missing URL in request body'}), 400

    video_url = data['url']
    video_id = extract_video_id(video_url)

    if not video_id:
        return jsonify({'error': 'Invalid YouTube URL'}), 400

    try:
        transcript_list = YouTubeTranscriptApi.get_transcript(video_id)
        transcript = ''
        for i, entry in enumerate(transcript_list):
            text = entry['text'].replace('\n', ' ')
            transcript += text
            if i + 1 < len(transcript_list):
                gap = transcript_list[i + 1]['start'] - (entry['start'] + entry['duration'])
                if gap > 1.5:
                    transcript += ' ....  '
                else:
                    transcript += ' '
        return jsonify({'transcript': transcript})
    except (TranscriptsDisabled, NoTranscriptFound):
        return jsonify({'error': 'Transcript not available for this video'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
