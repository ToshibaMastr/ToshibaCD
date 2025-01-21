from collections import defaultdict
from typing import Dict

import socketio
import uvicorn
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from sqlalchemy.sql import asc, desc, select

from .db import Endpoint, Server, ServerStatus, User, async_session, init_db
from .hasher import generate_hash

scheduler = AsyncIOScheduler()


async def init():
    scheduler.start()
    await init_db()


sio = socketio.AsyncServer(
    async_mode="asgi",
    cors_allowed_origins="*",
)
app = socketio.ASGIApp(sio, on_startup=init)

if not sio:
    exit()

users = {}
reqcache = {}


@sio.event
async def connect(sid, environ):
    users[sid] = set({})


@sio.event
async def disconnect(sid):
    del users[sid]


MODEL_MAPPING = {
    "server": Server,
    "server_status": ServerStatus,
    "endpoint": Endpoint,
    "user": User,
}

MODEL_MAPPING_R = {
    Server: "server",
    ServerStatus: "server_status",
    Endpoint: "endpoint",
    User: "user",
}

DIRECTION_MAPPING = {"asc": asc, "desc": desc}


async def build_query(request):
    params = request.get("filter", {})
    ob = MODEL_MAPPING[request["type"]]

    query = select(ob)

    for name, val in params.items():
        field = getattr(ob, name)
        if isinstance(val, list):
            query = query.filter(field.in_(set(val)))
        else:
            query = query.filter(field == val)

    if sort := request.get("sort"):
        direction_name = sort.get("direction", "desc")
        field = sort.get("field")
        direction = DIRECTION_MAPPING[direction_name]
        query = query.order_by(direction(getattr(ob, field)))

    if pagination := request.get("pagination"):
        offset = pagination.get("offset", 0)
        limit = pagination.get("limit", 20)
        query = query.offset(offset).limit(limit)
    else:
        query = query.limit(20)

    return query


async def get_objects(request: Dict):
    async with async_session() as session:
        query = await build_query(request)
        result = await session.execute(query)
        entitys = result.scalars().all()

    return entitys


async def localize_results(results, localization: str):
    for result in results:
        if "info" in result:
            info_data = result["info"]
            common_info = info_data.get("common", {})
            localized_info = info_data.get(localization, {})
            common_info.update(localized_info)
            result["info"] = common_info
    return results


async def resolve_dependencies(objects, dependencies):
    dep_results = defaultdict(list)

    async def process_dependency(obj, dependency_name):
        if attr := getattr(obj.awaitable_attrs, dependency_name, None):
            resolved = await attr
            model_type = MODEL_MAPPING_R[type(resolved)]
            dep_results[model_type].append(resolved.to_dict())

    for dependency in dependencies:
        for obj in objects:
            await process_dependency(obj, dependency)

    return dep_results


@sio.event
async def get(sid, req: Dict):
    result_raw = await get_objects(req)
    results = [obj.to_dict() for obj in result_raw]

    if localization := req.get("loc"):
        results = await localize_results(results, localization)

    reqid = generate_hash(req)
    ret = {"id": reqid, "data": results}

    await sio.emit(f"update:{req['type']}", ret, to=sid)

    if dependencies := req.get("resolve"):
        dep_results = await resolve_dependencies(result_raw, dependencies)
        for dependency_type, dep_data in dep_results.items():
            dep_ret = {"id": f"{reqid}_dep_{dependency_type}", "data": dep_data}
            await sio.emit(f"update:{dependency_type}", dep_ret, to=sid)


async def sync_users():
    # TODO
    pass


scheduler.add_job(sync_users, "interval", seconds=0.5)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=5000)
