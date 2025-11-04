## 项目结构

```
visual/
├── app.py                 # 主应用文件
├── config.py             # 配置文件
├── database.py           # 数据库操作层
├── start_server.py       # 启动脚本
├── models/               # 数据模型层
│   ├── __init__.py
│   └── city.py          # 城市相关数据模型
├── services/             # 业务逻辑层
│   ├── __init__.py
│   └── city_service.py  # 城市相关业务逻辑
├── routes/               # 路由层
│   ├── __init__.py
│   └── city_routes.py   # 城市相关路由
└── utils/                # 工具类
    ├── __init__.py
    ├── response.py       # 响应工具类
    └── validators.py     # 验证工具类
```

1. **添加新的数据模型**: 在 `models/` 目录下创建新的模型文件
2. **添加新的业务逻辑**: 在 `services/` 目录下创建新的服务文件
3. **添加新的API端点**: 在 `routes/` 目录下创建新的路由文件
4. **添加新的工具函数**: 在 `utils/` 目录下创建新的工具文件