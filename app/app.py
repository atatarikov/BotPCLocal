from flask import Flask, request, jsonify, render_template
from flask_sqlalchemy import SQLAlchemy
from marshmallow import Schema, fields
import os
from sqlalchemy.orm import relationship, backref
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy.exc import NoResultFound

# Инициализация приложения и подключение к SQLite
app = Flask(__name__, template_folder='templates', static_folder='static')
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'data.db')
db = SQLAlchemy(app)

# Модели
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    telegram_login = db.Column(db.String(80), unique=True, nullable=False)

class Location(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    latitude = db.Column(db.Float, nullable=False)
    longitude = db.Column(db.Float, nullable=False)
    description = db.Column(db.String(120), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    user = db.relationship('User', backref=db.backref('locations', lazy=True))

class Group(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    group_link = db.Column(db.String(255), unique=True, nullable=False)
    title = db.Column(db.String(120), nullable=False)
    admin_user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    admin_user = db.relationship('User', backref=db.backref('admin_groups', lazy=True))
    # Каскадное удаление: при удалении группы удаляются все связанные записи UserGroup
    members = relationship("UserGroup", cascade="all, delete-orphan", backref="group_ref")


class UserGroup(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    group_id = db.Column(db.Integer, db.ForeignKey('group.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    group = db.relationship('Group', backref=db.backref('users_in_group', lazy=True))
    user = db.relationship('User', backref=db.backref('groups', lazy=True))

# Маршаллинг схем для сериализации/десериализации объектов
class UserSchema(Schema):
    class Meta:
        model = User
        load_instance = True
    id = fields.Int()
    telegram_login = fields.Str(required=True)

class LocationSchema(Schema):
    class Meta:
        model = Location
        load_instance = True
    id = fields.Int()
    latitude = fields.Float(required=True)
    longitude = fields.Float(required=True)
    name = fields.Str(required=True)
    description = fields.Str()
    user_id = fields.Int()

class GroupSchema(Schema):
    class Meta:
        model = Group
        load_instance = True
    id = fields.Int()
    group_link = fields.Str(required=True)
    title = fields.Str(required=True)
    admin_user_id = fields.Int()
    hash_sum = fields.Str()

class UserGroupSchema(Schema):
    class Meta:
        model = UserGroup
        load_instance = True
    id = fields.Int()
    group_id = fields.Int()
    user_id = fields.Int()

user_schema = UserSchema()
location_schema = LocationSchema()
group_schema = GroupSchema()
user_group_schema = UserGroupSchema()

# Основные маршруты API

@app.route('/api/user/add', methods=['POST'])
def add_user():
    """ Endpoint для добавления пользователя в базу данных. Принимает JSON с полем 'telegram_login'. """
    data = request.get_json()
    telegram_login = data.get('telegram_login')

    # Проверяем, существует ли уже такой пользователь
    existing_user = User.query.filter_by(telegram_login=telegram_login).first()
    if existing_user is None:
        # Если пользователя нет, добавляем его в базу данных
        new_user = User(telegram_login=telegram_login)
        try:
            db.session.add(new_user)
            db.session.commit()
            return jsonify({"message": "Пользователь успешно добавлен."}), 201
        except IntegrityError:
            # В случае конфликта уникальности (это редкий случай, если уже проверяли)
            db.session.rollback()
            return jsonify({"message": "Пользователь уже существует."}), 409
    else:
        # Если пользователь уже существует, возвращаем ошибку
        return jsonify({"message": "Пользователь уже существует."}), 409

# @app.route('/api/users/<string:telegram_login>/groups', methods=['GET'])
# def list_user_groups(telegram_login):
#     # Получаем пользователя по Telegram login
#     user = User.query.filter_by(telegram_login=telegram_login).first()
    
#     if not user:
#         return jsonify({'message': 'Пользователь не найден'}), 404
    
#     groups = user.groups
#     result = user_group_schema.dump(groups, many=True)
#     return jsonify(result), 200

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/groups/<string:hash_sum>/add-user', methods=['POST'])
def add_user_to_group(hash_sum):
    data = request.get_json()
    telegram_login = data.get('telegram_login')
    
    # Проверяем существование группы по её хэш-сумме
    group = Group.query.filter_by(hash_sum=hash_sum).first()
    if not group:
        return jsonify({'message': 'Группа не найдена'}), 404
    
    # Проверка существования пользователя
    user = User.query.filter_by(telegram_login=telegram_login).first()
    if not user:
        return jsonify({'message': 'Пользователь не найден'}), 404
    
    # Добавляем пользователя в группу
    new_user_group = UserGroup(group_id=group.id, user_id=user.id)
    db.session.add(new_user_group)
    db.session.commit()
    return jsonify({'message': f'Пользователь {telegram_login} успешно добавлен в группу {group.title}'}), 201


@app.route('/api/groups/<string:hash_sum>/remove-user', methods=['DELETE'])
def remove_user_from_group(hash_sum):
    data = request.get_json()
    telegram_login = data.get('telegram_login')
    
    # Поиск группы по хэшу
    group = Group.query.filter_by(hash_sum=hash_sum).first()
    if not group:
        return jsonify({'message': 'Группа не найдена'}), 404
    
    # Поиск пользователя
    user = User.query.filter_by(telegram_login=telegram_login).first()
    if not user:
        return jsonify({'message': 'Пользователь не найден'}), 404
    
    # Удаление связи между группой и пользователем
    user_group = UserGroup.query.filter_by(group_id=group.id, user_id=user.id).first()
    if not user_group:
        return jsonify({'message': 'Пользователь не состоит в группе'}), 404
    
    db.session.delete(user_group)
    db.session.commit()
    return jsonify({'message': f'Пользователь {telegram_login} удалён из группы {group.title}'}), 200


@app.route('/api/admin-groups/<string:telegram_login>', methods=['GET'])
def list_admin_groups(telegram_login):
    # Получаем пользователя по Telegram login
    user = User.query.filter_by(telegram_login=telegram_login).first()
    
    if not user:
        return jsonify({'message': 'Пользователь не найден'}), 404
    
    admin_groups = user.admin_groups
    result = group_schema.dump(admin_groups, many=True)
    return jsonify(result), 200


@app.route('/api/add-group', methods=['POST'])
def create_group():
    data = request.get_json()
    telegram_login = data.get('telegram_login')
    group_link = data.get('group_link')
    title = data.get('title')
    
    # Проверка наличия всех обязательных полей
    if not all([telegram_login, group_link, title]):
        return jsonify({'message': 'Отсутствуют обязательные поля'}), 400
    
    # Найти пользователя
    user = User.query.filter_by(telegram_login=telegram_login).first()
    if not user:
        return jsonify({'message': 'Пользователь не найден'}), 404
    
    # Создать новую группу
    new_group = Group(
        group_link=group_link,
        title=title,
        admin_user_id=user.id
    )
    db.session.add(new_group)
    db.session.commit()
    return jsonify({'message': f'Группа "{title}" создана успешно'}), 201


# Обработчик удаления группы
@app.route('/api/delete-group/<int:group_id>/<string:owner>', methods=['DELETE'])
def delete_group(group_id, owner):
    try:
        user = User.query.filter_by(telegram_login=owner).first()
        # Находим группу по ID и проверяем владельца
        group = Group.query.filter_by(id=group_id).one()
        
        # Удаляем группу из базы данных
        db.session.delete(group)
        db.session.commit()
        
        return jsonify({"message": "Группа успешно удалена"}), 200
    except NoResultFound:
        return jsonify({"message": "Группа не найдена или вы не имеете прав на её удаление"}), 404
    except Exception as e:
        return jsonify({"message": "Ошибка при удалении группы", "details": str(e)}), 500


@app.route('/api/users/<string:telegram_login>/locations', methods=['GET'])
def list_user_locations(telegram_login):
    # Получаем пользователя по Telegram login
    user = User.query.filter_by(telegram_login=telegram_login).first()
    
    if not user:
        return jsonify({'message': 'Пользователь не найден'}), 404
    
    locations = user.locations
    result = location_schema.dump(locations, many=True)
    return jsonify(result), 200


@app.route('/api/add-location', methods=['POST'])
def add_location():
    data = request.get_json()
    telegram_login = data.get('telegram_login')
    latitude = float(data.get('latitude'))
    longitude = float(data.get('longitude'))
    description = data.get('description')
    
    # Проверка наличия обязательных полей
    if not all([telegram_login, latitude, longitude, description]):
        return jsonify({'message': 'Отсутствуют обязательные поля'}), 400
    
    # Получить пользователя
    user = User.query.filter_by(telegram_login=telegram_login).first()
    if not user:
        return jsonify({'message': 'Пользователь не найден'}), 404
    
    # Создать новую локацию
    new_location = Location(latitude=latitude, longitude=longitude, description=description, user_id=user.id)
    db.session.add(new_location)
    db.session.commit()
    return jsonify({'message': f'Локация "{description}" добавлена успешно'}), 201

# Обработчик удаления локации
@app.route('/api/users/<string:username>/locations/<int:location_id>', methods=['DELETE'])
def delete_location(username, location_id):
    try:
        # Находим локацию по id и проверяем, принадлежит ли она данному пользователю
        location = Location.query.filter_by(id=location_id).one()
        
        # Удаляем локацию из базы данных
        db.session.delete(location)
        db.session.commit()
        
        return jsonify({"message": "Локация успешно удалена"}), 200
    except NoResultFound:
        return jsonify({"message": "Локация не найдена или не принадлежит вам"}), 404
    except Exception as e:
        return jsonify({"message": "Ошибка при удалении локации", "details": str(e)}), 500

@app.route('/api/check-invite-code/<string:invite_code>', methods=['GET'])
def check_invite_code(invite_code):
    group = Group.query.filter_by(group_link=invite_code).first()
    if group:
        return jsonify({
            "valid": True,
            "group_id": group.id,
            "group_title": group.title
        }), 200
    else:
        return jsonify({"valid": False}), 404
    
    
@app.route('/api/join-group/<string:invite_code>', methods=['POST'])
def join_group(invite_code):
    data = request.get_json()
    telegram_login = data.get('telegram_login')

    # Проверяем существование группы по пригласительному коду
    group = Group.query.filter_by(group_link=invite_code).first()
    if not group:
        return jsonify({'message': 'Группа не найдена'}), 404

    # Проверяем существование пользователя
    user = User.query.filter_by(telegram_login=telegram_login).first()
    if not user:
        return jsonify({'message': 'Пользователь не найден'}), 404

    # Проверяем, не состоит ли пользователь уже в группе
    existing_association = UserGroup.query.filter_by(group_id=group.id, user_id=user.id).first()
    if existing_association:
        return jsonify({'message': 'Вы уже состоите в этой группе'}), 409

    # Создаем новую ассоциацию пользователя с группой
    new_user_group = UserGroup(group_id=group.id, user_id=user.id)
    db.session.add(new_user_group)
    db.session.commit()
    return jsonify({'message': f'Пользователь {telegram_login} успешно добавлен в группу {group.title}'}), 201


@app.route('/api/users/<string:telegram_login>/groups', methods=['GET'])
def list_user_groups(telegram_login):
    # Получаем пользователя по Telegram login
    user = User.query.filter_by(telegram_login=telegram_login).first()
    if not user:
        return jsonify({'message': 'Пользователь не найден'}), 404
    
    # Получаем группы через отношение Many-to-Many (используя UserGroup)
    groups = db.session.query(Group)\
                      .join(UserGroup, Group.id == UserGroup.group_id)\
                      .filter(UserGroup.user_id == user.id)\
                      .all()
    
    # Преобразование результата в нужный формат
    result = group_schema.dump(groups, many=True)
    return jsonify(result), 200


@app.route('/api/leave-group/<int:group_id>', methods=['DELETE'])
def leave_group(group_id):
    data = request.get_json()
    telegram_login = data.get('telegram_login')
    
    # Проверяем существование пользователя
    user = User.query.filter_by(telegram_login=telegram_login).first()
    if not user:
        return jsonify({'message': 'Пользователь не найден'}), 404
    
    # Проверяем существование группы
    group = Group.query.filter_by(id=group_id).first()
    if not group:
        return jsonify({'message': 'Группа не найдена'}), 404
    
    # Убираем пользователя из группы
    user_group = UserGroup.query.filter_by(group_id=group.id, user_id=user.id).first()
    if not user_group:
        return jsonify({'message': 'Вы не состоите в этой группе'}), 404
    
    db.session.delete(user_group)
    db.session.commit()
    return jsonify({'message': f'Вы покинули группу {group.title}'}), 200


@app.route('/api/all-map-data', methods=['GET'])
def all_map_data():
    # Получаем все локации всех пользователей
    locations = Location.query.all()
    result = []
    for loc in locations:
        result.append({
            "latitude": loc.latitude,
            "longitude": loc.longitude,
            "description": loc.description,
            "telegram_login": loc.user.telegram_login
        })
    
    return jsonify({"locations": result}), 200

@app.before_first_request
def create_tables():
    db.create_all()

if __name__ == '__main__':
    # with app.app_context():
    #     db.create_all()  # Создает таблицы в базе данных перед запуском сервера
    app.run(debug=True)