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
    fs=GridFS(db)
    app.logger.info("Conectado à MongoDB com sucesso")
except Exception as e:
    app.logger.error(f"Erro ao conectar à MongoDB: {e}")


#Adicionar videos
@app.route('/api/videos', methods=['POST'])
def adicionar_video():
    if videos_collection is None:
        return jsonify({'error': 'Banco de dados inacessível.'}), 500
    
    if 'videofile' not in request.files:
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
                minutos = int(duracao_segundos // 60)
                segundos = int(duracao_segundos % 60)
                duracaommss = f"{minutos}:{segundos:02d}"
                break
    except Exception as e:
        app.logger.error(f"Error ao extrair a duracao: {e}")

    with open(temp_path, 'rb') as f:
        file_id = fs.put(
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
        'duracao': duracaommss,
        'file_id': file_id,
        'uploadDate': datetime.utcnow()
    }
    result = videos_collection.insert_one(metadados)

    return jsonify({
        'id': str(result.inserted_id),
        'file_id': str(file_id),
        'duracao': duracaommss
    }), 201
    

@app.route('/api/videos', methods=['GET'])
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
                # grid_out = fs.get(ObjectId(file_id))
                duracao = doc.get('duracao')
            except Exception:
                pass

            videos.append({
                'id': str(doc.get('_id')),
                'titulo': doc.get('titulo'),
                'descricao': doc.get('descricao'),
                'duracao': duracao
            })

        return jsonify(videos), 200

    except Exception as e:
        # Se der qualquer exceção aqui, ela aparecerá com stack trace no console
        app.logger.error(f"Erro ao obter vídeos: {e}")
        return jsonify({'error': 'Erro ao listar vídeos.'}), 500

    


#pesquisar video por ID.
@app.route('/api/videos/<id>', methods=['GET'])
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
@app.route('/api/videos/<id>', methods=['DELETE'])
def apagar_video(id):
    try:
        apagado = videos_collection.delete_one({'_id':ObjectId(id)})
        if apagado.deleted_count == 0:
            return jsonify({'error': 'video nao apagado'}), 404
        file_id = apagado.get('file_id')
        if file_id:
            try:
                fs.delete(ObjectId(file_id))

            except Exception as e:
                app.logger.warning(f"Erro ao apagar video no GridFS: {e}")
        return jsonify({'message': 'video apagado com sucesso'})
    except Exception as e:
        app.logger.error(f"Erro ao apagar o video: {e}")
        return jsonify({'error':'Erro interno no servidor'}), 500


#editar video
@app.route('/api/videos/<id>', methods=['PUT'])
def editar_video(id):
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'Dados não fornecidos'}), 400

        atualizado = {
            'titulo': data.get('titulo'),
            'descricao': data.get('descricao'),
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
    
    app.run(host= "0.0.0.0", port = 5000, debug=False)