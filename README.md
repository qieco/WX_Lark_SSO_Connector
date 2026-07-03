# WX Lark SSO Connector — 问学飞书 SSO 自动跳转桥接器

通过管理页面配置"路由名 → 问学 agent"的映射，终端用户访问 `域名/路由名`（如 `/helpdesk`）时自动 302 重定向到飞书 SSO 登录页。

## 架构

```
用户浏览器 → GET /{route_name}
                │
                ├─ DB 查询 route_name 对应的 app_id
                │
                └─ GET https://wenxue.example.com/api/apps/sso/login/path?app_id={app_id}
                     │
                     └─ 解析 JSON → 提取 FEISHU 类型的 completeRedirectUrl
                          │
                          └─ 302 → 飞书 SSO 登录页
```

后端（Python FastAPI）：
- 配置 CRUD（SQLite 持久化）
- 代理请求问学平台 SSO API
- 302 重定向到飞书账号授权页

前端（React + Vite）：
- 端点配置管理表格
- 系统设置面板（问学平台地址可配置）

## 快速开始

### 依赖

- Python ≥ 3.12
- Node.js ≥ 18

### 安装与启动

```bash
# 后端
cd backend
pip install -r requirements.txt
uvicorn main:app --reload --port 8000

# 前端（另一个终端）
cd frontend
npm install
npm run dev
```

一键开发启动：

```bash
python run.py
```

访问 `http://localhost:5173` 进入管理页面。

### 生产部署

```bash
cd frontend && npm run build
cd ../backend && uvicorn main:app --host 0.0.0.0 --port 8000
```

前端构建产物由 FastAPI 自动托管（`StaticFiles` mount），单进程即可运行。生产环境建议前置 nginx/Caddy 做 HTTPS 反代。

## 使用

1. 打开管理页面，点击 ⚙️ 设置问学平台基础地址（默认 `https://wenxue.example.com`）
2. 点击"+ 新增端点"，填写路由名、Instance ID、App ID
3. 访问 `http://localhost:5173/{路由名}`（开发）或 `https://你的域名/{路由名}`（生产）
4. 浏览器自动 302 跳转到飞书 SSO 登录页

## API

| 方法 | 路径 | 说明 |
|---|---|---|
| GET | `/api/endpoints` | 列出所有端点 |
| POST | `/api/endpoints` | 新增端点 |
| PUT | `/api/endpoints/{id}` | 更新端点 |
| DELETE | `/api/endpoints/{id}` | 删除端点 |
| GET | `/api/settings` | 列出系统设置 |
| PUT | `/api/settings/{key}` | 更新系统设置 |
| GET | `/{route_name}` | SSO 重定向 |

## License

MIT
