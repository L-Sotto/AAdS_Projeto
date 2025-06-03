from flask import Flask, request, jsonify
from flask_cors import CORS
from pymongo import MongoClient
from bson import ObjectId
import logging
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
@app.route('api/video', methods=['POST'])
def adicionar_video():
    try:
        data = request.get_json()
        if not data:
            return jsonify({'status': 'error', 'message':'Dados não fornecidos'}), 400
        
        campos_required = ['titulo', 'descricao', 'duracao', 'url']
        if not all(caampos in data for caampos in campos_required):
            return jsonify({'error': 'Faltam campos obrigatórios'}), 400
        col_videos = videos_collection.insert_one(data)
        return jsonify({'message': 'Video adicionado com sucesso', 'id': str(col_videos.inserted_id)}), 201
        
    except Exception as e:
        app.logger.error(f"Erro ao processar voto: {e}")
        return jsonify({'status': 'error', 'message': 'Erro interno do servidor'}), 500

#Lista dos vídeos.
@app.route('api/video', methods=['GET'])
def obter_videos():
    try:
        video = videos_collection.find_one({'id_': ObjectId(id)})
        if not video:
            return jsonify({'error': 'Video nao encontrado :('}),404
        return jsonify(str(video['_id']))
    except Exception as e:
        app.logger.error(f"Erro ao obter o video: {e}")
        return jsonify({'error': 'Erro interno do servidor'}), 500
    
#listavideos
def serializar_video(video):
    video['_id'] = str(video['_id'])
    return video

@app.route('/api/video', methods=['GET'])
def listar_videos():
    try:
        videos = list(videos_collection.find())
        return jsonify(str(v['_id']) for v in videos)
    except Exception as e:
        app.logger.error(f"Erro ao listar vídeos: {e}")
        return jsonify({'error': 'Erro interno do servidor'}), 500



#pesquisar video por ID.
@app.route('api/video/<id>', methods=['GET'])
def obter_video_id(id):
    try:
        video = videos_collection.find_one({'_id': ObjectId(id)})
        if not video:
            return jsonify({'error': 'Vídeo não encontrado'}), 404
        return jsonify(str(video['_id']))
    except Exception as e:
        app.logger.error(f"Erro ao obter vídeo: {e}")
        return jsonify({'error': 'Erro interno do servidor'}), 500

#Apagar video
@app.route('api/video/<id>', methods=['DELETE'])
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
@app.route('api/video/<id>', methods=['PUT'])
def editar_video(id):
    try:
        data = request.get_json()
        atualizar = {
            'titulo': data['titulo'],
            'descricao': data['descricao'],
            'duracao': data['duracao'],
            'url': data['url']
        }

        resul = videos_collection.update_one({'_id': ObjectId(id)}, {'$set': atualizar})
        if resul.matched_count == 0:
            return jsonify({'error': 'Video nao encontrado'}), 404
        return jsonify({'message': 'Video atualizado com sucesso'})
    except Exception as e:
        app.logger.error(f"Erro ao editar o video: {e}")
        return jsonify({'error': 'Erro interno no servidor'}), 500    


@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({'status': 'healthy'})

if __name__ == "__main__":
    
    app.run(host= "0.0.0.0", port = 6000, debug=False)