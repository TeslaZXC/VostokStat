from sqladmin import ModelView
from database import (
    Mission, PlayerStat, MissionSquadStat, GlobalSquad, AppConfig, AdminUser,
    engine
)
import bcrypt
from sqlalchemy import select
from sqladmin import BaseView, expose
from sqlalchemy import update

class MissionAdmin(ModelView, model=Mission):
    column_list = [
        Mission.id, 
        Mission.mission_name, 
        Mission.file_date, 
        Mission.map_name, 
        Mission.total_players,
        Mission.win_side
    ]
    column_searchable_list = [Mission.mission_name, Mission.file_name]
    column_sortable_list = [Mission.id, Mission.file_date, Mission.total_players]
    column_labels = {
        Mission.id: "ID",
        Mission.mission_name: "Название миссии",
        Mission.file_date: "Дата файла",
        Mission.map_name: "Карта",
        Mission.total_players: "Игроков",
        Mission.win_side: "Победитель"
    }
    icon = "fa-solid fa-flag"
    name = "Миссия"
    name_plural = "Миссии"

class PlayerStatAdmin(ModelView, model=PlayerStat):
    column_list = [
        PlayerStat.id,
        PlayerStat.name,
        PlayerStat.squad,
        PlayerStat.side,
        PlayerStat.frags,
        PlayerStat.death,
        PlayerStat.mission_id
    ]
    column_searchable_list = [PlayerStat.name, PlayerStat.squad]
    column_labels = {
        PlayerStat.id: "ID",
        PlayerStat.name: "Имя (Ник)",
        PlayerStat.squad: "Отряд",
        PlayerStat.side: "Сторона",
        PlayerStat.frags: "Фраги",
        PlayerStat.death: "Смерти",
        PlayerStat.mission_id: "ID Миссии"
    }
    # Removed column_filters to fix AttributeError with sqladmin 0.22.0
    icon = "fa-solid fa-person-rifle"
    name = "Статистика Игрока"
    name_plural = "Статистика Игроков"

from sqlalchemy import select

class MissionSquadStatAdmin(ModelView, model=MissionSquadStat):
    column_list = [
        MissionSquadStat.id,
        MissionSquadStat.squad_tag,
        MissionSquadStat.side,
        MissionSquadStat.frags,
        MissionSquadStat.death,
        MissionSquadStat.mission_id
    ]
    column_searchable_list = [MissionSquadStat.squad_tag]
    column_labels = {
        MissionSquadStat.id: "ID",
        MissionSquadStat.squad_tag: "Тег отряда",
        MissionSquadStat.side: "Сторона",
        MissionSquadStat.frags: "Фраги",
        MissionSquadStat.death: "Смерти",
        MissionSquadStat.mission_id: "ID Миссии"
    }
    # Removed column_filters to fix AttributeError with sqladmin 0.22.0
    icon = "fa-solid fa-users"
    name = "Статистика Отряда"
    name_plural = "Статистика Отрядов"

    def list_query(self, request):
        query = super().list_query(request)
        subq = select(GlobalSquad.name)
        return query.where(MissionSquadStat.squad_tag.in_(subq))

class GlobalSquadAdmin(ModelView, model=GlobalSquad):
    column_list = [GlobalSquad.id, GlobalSquad.name, GlobalSquad.tags]
    column_searchable_list = [GlobalSquad.name]
    column_labels = {
        GlobalSquad.id: "ID",
        GlobalSquad.name: "Название",
        GlobalSquad.tags: "Теги (Алиасы)"
    }
    icon = "fa-solid fa-layer-group"
    name = "Отряд (Global)"
    name_plural = "Отряды (Global)"

from sqladmin import BaseView, expose
from sqlalchemy import update
from database import engine, AppConfig

class AppConfigAdmin(ModelView, model=AppConfig):
    column_list = [AppConfig.key, AppConfig.value]
    form_columns = [AppConfig.key, AppConfig.value]
    column_labels = {
        AppConfig.key: "Ключ",
        AppConfig.value: "Значение"
    }
    icon = "fa-solid fa-gears"
    name = "Настройки"
    name_plural = "Настройки"

class AdminUserAdmin(ModelView, model=AdminUser):
    column_list = [AdminUser.username]
    form_columns = [AdminUser.username, AdminUser.password_hash]
    column_labels = {
        AdminUser.username: "Имя пользователя",
        AdminUser.password_hash: "Пароль"
    }
    icon = "fa-solid fa-user-shield"
    name = "Администратор"
    name_plural = "Администраторы"

    async def on_model_change(self, data, model, is_created, request):
        password = data.get("password_hash")
        if password and not password.startswith("$2b$"): # If not already hashed (simple check)
            # Hash the password
            hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
            data["password_hash"] = hashed.decode('utf-8')

    def is_accessible(self, request):
        # Only "admin" can manage other admins
        return request.session.get("token") == "admin"

    def is_visible(self, request):
        # Hide from menu if not "admin"
        return request.session.get("token") == "admin"

class MergePlayersView(BaseView):
    name = "Объединить Игроков"
    icon = "fa-solid fa-screwdriver-wrench"

    @expose("/merge", methods=["GET", "POST"])
    async def merge_players(self, request):
        success = None
        error = None
        
        if request.method == "POST":
            form = await request.form()
            source = form.get("source_name", "").strip()
            target = form.get("target_name", "").strip()
            
            if not source or not target:
                error = "Поля 'Исходное имя' и 'Целевое имя' обязательны."
            elif source == target:
                error = "Исходное и Целевое имена должны отличаться."
            else:
                # Perform Update
                async with engine.begin() as conn:
                    # Check if source exists (optional, simply update is fine)
                    stmt = (
                        update(PlayerStat)
                        .where(PlayerStat.name == source)
                        .values(name=target)
                    )
                    result = await conn.execute(stmt)
                    rows_affected = result.rowcount
                    
                    if rows_affected > 0:
                        success = f"Успешно объединено {rows_affected} записей с '{source}' на '{target}'."
                    else:
                        error = f"Записи для игрока '{source}' не найдены."
        
        return await self.templates.TemplateResponse(
            request,
            "merge_players.html", 
            context={"request": request, "success": success, "error": error}
        )
