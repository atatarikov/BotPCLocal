from flask import Flask, request, jsonify, render_template
from flask_sqlalchemy import SQLAlchemy
from marshmallow import Schema, fields
from flask_migrate import Migrate
import os
from sqlalchemy.exc import IntegrityError
from slugify import slugify
from datetime import datetime, timezone


# Инициализация приложения и подключение к SQLite
app = Flask(__name__, template_folder="templates", static_folder="static")
basedir = os.path.abspath(os.path.dirname(__file__))
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///" + os.path.join(basedir, "data.db")
# TODO
# load_dotenv()
# DATABASE_URI = os.getenv("DATABASE_URI")
# app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE_URI
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False  # Отключаем tracking
db = SQLAlchemy(app)
migrate = Migrate(app, db)


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    telegram_id = db.Column(db.BigInteger, unique=True, nullable=False, index=True)
    username = db.Column(db.String(255))
    first_name = db.Column(db.String(255))
    training_stage = db.Column(db.Integer, nullable=False, default=0)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )


class Location(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    latitude = db.Column(db.Float, nullable=False)
    longitude = db.Column(db.Float, nullable=False)
    description = db.Column(db.String(120), nullable=False)
    user_id = db.Column(
        db.Integer, db.ForeignKey("user.id"), nullable=False, index=True
    )
    user = db.relationship("User", backref=db.backref("locations", lazy=True))
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )


class Group(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    group_link = db.Column(db.String(255), unique=True, nullable=False)
    title = db.Column(db.String(120), nullable=False)
    admin_user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    admin_user = db.relationship("User", backref=db.backref("admin_groups", lazy=True))
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    members = db.relationship(
        "UserGroup",
        back_populates="group_ref",
        cascade="all, delete-orphan",
        overlaps="users_in_group",
    )


class UserGroup(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    group_id = db.Column(db.Integer, db.ForeignKey("group.id"), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )
    user = db.relationship("User", backref=db.backref("groups", lazy=True))
    group_ref = db.relationship(
        "Group", back_populates="members", overlaps="users_in_group"
    )


# Маршаллинг схем для сериализации/десериализации объектов
class UserSchema(Schema):
    id = fields.Int()
    telegram_id = fields.Int(required=True)
    username = fields.Str()
    first_name = fields.Str()
    training_stage = fields.Int()
    created_at = fields.DateTime()
    updated_at = fields.DateTime()


class LocationSchema(Schema):
    id = fields.Int()
    latitude = fields.Float(required=True)
    longitude = fields.Float(required=True)
    description = fields.Str(required=True)
    user_id = fields.Int()
    created_at = fields.DateTime()
    updated_at = fields.DateTime()


class GroupSchema(Schema):
    id = fields.Int()
    group_link = fields.Str(required=True)
    title = fields.Str(required=True)
    admin_user_id = fields.Int()
    created_at = fields.DateTime()
    updated_at = fields.DateTime()


class UserGroupSchema(Schema):
    id = fields.Int()
    group_id = fields.Int()
    user_id = fields.Int()
    created_at = fields.DateTime()
    updated_at = fields.DateTime()


user_schema = UserSchema()
location_schema = LocationSchema()
group_schema = GroupSchema()
user_group_schema = UserGroupSchema()


def generate_unique_group_code(title: str) -> str:
    base_slug = slugify(title)
    slug = base_slug
    counter = 1

    # Проверяем в базе, есть ли уже такая ссылка
    while Group.query.filter_by(group_link=slug).first() is not None:
        slug = f"{base_slug}-{counter}"
        counter += 1

    return slug


# Основные маршруты API


@app.route("/")
def index():
    return render_template("index.html")


# --------------------------
# ХЕЛПЕРЫ
# --------------------------
def error_response(message, status_code=400, details=None):
    response = {"status": "error", "message": message}
    if details:
        response["details"] = details
    return jsonify(response), status_code


def success_response(message, data=None, status_code=200):
    response = {"status": "success", "message": message}
    # if data:
    response["data"] = data
    return jsonify(response), status_code


# --------------------------
# USER ROUTES
# --------------------------
@app.route("/api/user/add", methods=["POST"])
def add_user():
    data = request.get_json()
    telegram_id = data.get("telegram_id")
    username = data.get("username")
    first_name = data.get("first_name")

    if not telegram_id:
        return error_response("Поле telegram_id обязательно.")

    user = User.query.filter_by(telegram_id=telegram_id).first()
    if user:
        return success_response(
            "Пользователь уже существует.", {"training_stage": user.training_stage}, 201
        )

    try:
        new_user = User(
            telegram_id=telegram_id, username=username, first_name=first_name
        )
        db.session.add(new_user)
        db.session.commit()
        return success_response(
            "Пользователь успешно добавлен.",
            {"training_stage": new_user.training_stage},
            200,
        )
    except IntegrityError as e:
        db.session.rollback()
        return error_response("Ошибка при создании пользователя.", 500, str(e))


@app.route("/api/user/update_training_stage", methods=["POST"])
def update_training_stage():
    data = request.get_json()
    telegram_id = data.get("telegram_id")
    new_stage = data.get("new_training_stage")

    if not telegram_id or new_stage is None:
        return error_response("Обязательные поля: telegram_id и new_training_stage")

    user = User.query.filter_by(telegram_id=telegram_id).first()
    if not user:
        return error_response("Пользователь не найден", 404)

    try:
        user.training_stage = new_stage
        db.session.commit()
        return success_response(
            "Стадия обучения обновлена", {"training_stage": user.training_stage}
        )
    except Exception as e:
        db.session.rollback()
        return error_response("Ошибка при обновлении стадии обучения", 500, str(e))


@app.route("/api/user/<int:telegram_id>/groups", methods=["GET"])
def get_user_groups(telegram_id):
    user = User.query.filter_by(telegram_id=telegram_id).first()
    if not user:
        return error_response("Пользователь не найден", 404)

    try:
        groups = (
            db.session.query(Group)
            .join(UserGroup, Group.id == UserGroup.group_id)
            .filter(UserGroup.user_id == user.id)
            .all()
        )
        return success_response(
            "Группы пользователя получены", group_schema.dump(groups, many=True)
        )
    except Exception as e:
        return error_response("Ошибка при получении групп пользователя", 500, str(e))


@app.route("/api/group/<string:group_link>/join", methods=["POST"])
def join_group(group_link):
    data = request.get_json()
    telegram_id = data.get("telegram_id")

    if not telegram_id:
        return error_response("Требуется telegram_id пользователя")

    group = Group.query.filter_by(group_link=group_link).first()
    if not group:
        return error_response(f"Группа {group_link} не найдена", 404)

    user = User.query.filter_by(telegram_id=telegram_id).first()
    if not user:
        return error_response("Пользователь не найден", 404)

    if UserGroup.query.filter_by(group_id=group.id, user_id=user.id).first():
        return success_response("Пользователь уже в группе", 201)

    try:
        new_user_group = UserGroup(group_id=group.id, user_id=user.id)
        db.session.add(new_user_group)
        db.session.commit()
        return success_response(f"Пользователь добавлен в группу {group.title}")
    except Exception as e:
        db.session.rollback()
        return error_response("Ошибка при добавлении в группу", 500, str(e))


@app.route("/api/group/<int:group_id>/leave", methods=["DELETE"])
def leave_group(group_id):
    data = request.get_json()
    telegram_id = data.get("telegram_id")

    if not telegram_id:
        return error_response("Требуется telegram_id пользователя")

    user = User.query.filter_by(telegram_id=telegram_id).first()
    if not user:
        return error_response("Пользователь не найден", 404)

    user_group = UserGroup.query.filter_by(group_id=group_id, user_id=user.id).first()
    if not user_group:
        return error_response("Пользователь не состоит в группе", 404)

    try:
        db.session.delete(user_group)
        db.session.commit()
        return success_response("Вы покинули группу")
    except Exception as e:
        db.session.rollback()
        return error_response("Ошибка при выходе из группы", 500, str(e))


@app.route("/api/user/<string:telegram_id>/admin-groups", methods=["GET"])
def get_admin_groups(telegram_id):
    """
    Получение списка групп, где пользователь является администратором
    """
    if not telegram_id:
        return error_response("Требуется telegram_id пользователя")

    user = User.query.filter_by(telegram_id=telegram_id).first()
    if not user:
        return error_response("Пользователь не найден", 404)

    try:
        admin_groups = user.admin_groups
        return success_response(
            "Группы администратора получены", group_schema.dump(admin_groups, many=True)
        )
    except Exception as e:
        return error_response("Ошибка при получении групп администратора", 500, str(e))


@app.route("/api/group/create", methods=["POST"])
def create_group():
    data = request.get_json()
    telegram_id = data.get("telegram_id")
    title = data.get("title")

    if not all([telegram_id, title]):
        return error_response("Отсутствуют обязательные поля: telegram_id и title")

    user = User.query.filter_by(telegram_id=telegram_id).first()
    if not user:
        return error_response("Пользователь не найден", 404)

    try:
        group_link = generate_unique_group_code(title)
        new_group = Group(group_link=group_link, title=title, admin_user_id=user.id)
        db.session.add(new_group)
        db.session.commit()
        return success_response(
            f'Группа "{title}" создана успешно', {"group_link": group_link}, 201
        )
    except Exception as e:
        db.session.rollback()
        return error_response("Ошибка при создании группы", 500, str(e))


@app.route("/api/group/<int:group_id>/delete", methods=["DELETE"])
def delete_group(group_id):
    data = request.get_json()
    telegram_id = data.get("telegram_id")

    if not telegram_id:
        return error_response("Требуется telegram_id администратора")

    user = User.query.filter_by(telegram_id=telegram_id).first()
    if not user:
        return error_response("Пользователь не найден", 404)

    group = Group.query.filter_by(id=group_id, admin_user_id=user.id).first()
    if not group:
        return error_response("Группа не найдена или у вас нет прав", 404)

    try:
        db.session.delete(group)
        db.session.commit()
        return success_response("Группа успешно удалена")
    except Exception as e:
        db.session.rollback()
        return error_response("Ошибка при удалении группы", 500, str(e))


@app.route("/api/location/add", methods=["POST"])
def add_location():
    data = request.get_json()
    telegram_id = data.get("telegram_id")
    latitude = data.get("latitude")
    longitude = data.get("longitude")
    description = data.get("description")

    if not all([telegram_id, latitude, longitude, description]):
        return error_response("Отсутствуют обязательные поля")

    try:
        latitude = float(latitude)
        longitude = float(longitude)
    except (TypeError, ValueError):
        return error_response("Неверный формат координат")

    user = User.query.filter_by(telegram_id=telegram_id).first()
    if not user:
        return error_response("Пользователь не найден", 404)

    try:
        new_location = Location(
            latitude=latitude,
            longitude=longitude,
            description=description,
            user_id=user.id,
        )
        db.session.add(new_location)
        db.session.commit()
        return success_response(
            "Локация добавлена", location_schema.dump(new_location), 201
        )
    except Exception as e:
        db.session.rollback()
        return error_response("Ошибка при добавлении локации", 500, str(e))


@app.route("/api/user/<int:telegram_id>/locations", methods=["GET"])
def get_user_locations(telegram_id):
    """
    Получение списка локаций пользователя
    """
    try:
        user = User.query.filter_by(telegram_id=telegram_id).first()

        if not user:
            return error_response("Пользователь не найден", 404)

        locations = user.locations
        return success_response(
            "Локации пользователя получены", location_schema.dump(locations, many=True)
        )

    except Exception as e:
        return error_response("Ошибка при получении локаций", 500, str(e))


@app.route("/api/location/<int:location_id>/delete", methods=["DELETE"])
def delete_location(location_id):
    data = request.get_json()
    telegram_id = data.get("telegram_id")

    if not telegram_id:
        return error_response("Требуется telegram_id пользователя")

    user = User.query.filter_by(telegram_id=telegram_id).first()
    if not user:
        return error_response("Пользователь не найден", 404)

    location = Location.query.filter_by(id=location_id, user_id=user.id).first()
    if not location:
        return success_response("Локация не найдена, уже удалена,  или не принадлежит вам", 203)

    try:
        db.session.delete(location)
        db.session.commit()
        return success_response("Локация успешно удалена")
    except Exception as e:
        db.session.rollback()
        return error_response("Ошибка при удалении локации", 500, str(e))


# --------------------------
# UTILITY ROUTES
# --------------------------


@app.route("/api/invite/<string:invite_code>/check", methods=["GET"])
def check_invite_code(invite_code):
    group = Group.query.filter_by(group_link=invite_code).first()
    if not group:
        return error_response("Код приглашения недействителен", 404)

    return success_response(
        "Код приглашения действителен",
        {"group_id": group.id, "group_title": group.title},
    )


@app.route("/api/all-map-data", methods=["GET"])
def all_map_data():
    locations = Location.query.all()
    result = []
    # TODO
    # т.к. логин (юзернейм может быть скрыт, то на карте нужно вывести хотябы имя, или так и написать "тебя не смогут написать...")
    # и проверку желательно на старте сделать, если у пользователя скрыт юзер нейм, то предупредить его, что написать ему не смогут,
    # предложить что-то еще

    for loc in locations:
        result.append(
            {
                "latitude": loc.latitude,
                "longitude": loc.longitude,
                "description": loc.description,
                "first_name": loc.user.first_name,
                "username": loc.user.username,
            }
        )

    return jsonify({"locations": result}), 200


@app.before_first_request
def create_tables():
    db.create_all()


if __name__ == "__main__":
    # with app.app_context():
    #     db.create_all()  # Создает таблицы в базе данных перед запуском сервера
    app.run(debug=True, use_reloader=False)
