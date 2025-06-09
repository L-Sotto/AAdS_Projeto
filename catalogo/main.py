from flask import Flask, request, jsonify
from flask_cors import CORS
from pymongo import MongoClient
import logging
from bson import ObjectId, errors as bson_errors
from gridfs import GridFS
import os
from datetime import datetime
# from moviepy.editor import VideoFileClip
from pymediainfo import MediaInfo
app = Flask(__name__)
CORS(app)

try:
    client = MongoClient('mongodb://admin:password123@mongodb:27017/')
    db = client.videos_db
    videos_collection = db.videos
    app.logger.info("Conectado à MongoDB com sucesso")
except Exception as e:
    app.logger.error(f"Erro ao conectar à MongoDB: {e}")


#Adicionar videos
@app.route('/api/video', methods=['POST'])
def adicionar_video():
    if videos_collection in None:
        return jsonify({'error': 'Banco de dados inacessível.'}), 500
    
    if 'videoFile' not in request.files:
        return jsonify({'error': 'Arquivo de vídeo não fornecido'}), 400
    arquivo = request.files['videofile']
    filename = arquivo.filename
    
    if filename == "":
        return jsonify({'error':'Nenhum arquivo selecionado'}), 400
    
    titulo = request.form.get('titulo','').strip()
    descricao = request.form.get('descricao','').strip()
    
    if not titulo or not descricao:
        return jsonify({'error': 'titulo e descricao sao obrigatorios'}),400
    
    temp_path= os.path.join('/tmp', filename)
    arquivo.save(temp_path)

    duracao_segundos=None

    try:
        mediainfo = MediaInfo.parse(temp_path)
        for track in mediainfo.tracks:
            if track.track_type == 'General' and track.duration:
                duracao_segundos = float(track.duration)/1000.0
                break
    except Exception as e:
        app.logger.error(f"Error ao extrair a duracao: {e}")

    with open(temp_path, 'rb') as f:
        fileId = fs.put(
            f,
            filename=filename,
            content_type = arquivo.content_type
        )
    
    try:
        os.remove(temp_path)
    except OSError:
        pass

    metadados = {
        'titulo': titulo,
        'descricao': descricao,
        'filename': filename,
        'content_type': arquivo.content_type,
        'duracao': duracao_segundos,
        'fileId': fileId,
        'uploadDate': datetime.utcnow()
    }
    result = videos_collection.insert_one(metadados)

    return jsonify({
        'id': str(result.inserted_id),
        'file_id': str(fileId),
        'duracao': duracao_segundos
    }), 201
    
'''
    try:
        titulo = request.form.get('titulo', "").strip()
        descricao = request.form.get('descricao', "").strip()
        
        if not titulo or not descricao:
            return jsonify({'status': 'error', 'message':'Dados nao fornecidos'}), 400
        arquivo = request.files['videofile']
        if arquivo == "":
            return jsonify({'error': 'Nenhum arquivo selecionado'}), 400
        
        fileId = fs.put(
            arquivo.stream,
            filename = arquivo.filename,
            content_type = arquivo.content_type
        )
        metadados = {
            'Titulo': titulo,
            'Descricao': descricao,
            'file_id': fileId,
            'filename': arquivo.filename,
            'content_type': arquivo.content_type
        }
        col_id = videos_collection.insert_one(metadados)

        return jsonify({
            'id': str(col_id.inserted_id),
            'file_id': str(fileId),
            # 'duracao': duracaoo,
            'message': 'Adicionado :)'
        }), 201
    except Exception as e:
        app.logger.error(f"Error ao criar o video: {e}")
        return jsonify({'error': 'Erro interno'}), 500
'''

#Lista dos videos.
# @app.route('/api/video', methods=['GET'])
# def obter_videos():
#     try:
#         video = videos_collection.find_one({'id_': ObjectId(id)})
#         if not video:
#             return jsonify({'error': 'Video nao encontrado :('}),404
#         return jsonify(str(video['_id']))
#     except Exception as e:
#         app.logger.error(f"Erro ao obter o video: {e}")
#         return jsonify({'error': 'Erro interno do servidor'}), 500

@app.route('/api/video', methods=['GET'])
def obter_videos():
   
    if videos_collection is None:
        return jsonify({'error': 'Banco de dados inacessível.'}), 500

    try:
        docs = videos_collection.find()
        videos = []
        for doc in docs:
            file_id = doc.get('file_id')
            duracao = None
            # Tenta obter duração a partir do tamanho do arquivo no GridFS
            try:
                grid_out = fs.get(ObjectId(file_id))
                duracao = grid_out.length
            except Exception:
                pass

            videos.append({
                'titulo': doc.get('titulo'),
                'descricao': doc.get('descricao'),
                'duracao': duracao
            })

        return jsonify(videos), 200

    except Exception as e:
        # Se der qualquer exceção aqui, ela aparecerá com stack trace no console
        app.logger.error(f"Erro ao obter vídeos: {e}")
        return jsonify({'error': 'Erro ao listar vídeos.'}), 500

    
#listavideos
# def serializar_video(video):
#     video['_id'] = str(video['_id'])
#     return video

# @app.route('/api/video', methods=['GET'])
# def listar_videos():
#     try:
#         videos = list(videos_collection.find())
#         return jsonify(str(v['_id']) for v in videos)
#     except Exception as e:
#         app.logger.error(f"Erro ao listar videos: {e}")
#         return jsonify({'error': 'Erro interno do servidor'}), 500



#pesquisar video por ID.
@app.route('/api/video/<id>', methods=['GET'])
def obter_video_id(id):
    try:
        video = videos_collection.find_one({'_id': ObjectId(id)})
        if not video:
            return jsonify({'error': 'Video nao encontrado'}), 404
        return jsonify(str(video['_id']))
    except Exception as e:
        app.logger.error(f"Erro ao obter video: {e}")
        return jsonify({'error': 'Erro interno do servidor'}), 500

#Apagar video
@app.route('/api/video/<id>', methods=['DELETE'])
def apagar_video(id):
    try:
        apagado = videos_collection.delete_one({'_id':ObjectId(id)})
        if apagado.deleted_count == 0:
            return jsonify({'error': 'video nao apagado'}), 404
        return jsonify({'message': 'video apagado com sucesso'})
    except Exception as e:
        app.logger.error(f"Erro ao apagar o video: {e}")
        return jsonify({'error':'Erro interno no servidor'}), 500


#editar video
@app.route('/api/video/<id>', methods=['PUT'])
def editar_video(id):
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'Dados não fornecidos'}), 400

        atualizado = {
            'titulo': data.get('titulo'),
            'descricao': data.get('descricao'),
            'duracao': data.get('duracao'),
            'url': data.get('url')
        }
        resultado = videos_collection.update_one(
            {'_id': ObjectId(id)},
            {'$set': atualizado}
        )
        if resultado.matched_count == 0:
            return jsonify({'error': 'Vídeo não encontrado'}), 404

        return jsonify({'message': 'Vídeo atualizado com sucesso'}), 200

    except Exception as e:
        app.logger.error(f"Erro ao editar vídeo: {e}")
        return jsonify({'error': 'Erro interno ao editar vídeo.'}), 500


@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({'status': 'healthy'})

if __name__ == "__main__":
    
    app.run(host= "0.0.0.0", port = 5000, debug= True)