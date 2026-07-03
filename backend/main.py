import os
from contextlib import asynccontextmanager
from typing import List, Optional

import aiosqlite
import httpx
from fastapi import FastAPI, HTTPException, Path
from fastapi.responses import RedirectResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles

from database import DB_PATH, init_db
from models import (
    EndpointCreate,
    EndpointUpdate,
    EndpointResponse,
    SettingResponse,
    SettingUpdate,
)

# ── Lifespan ──────────────────────────────────────────────────────────────


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield


app = FastAPI(title="问学飞书 SSO 桥接器", lifespan=lifespan)

# ── Settings Helpers ──────────────────────────────────────────────────────


async def get_setting(key: str, default: str = "") -> str:
    """Read a setting value from the database."""
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            "SELECT value FROM settings WHERE key = ?", (key,)
        )
        row = await cursor.fetchone()
        return row[0] if row else default


# ── Helpers ───────────────────────────────────────────────────────────────


async def fetch_row(db: aiosqlite.Connection, endpoint_id: int):
    """Fetch a single endpoint row by id or raise 404."""
    cursor = await db.execute(
        "SELECT id, route_name, instance_id, app_id, description, "
        "       created_at, updated_at FROM endpoints WHERE id = ?",
        (endpoint_id,),
    )
    row = await cursor.fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail="端点配置不存在")
    return dict(row)


def row_to_response(row: dict) -> EndpointResponse:
    return EndpointResponse(**row)


# ── API: CRUD Endpoints ───────────────────────────────────────────────────


@app.get("/api/endpoints", response_model=List[EndpointResponse])
async def list_endpoints():
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            "SELECT id, route_name, instance_id, app_id, description, "
            "       created_at, updated_at FROM endpoints ORDER BY id"
        )
        rows = await cursor.fetchall()
        return [row_to_response(dict(r)) for r in rows]


@app.post("/api/endpoints", response_model=EndpointResponse, status_code=201)
async def create_endpoint(body: EndpointCreate):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        # Check uniqueness
        cursor = await db.execute(
            "SELECT id FROM endpoints WHERE route_name = ?", (body.route_name,)
        )
        if await cursor.fetchone():
            raise HTTPException(
                status_code=409,
                detail=f"路由名 '{body.route_name}' 已存在",
            )
        cursor = await db.execute(
            "INSERT INTO endpoints (route_name, instance_id, app_id, description) "
            "VALUES (?, ?, ?, ?)",
            (body.route_name, body.instance_id, body.app_id, body.description or ""),
        )
        await db.commit()
        row = await fetch_row(db, cursor.lastrowid)
        return row_to_response(dict(row))


@app.put("/api/endpoints/{endpoint_id}", response_model=EndpointResponse)
async def update_endpoint(endpoint_id: int, body: EndpointUpdate):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row

        # Check exists
        await fetch_row(db, endpoint_id)

        # Check route_name uniqueness if changing
        if body.route_name is not None:
            cursor = await db.execute(
                "SELECT id FROM endpoints WHERE route_name = ? AND id != ?",
                (body.route_name, endpoint_id),
            )
            if await cursor.fetchone():
                raise HTTPException(
                    status_code=409,
                    detail=f"路由名 '{body.route_name}' 已存在",
                )

        updates = []
        params = []
        for field in ("route_name", "instance_id", "app_id", "description"):
            value = getattr(body, field, None)
            if value is not None:
                updates.append(f"{field} = ?")
                params.append(value)

        if updates:
            updates.append("updated_at = datetime('now')")
            params.append(endpoint_id)
            await db.execute(
                f"UPDATE endpoints SET {', '.join(updates)} WHERE id = ?",
                params,
            )
            await db.commit()

        row = await fetch_row(db, endpoint_id)
        return row_to_response(dict(row))


@app.delete("/api/endpoints/{endpoint_id}", status_code=204)
async def delete_endpoint(endpoint_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        await fetch_row(db, endpoint_id)
        await db.execute("DELETE FROM endpoints WHERE id = ?", (endpoint_id,))
        await db.commit()
        return None


# ── API: Settings ─────────────────────────────────────────────────────────


@app.get("/api/settings", response_model=List[SettingResponse])
async def list_settings():
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            "SELECT key, value, description FROM settings ORDER BY key"
        )
        rows = await cursor.fetchall()
        return [SettingResponse(**dict(r)) for r in rows]


@app.put("/api/settings/{key}", response_model=SettingResponse)
async def update_setting(key: str, body: SettingUpdate):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            "SELECT key, value, description FROM settings WHERE key = ?", (key,)
        )
        if not await cursor.fetchone():
            raise HTTPException(status_code=404, detail="设置不存在")
        await db.execute(
            "UPDATE settings SET value = ? WHERE key = ?",
            (body.value, key),
        )
        await db.commit()
        cursor = await db.execute(
            "SELECT key, value, description FROM settings WHERE key = ?", (key,)
        )
        row = await cursor.fetchone()
        return SettingResponse(**dict(row))


# ── SSO Redirect ──────────────────────────────────────────────────────────


@app.get("/{route_name}")
async def sso_redirect(route_name: str = Path(...)):
    # 1. Look up route in database
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            "SELECT route_name, instance_id, app_id FROM endpoints WHERE route_name = ?",
            (route_name,),
        )
        row = await cursor.fetchone()

    if row is None:
        return HTMLResponse(
            content=f"<h1>404 - Not Found</h1><p>未找到配置：{route_name}</p>",
            status_code=404,
        )

    app_id = row["app_id"]
    wenxue_base = await get_setting("wenxue_base_url", "https://wenxue.example.com")
    url = f"{wenxue_base}/api/apps/sso/login/path?app_id={app_id}"

    # 2. Proxy request to Wenxue
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(url)
            resp.raise_for_status()
            data = resp.json()
    except httpx.TimeoutException:
        return HTMLResponse(
            content="<h1>502 - Bad Gateway</h1><p>请求问学平台超时</p>",
            status_code=502,
        )
    except httpx.HTTPStatusError as e:
        return HTMLResponse(
            content=f"<h1>502 - Bad Gateway</h1><p>问学平台返回错误: {e.response.status_code}</p>",
            status_code=502,
        )
    except Exception as e:
        return HTMLResponse(
            content=f"<h1>502 - Bad Gateway</h1><p>请求问学平台失败: {str(e)}</p>",
            status_code=502,
        )

    # 3. Validate response structure
    if not isinstance(data, dict) or data.get("code") != 200:
        msg = data.get("message", str(data)) if isinstance(data, dict) else str(data)
        return HTMLResponse(
            content=f"<h1>502 - Bad Gateway</h1><p>问学平台返回错误: {msg}</p>",
            status_code=502,
        )

    items = data.get("data", [])
    if not items or not isinstance(items, list):
        return HTMLResponse(
            content="<h1>502 - Bad Gateway</h1><p>问学平台返回数据为空</p>",
            status_code=502,
        )

    # 4. Find Feishu SSO redirect URL
    redirect_url = None
    for item in items:
        if isinstance(item, dict) and item.get("type") == "FEISHU":
            redirect_url = item.get("completeRedirectUrl")
            break

    if not redirect_url:
        return HTMLResponse(
            content="<h1>502 - Bad Gateway</h1><p>未找到飞书 SSO 配置</p>",
            status_code=502,
        )

    # 5. Redirect
    return RedirectResponse(url=redirect_url, status_code=302)


# ── Static File Serving (production) ──────────────────────────────────────

STATIC_DIR = os.path.join(os.path.dirname(__file__), "..", "frontend", "dist")
if os.path.isdir(STATIC_DIR):
    app.mount(
        "/",
        StaticFiles(directory=STATIC_DIR, html=True),
        name="static",
    )

# ── Main ──────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
