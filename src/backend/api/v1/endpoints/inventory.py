from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, not_
from sqlalchemy.ext.asyncio import AsyncSession

from api.v1.Models.inventory import ContainerModel, NamesNode, PlasticModel, CassetteModel
from api.v1.dependencies.permissions import require_role
from database.db_cmd.plastic_supply import get_plastic_residue
from database.models import Container, Names, Cassette
from database.models.blank_cassettes import CassetteType
from database.models.cassette import CassetteState
from database.session_context import get_async_session

router = APIRouter(prefix="/inventory", tags=["inventory"], dependencies=[Depends(require_role("Кладовщик"))])


@router.get("/containers", response_model=list[ContainerModel])
async def get_available_containers(session: AsyncSession = Depends(get_async_session)):
    containers = (
        await session.scalars(
            select(Container)
            .order_by(Container.storage, Container.name, Container.number)
            .where(not_(Container.number.contains("-")))
            .where(Container.storage != "Отгружено")
            .where(Container.storage != "Н/Д")
            .where(~Container.storage.op("~")(r"^[A-Za-zА-Яа-я]\d+\.\d+\.\d+$"))
            .where(~Container.storage.op("~")(r"^[A-Za-zА-Яа-я]\d+\.\d+\-\d+$"))
        )
    ).all()
    return containers


@router.get("/containers/storages", response_model=list[str])
async def get_containers_storages(session: AsyncSession = Depends(get_async_session)):
    containers = (
        await session.scalars(
            select(Container.storage)
            .order_by(Container.storage)
            .where(not_(Container.number.contains("-")))
            .where(Container.storage != "Отгружено")
            .where(Container.storage != "Н/Д")
            .where(~Container.storage.op("~")(r"^[A-Za-zА-Яа-я]\d+\.\d+\.\d+$"))
            .where(~Container.storage.op("~")(r"^[A-Za-zА-Яа-я]\d+\.\d+\-\d+$"))
            .distinct()
        )
    ).all()
    return containers


@router.get("/containers/names", response_model=NamesNode)
async def get_names_tree(session: AsyncSession = Depends(get_async_session)):
    result = await session.execute(select(Names))
    all_names = result.scalars().all()

    children_map = {}
    names_map = {}

    for n in all_names:
        names_map[n.id] = n
        children_map.setdefault(n.parent_id, []).append(n)

    def build_node(n: Names, prefix: str = "") -> dict:
        node_name = f"{prefix}-{n.name}".strip()
        children = children_map.get(n.id, [])
        if not children:
            return {"text": node_name, "value": node_name, "children": None}
        return {"text": n.name, "value": n.name, "children": [build_node(child, n.name) for child in children]}

    root = names_map.get(1)
    if not root:
        raise HTTPException(status_code=404, detail="Root node with id=1 not found")

    return build_node(root)


@router.get("/plastic", response_model=list[PlasticModel])
async def get_plastic():
    data = await get_plastic_residue()
    return [PlasticModel(color=i[0], total_weight=i[1]) for i in data if i[1] > 0]


@router.get("/cassette", response_model=list[CassetteModel])
async def get_cassette(session: AsyncSession = Depends(get_async_session)):
    stmt = select(Cassette).filter(Cassette.state != CassetteState.SHIP).order_by(Cassette.id)
    data = (await session.execute(stmt)).scalars().all()
    return [CassetteModel.from_orm(i) for i in data]


@router.get("/cassette/states", response_model=list[str])
async def get_cassette_states():
    return CassetteState.to_list()


@router.get("/cassette/types", response_model=list[str])
async def get_cassette_types():
    return CassetteType.to_list()


@router.get("/cassette/storages", response_model=list[str])
async def get_cassette_storages(session: AsyncSession = Depends(get_async_session)):
    stmt = select(Cassette.storage).filter(Cassette.state != CassetteState.SHIP).order_by(Cassette.storage).distinct()
    data = (await session.execute(stmt)).scalars().all()
    return data


@router.get("/cassette/names", response_model=list[str])
async def get_cassette_names(session: AsyncSession = Depends(get_async_session)):
    stmt = select(Cassette.name).filter(Cassette.state != CassetteState.SHIP).order_by(Cassette.name).distinct()
    data = (await session.execute(stmt)).scalars().all()
    return data
