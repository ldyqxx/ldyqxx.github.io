# QuantLab 量化预测平台

这是一个可部署到 GitHub Pages 的量化研究前端，以及一个可部署到 Render 的 FastAPI 后端。当前 API 使用**确定性的演示数据**，用于验证产品流程；上线前必须替换为合规行情数据和经过回测的模型。

## 本地运行

后端：

```bash
cd api
pip install -r requirements.txt
uvicorn main:app --reload
```

然后打开 `http://localhost:8000/docs` 查看 API 文档。前端直接打开 `index.html` 时，如果 API 不可访问，会自动显示离线演示模式。

## 部署

1. 将仓库推送到 GitHub，并在 Pages 设置中选择 `main` 分支根目录，部署静态前端。
2. 在 Render 连接仓库。根目录配置已写入 `render.yaml`，会在 `api` 目录安装依赖并启动 FastAPI。
3. 将前端的 `API_URL` 指向 Render 服务 URL，并重新发布 GitHub Pages。
4. 生产环境把 `api/main.py` 的 `allow_origins=["*"]` 改为仅允许你的 Pages 域名。

## 下一步替换点

- `make_forecast()`：接入行情数据、特征工程、模型推理和模型版本管理。
- 增加数据缓存、请求限流、认证、日志和监控。
- 使用时间序列交叉验证、交易成本、滑点和最大回撤进行回测。
- 发布前补充金融监管、隐私和风险披露要求。

预测结果不构成投资、税务或法律建议，也不代表未来收益。
