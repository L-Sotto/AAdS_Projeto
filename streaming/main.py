# from flask import Flask, request, jsonify
# from flask_cors import CORS

# app = Flask(__name__)
# CORS(app)
from flask import Flask, Response, stream_with_context, jsonify
from flask_cors import CORS
from pymongo import MongoClient
from gridfs import GridFS
from bson import ObjectId

app = Flask(__name__)
CORS(app)

# Conectar ao MongoDB
try:
    client = MongoClient('mongodb://admin:password123@mongodb:27017/')
    db = client.videos_db
    fs = GridFS(db)
    videos_collection = db.videos
    app.logger.info("Conectado ao MongoDB com sucesso")
except Exception as e:
    app.logger.error(f"Erro ao conectar ao MongoDB: {e}")

@app.route('/api/videos', methods=['GET'])
def listar_videos():
    if videos_collection is None:
        return jsonify({'error': 'Banco de dados inacessível.'}), 500

    try:
        videos = []
        for doc in videos_collection.find():
            videos.append({
                'id': str(doc.get('_id')),
                'titulo': doc.get('titulo'),
                'descricao': doc.get('descricao'),
                'duracao': doc.get('duracao')
            })
        return jsonify(videos), 200
    except Exception as e:
        app.logger.error(f"Erro ao listar vídeos: {e}")
        return jsonify({'error': 'Erro interno ao listar vídeos'}), 500

@app.route('/api/videos/<video_id>', methods=['GET'])
def stream_video(video_id):
    """Faz o streaming do arquivo do GridFS."""
    try:
        video = videos_collection.find_one({'_id': ObjectId(video_id)})
        if not video:
            return jsonify({'error': 'Vídeo não encontrado'}), 404

        file_id = video.get('file_id')
        grid_out = fs.get(ObjectId(file_id))

        def generate():
            for chunk in grid_out:
                yield chunk

        return Response(
            stream_with_context(generate()),
            mimetype=grid_out.content_type,
            headers={
                # Se precisar de Range Requests, pode adicionar headers aqui
            }
        )
    except Exception as e:
        app.logger.error(f"Erro ao enviar vídeo: {e}")
        return jsonify({'error': 'Erro interno ao enviar vídeo'}), 500

if __name__ == "__main__":
    # Ajuste a porta para 7000 (conforme o Deployment)
    app.run(host="0.0.0.0", port=7000, debug=False)

