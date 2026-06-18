# demo1：前后端分离 + 数据库（Docker Compose）

包含 3 个服务：

- `frontend`：Nginx 静态页 + 反向代理 `/api/*` 到后端
- `backend`：FastAPI（提供 Todo API）
- `db`：PostgreSQL 16（持久化到数据卷 `pgdata`）

## 一键启动

在仓库根目录执行：

```bash
docker compose -f demo1/docker-compose.yml up --build
```

启动后访问：

- 前端页面：`http://localhost:31888`
- 后端健康检查：`http://localhost:31889/api/health`

## 常用命令

```bash
# 后台运行
docker compose -f demo1/docker-compose.yml up -d --build

# 看日志
docker compose -f demo1/docker-compose.yml logs -f --tail=200

# 停止并删除容器（保留数据卷）
docker compose -f demo1/docker-compose.yml down

# 连数据也一起删（会清空 Postgres 数据）
docker compose -f demo1/docker-compose.yml down -v
```

## 改 Compose 的常见点

- **改端口**：在 `ports:` 调整，例如把前端改成 `80:80`（本 demo 当前用 `31888/31889`）
- **改数据库密码**：`db.environment.POSTGRES_PASSWORD` 和 `backend.environment.DATABASE_URL` 要一起改
- **想本地开发后端**：可以先只起 `db`（`docker compose up db`），本机跑后端并把 `DATABASE_URL` 指向 `localhost:5432`

