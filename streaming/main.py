from flask import Flask, Response, stream_with_context, jsonify, send_file, request
from flask_cors import CORS
from pymongo import MongoClient
from gridfs import GridFS
from bson import ObjectId
import os

app = Flask(__name__)
CORS(app)

CACHE_DIR = os.path.join(os.getcwd(), "video_cache")
os.makedirs(CACHE_DIR, exist_ok=True)



# Conectar ao MongoDB
try:
    client = MongoClient('mongodb://admin:password123@mongodb:27017/')
    db = client.videos_db
    videos_collection = db.videos
    fs = GridFS(db)
    app.logger.info("Conectado ao MongoDB com sucesso")
except Exception as e:
    app.logger.error(f"Erro ao conectar ao MongoDB: {e}")

@app.route('/api/videos', methods=['GET'])
def listar_videos():
    
    docs = videos_collection.find()
    if videos_collection is None:
        return jsonify({'error': 'Banco de dados inacessível.'}), 500


    try:
        videos = []
        for doc in docs:
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

    # cache_path = os.path.join(CACHE_DIR, f"{video_id}.mp4")
    # if os.path.exists(cache_path):
    # resp = send_file(cache_path,
    #                     conditional=True,
    #                     mimetype='video/mp4')    # or grid_out.content_type
    # resp.headers['X-Cache-Status'] = 'HIT'
    # return resp

    # """Faz o streaming do arquivo do GridFS."""
    # try:
    #     video = videos_collection.find_one({'_id': ObjectId(video_id)})
    #     if not video:
    #         return jsonify({'error': 'Vídeo não encontrado'}), 404

    #     file_id = video.get('file_id')
    #     grid_out = fs.get(ObjectId(file_id))

    #     def generate():
    #         for chunk in grid_out:
    #             yield chunk
        
    #     return Response(
    #         stream_with_context(generate()),
    #         mimetype=grid_out.content_type,
    #         headers={
    #             # Se precisar de Range Requests, pode adicionar headers aqui
    #         }
    #     )
    # except Exception as e:
    #     app.logger.error(f"Erro ao enviar vídeo: {e}")
    #     return jsonify({'error': 'Erro interno ao enviar vídeo'}), 500

    cache_path = os.path.join(CACHE_DIR, f"{video_id}.mp4")

    # 1) Se já estiver em cache em disco, serve-o diretamente
    if os.path.isfile(cache_path):
        resp = send_file(
            cache_path,
            conditional=True,          # lida com If-Modified-Since/ETag
            mimetype='video/mp4',      # ou o grid_out.content_type original
            as_attachment=False
        )
        resp.headers['Cache-Control']    = 'public, max-age=3600'
        resp.headers['Accept-Ranges']    = 'bytes'
        resp.headers['X-Cache-Status']   = 'HIT'
        return resp

    # 2) Caso contrário, busca do GridFS, grava em disco e depois serve
    video = videos_collection.find_one({'_id': ObjectId(video_id)})
    if not video:
        return jsonify({'error': 'Vídeo não encontrado'}), 404

    grid_out = fs.get(ObjectId(video['file_id']))
    # grava o ficheiro completo no disco
    with open(cache_path, 'wb') as f:
        for chunk in grid_out:
            f.write(chunk)

    # serve-o com send_file (e headers de cache)
    resp = send_file(
        cache_path,
        conditional=True,
        mimetype=grid_out.content_type
    )
    resp.headers['Cache-Control']    = 'public, max-age=3600'
    resp.headers['Accept-Ranges']    = 'bytes'
    resp.headers['X-Cache-Status']   = 'MISS'
    return resp

if __name__ == "__main__":
    # Ajuste a porta para 7000 (conforme o Deployment)
    app.run(host="0.0.0.0", port=7000, debug=False)

