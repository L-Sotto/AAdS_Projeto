import psycopg2
from psycopg2.extras import RealDictCursor

from flask import Flask, request, jsonify
app = Flask(__name__)

DB_CONFIG = {
    "dbname": "users_bd",
    "user": "user",
    "password": "password",
    "host": "postgres_users",
    "port": 5432,
}

def iniciar_bd():
    create_table_query = """
    CREATE TABLE IF NOT EXISTS users ( 
        id SERIAL PRIMARY KEY,
        name VARCHAR(80) UNIQUE NOT NULL,
        password VARCHAR(120) NOT NULL,
    )
    """
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()
        cursor.execute(create_table_query)
        conn.commit()
        cursor.close()
        conn.close()
        print("Tabela 'users' inicializada com sucesso.")
    except Exception as e:
        print(f"Erro ao inicializar a tabela: {e}")


def obter_bd_connect():
    return psycopg2.connect(**DB_CONFIG)

#criar users
@app.route('/users', methods=['POST'])
def create_user():
    data = request.json
    if not data or not data.get('name') or not data.get('password'):
        return jsonify({"error": "Invalid input"}), 400
    
    try:
        conn = obter_bd_connect()
        cursor = conn.cursor()

        cursor.execute(
            "INSERT INTO users (name, password) VALUES (%s, %s) RETURNING id;",
            (data['name'], data['password'])
        )
        user_id = cursor.fetchone()[0]
        conn.commit()

        return jsonify({"id": user_id, "name": data['name'], "password": data['password']}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        conn.close()


#obter users


#logins
@app.route('/login', methods=['GET'])
def login_users():
    data= request.json
    if not data or not data.get('name') or not data.get('password'):
         return jsonify({"error": "User ou Password incorretos."}), 400
    try:
        connect = obter_bd_connect()
        cursor = connect.cursor(cursor_factory=RealDictCursor)

        cursor.execute("SELECT * FROM users WHERE name = %s;", (data['name'],))
        user = cursor.fetchone()

        if not user:
            return jsonify({"error": "User ou password invalidos."}), 404
        
        if user['password'] != data['password']:
            print(user['password'])
            print(data['password'])
            return jsonify({"error": "Invalid password"}), 401
        
        return jsonify({"message": "Login feito com sucesso!", "user": user}), 200
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        connect.close()



if __name__ == "__main__":
    iniciar_bd()
    app.run(host= "0.0.0.0", port = 6000)